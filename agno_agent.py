import json
import os
import random
from pathlib import Path

from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from dotenv import load_dotenv
from agno.db.sqlite import SqliteDb
from system_prompt import SYSTEM_PROMPT

load_dotenv()


def _default_db_dir() -> Path:
    if Path("/tmp").exists():
        return Path("/tmp")

    local_dir = Path(__file__).resolve().parent / "tmp"
    local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir


db_path = Path(os.getenv("AGNO_DB_PATH", str(_default_db_dir() / "data_2.db")))
db = SqliteDb(db_file=str(db_path))

vocab_agent = Agent(
    model=AzureOpenAI(id="gpt-4.1"),
    markdown=True,
    instructions=SYSTEM_PROMPT,
    id='vocab_agent',
    db=db,
    add_history_to_context=True,
    num_history_runs=15,
    read_chat_history=True,
    store_tool_messages=False,
    enable_agentic_state=True,
)
