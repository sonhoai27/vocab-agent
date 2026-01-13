from agno.os import AgentOS
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from agno.agent import Agent
from agno_agent import vocab_agent
from models.vocab_info import VocabInfoRequest, VocabInfoResponse
from vocab_info_service import get_vocab_info

app: FastAPI = FastAPI(
    title="Custom FastAPI App",
    version="1.0.0",
)

agent_os = AgentOS(
    description="Example app with custom routers",
    agents=[vocab_agent],
    base_app=app  # Your custom FastAPI app
)

app = agent_os.get_app()


@app.post("/api/vocab/info", response_model=VocabInfoResponse)
async def vocab_info_endpoint(request: VocabInfoRequest):
    """
    API endpoint để lấy thông tin từ vựng (examples, synonyms, origin)
    
    - Kiểm tra cache trước
    - Nếu không có cache, gọi LLM và lưu vào cache
    - Trả về thông tin bằng ngôn ngữ được chỉ định
    """
    try:
        result = await get_vocab_info(request.vocab, request.language)
        return VocabInfoResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

if __name__ == "__main__":
    """Run the AgentOS application.

    You can see the docs at:
    http://localhost:7777/docs

    """
    agent_os.serve(app="custom_fastapi_app:app", reload=True)
