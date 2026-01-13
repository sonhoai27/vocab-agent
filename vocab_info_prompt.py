"""
Prompt template cho LLM để lấy thông tin từ vựng
"""

VOCAB_INFO_PROMPT_TEMPLATE = """
Bạn là một chuyên gia ngôn ngữ học. Nhiệm vụ của bạn là phân tích từ vựng tiếng Anh "{vocab}" và trả về thông tin chi tiết bằng ngôn ngữ {language}.

YÊU CẦU QUAN TRỌNG:
- TẤT CẢ nội dung trả về (examples, synonyms, origin) PHẢI được viết bằng {language}
- Chỉ có câu ví dụ (sentence) được viết bằng tiếng Anh
- Bản dịch (translation) và tất cả giải thích khác PHẢI bằng {language}

Hãy trả về một JSON object với format chính xác sau (KHÔNG có markdown, KHÔNG có code block, chỉ JSON thuần):

{{
  "vocab": "{vocab}",
  "language": "{language}",
  "examples": [
    {{
      "level": "easy",
      "sentence": "Câu ví dụ dễ bằng tiếng Anh",
      "translation": "Giải thích hoặc dịch bằng {language}"
    }},
    {{
      "level": "medium",
      "sentence": "Câu ví dụ trung bình bằng tiếng Anh",
      "translation": "Giải thích hoặc dịch bằng {language}"
    }},
    {{
      "level": "hard",
      "sentence": "Câu ví dụ khó bằng tiếng Anh",
      "translation": "Giải thích hoặc dịch bằng {language}"
    }}
  ],
  "synonyms": [
    {{
      "word": "từ đồng nghĩa 1",
      "meaning": "Giải thích nghĩa bằng {language}"
    }},
    {{
      "word": "từ đồng nghĩa 2",
      "meaning": "Giải thích nghĩa bằng {language}"
    }}
  ],
  "origin": {{
    "etymology": "Giải thích nguồn gốc từ bằng {language}",
    "historical_context": "Bối cảnh lịch sử bằng {language} (nếu có)"
  }}
}}

QUY TẮC:
1. Examples: Tối đa 3 ví dụ, sắp xếp từ dễ đến khó (easy → medium → hard)
2. Synonyms: Liệt kê các từ đồng nghĩa phổ biến, mỗi từ có giải thích bằng {language}
3. Origin: Giải thích nguồn gốc từ (etymology) và bối cảnh lịch sử (nếu có) bằng {language}
4. Tất cả giải thích, dịch thuật, và mô tả PHẢI bằng {language}
5. Chỉ có trường "sentence" trong examples được viết bằng tiếng Anh

Hãy trả về CHỈ JSON, không có text nào khác trước hoặc sau JSON.
"""


def get_vocab_info_prompt(vocab: str, language: str) -> str:
    """
    Format prompt với vocab và language
    
    Args:
        vocab: Từ vựng cần tra cứu
        language: Ngôn ngữ trả về
        
    Returns:
        Formatted prompt string
    """
    return VOCAB_INFO_PROMPT_TEMPLATE.format(vocab=vocab, language=language)
