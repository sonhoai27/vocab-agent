import json
import os
import random

from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from dotenv import load_dotenv
from agno.db.mongo import MongoDb
from system_prompt import SYSTEM_PROMPT

load_dotenv()


db_url = os.getenv(
    "AGNO_MONGO_URL",
    "mongodb+srv://project0:m89NF6G8YOHPXwrJ@cluster0.hujdnhm.mongodb.net/?appName=Cluster0",
)
db = MongoDb(db_url=db_url)

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
