from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ExampleLevel(str, Enum):
    """Mức độ khó của ví dụ"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ExampleItem(BaseModel):
    """Một ví dụ câu sử dụng từ vựng"""
    level: ExampleLevel = Field(..., description="Mức độ khó của ví dụ")
    sentence: str = Field(..., description="Câu ví dụ bằng tiếng Anh")
    translation: str = Field(..., description="Bản dịch hoặc giải thích bằng ngôn ngữ đích")


class SynonymItem(BaseModel):
    """Một từ đồng nghĩa"""
    word: str = Field(..., description="Từ đồng nghĩa")
    meaning: str = Field(..., description="Giải thích nghĩa bằng ngôn ngữ đích")


class OriginInfo(BaseModel):
    """Thông tin về nguồn gốc từ vựng"""
    etymology: str = Field(..., description="Nguồn gốc từ, giải thích bằng ngôn ngữ đích")
    historical_context: Optional[str] = Field(None, description="Bối cảnh lịch sử (tùy chọn)")


class VocabInfoRequest(BaseModel):
    """Request model cho API vocab info"""
    vocab: str = Field(..., description="Từ vựng cần tra cứu", min_length=1)
    language: str = Field(..., description="Ngôn ngữ trả về (ví dụ: Vietnamese, English, Japanese)", min_length=1)


class VocabInfoResponse(BaseModel):
    """Response model cho API vocab info"""
    vocab: str = Field(..., description="Từ vựng")
    language: str = Field(..., description="Ngôn ngữ của response")
    examples: List[ExampleItem] = Field(..., description="Danh sách ví dụ từ dễ đến khó (tối đa 3)", max_length=3)
    synonyms: List[SynonymItem] = Field(..., description="Danh sách từ đồng nghĩa")
    origin: OriginInfo = Field(..., description="Thông tin về nguồn gốc từ vựng")
