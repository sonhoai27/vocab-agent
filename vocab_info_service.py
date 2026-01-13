"""
Service function để lấy thông tin từ vựng từ LLM với caching
"""
import json
import os
import re
from typing import Dict, Any
from openai import AzureOpenAI
from vocab_info_prompt import get_vocab_info_prompt
from vocab_cache import get_cached_vocab_info, save_vocab_info_to_cache
from models.vocab_info import VocabInfoResponse


# Tạo Azure OpenAI client instance
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)


def _extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON từ LLM response (có thể có markdown code block hoặc text khác)
    
    Args:
        response: Raw response từ LLM
        
    Returns:
        Parsed JSON dict
    """
    # Loại bỏ markdown code blocks nếu có
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    
    # Tìm JSON object trong response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    
    # Nếu không tìm thấy, thử parse toàn bộ response
    return json.loads(response.strip())


async def get_vocab_info(vocab: str, language: str) -> Dict[str, Any]:
    """
    Lấy thông tin từ vựng từ cache hoặc LLM
    
    Args:
        vocab: Từ vựng cần tra cứu
        language: Ngôn ngữ trả về
        
    Returns:
        Dict chứa thông tin từ vựng (examples, synonyms, origin)
        
    Raises:
        ValueError: Nếu không thể parse response từ LLM
        Exception: Nếu có lỗi khi gọi LLM
    """
    # Kiểm tra cache trước
    cached_data = get_cached_vocab_info(vocab, language)

    if cached_data:
        return cached_data
    
    # Nếu không có cache, gọi LLM
    prompt = get_vocab_info_prompt(vocab, language)
    
    try:
        # Gọi LLM - sử dụng Azure OpenAI client
        model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful language expert."},
                {"role": "user", "content": prompt}
            ]
        )
        # Lấy nội dung từ response
        response_text = resp.choices[0].message.content
        if not response_text:
            raise ValueError("LLM response không có nội dung")
        
        # Parse JSON từ response
        parsed_data = _extract_json_from_response(response_text)
        
        # Validate với Pydantic model
        validated_data = VocabInfoResponse(**parsed_data)
        
        # Convert về dict để lưu cache
        result_dict = validated_data.model_dump()
        
        # Lưu vào cache
        save_vocab_info_to_cache(vocab, language, result_dict)
        
        return result_dict
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Không thể parse JSON từ LLM response: {e}")
    except Exception as e:
        raise Exception(f"Lỗi khi gọi LLM: {e}")
