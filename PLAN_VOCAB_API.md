# Kế hoạch bổ sung API Route POST cho Vocabulary Information

## Mục tiêu
Tạo một API route POST mới để lấy thông tin chi tiết về từ vựng:
- Các ví dụ từ dễ đến khó (tối đa 3)
- Synonyms (từ đồng nghĩa)
- Origin (nguồn gốc)
- Tất cả nội dung trả về phải matching với ngôn ngữ được truyền lên

## Cấu trúc API

### Endpoint
```
POST /api/vocab/info
```

### Request Body
```json
{
  "vocab": "string",      // Từ vựng cần tra cứu
  "language": "string"    // Ngôn ngữ trả về (ví dụ: "Vietnamese", "English", "Japanese")
}
```

### Response Format
```json
{
  "vocab": "string",
  "language": "string",
  "examples": [
    {
      "level": "easy",
      "sentence": "string",
      "translation": "string"  // Dịch sang language nếu cần
    },
    {
      "level": "medium",
      "sentence": "string",
      "translation": "string"
    },
    {
      "level": "hard",
      "sentence": "string",
      "translation": "string"
    }
  ],
  "synonyms": [
    {
      "word": "string",
      "meaning": "string"  // Giải thích bằng language
    }
  ],
  "origin": {
    "etymology": "string",  // Nguồn gốc từ, giải thích bằng language
    "historical_context": "string"  // Bối cảnh lịch sử (optional)
  }
}
```

## Các bước triển khai

### Bước 1: Tạo file chứa prompt cho LLM
- Tạo file `vocab_info_prompt.py`
- Định nghĩa prompt template để yêu cầu LLM trả về đúng format JSON
- Prompt phải đảm bảo:
  - Tất cả nội dung (examples, synonyms, origin) đều được viết bằng `language` được truyền vào
  - Examples được sắp xếp từ dễ đến khó
  - Tối đa 3 examples
  - JSON format chính xác

### Bước 2: Tạo function cache MongoDB
- Tạo file `vocab_cache.py` để quản lý cache
- Tạo function `get_cached_vocab_info(vocab: str, language: str) -> dict | None`
  - Tạo cache key từ vocab (lowercase, normalized) + language
  - Query MongoDB collection `vocab_cache` với key này
  - Trả về cached data nếu tồn tại, None nếu không
- Tạo function `save_vocab_info_to_cache(vocab: str, language: str, data: dict) -> None`
  - Lưu data vào MongoDB collection `vocab_cache`
  - Document structure:
    ```json
    {
      "_id": "vocab_language_key",  // composite key: vocab_lowercase_language
      "vocab": "string",
      "language": "string",
      "data": { ... },  // full response data
      "created_at": "datetime",
      "updated_at": "datetime"
    }
    ```
  - Sử dụng upsert để update nếu đã tồn tại

### Bước 3: Tạo function gọi LLM
- Tạo function `get_vocab_info(vocab: str, language: str) -> dict`
- Function này sẽ:
  - **Kiểm tra cache trước**: Gọi `get_cached_vocab_info()`
  - Nếu có cache, trả về ngay lập tức
  - Nếu không có cache:
    - Format prompt với vocab và language
    - Gọi LLM model (có thể tái sử dụng AzureOpenAI model từ `agno_agent.py`)
    - Parse JSON response từ LLM
    - Validate response
    - **Lưu vào cache**: Gọi `save_vocab_info_to_cache()` trước khi return
    - Return dict

### Bước 4: Tạo API route trong main.py
- Thêm route POST `/api/vocab/info` vào FastAPI app
- Route sẽ:
  - Nhận request body với vocab và language
  - Validate input
  - Gọi function `get_vocab_info()`
  - Trả về JSON response
  - Handle errors (invalid vocab, LLM errors, parsing errors)

### Bước 5: Tạo Pydantic models cho request/response
- Tạo `VocabInfoRequest` model cho request body
- Tạo `VocabInfoResponse` model cho response
- Tạo nested models cho examples, synonyms, origin
- Đảm bảo type safety và validation

### Bước 6: Testing
- Test với các từ vựng khác nhau
- Test với các ngôn ngữ khác nhau
- Test edge cases (từ không tồn tại, language không hợp lệ)
- Test JSON parsing và error handling

## Chi tiết kỹ thuật

### LLM Prompt Template
Prompt sẽ yêu cầu LLM:
1. Phân tích từ vựng `{vocab}`
2. Tạo 3 ví dụ câu từ dễ đến khó (tối đa 3)
3. Liệt kê synonyms với giải thích bằng `{language}`
4. Giải thích origin/etymology bằng `{language}`
5. Trả về đúng JSON format
6. Tất cả nội dung phải bằng `{language}`

### Error Handling
- 400: Invalid request (thiếu vocab hoặc language)
- 422: Validation error (Pydantic validation)
- 500: LLM error hoặc parsing error
- 404: Không tìm thấy thông tin về từ vựng (optional)

### Caching Strategy
- **Cache Key**: `{vocab_lowercase}_{language}` (ví dụ: "hello_vietnamese")
- **Collection**: `vocab_cache` trong MongoDB
- **Cache Flow**:
  1. Request đến → Check cache với key (vocab + language)
  2. Nếu có cache → Return ngay (không gọi LLM)
  3. Nếu không có cache → Gọi LLM → Save vào cache → Return
- **Cache Benefits**:
  - Giảm chi phí gọi LLM
  - Tăng tốc độ response
  - Đảm bảo consistency cho cùng vocab + language
- **Cache Management** (optional):
  - Có thể thêm TTL (Time To Live) nếu cần refresh cache sau một thời gian
  - Có thể thêm endpoint để clear cache nếu cần

### Dependencies
- Sử dụng lại AzureOpenAI model từ `agno_agent.py` hoặc tạo instance mới
- Sử dụng lại MongoDB connection từ `agno_agent.py` (db instance)
- FastAPI cho routing
- Pydantic cho validation
- json để parse response từ LLM
- datetime để track cache timestamps

## File structure
```
vocab-agent/
├── api/
│   └── index.py (existing)
├── vocab_info_prompt.py (new) - prompt template
├── vocab_cache.py (new) - MongoDB cache functions
├── vocab_info_service.py (new) - chứa logic gọi LLM và cache
├── models/
│   └── vocab_info.py (new) - Pydantic models
└── main.py (modified) - thêm route mới
```

## Thứ tự implementation
1. Tạo Pydantic models (`models/vocab_info.py`)
2. Tạo prompt template (`vocab_info_prompt.py`)
3. Tạo cache functions (`vocab_cache.py`)
4. Tạo service function (`vocab_info_service.py`) - tích hợp cache
5. Thêm route vào `main.py`
6. Test và fix bugs
7. Test cache hit/miss scenarios
