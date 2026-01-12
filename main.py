from agno.os import AgentOS
from fastapi import FastAPI
from agno.agent import Agent
from agno_agent import vocab_agent

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

if __name__ == "__main__":
    """Run the AgentOS application.

    You can see the docs at:
    http://localhost:7777/docs

    """
    agent_os.serve(app="custom_fastapi_app:app", reload=True)
