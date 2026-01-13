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
    "",
)

# Khởi tạo db với error handling để tránh crash khi timeout
db = None
try:
    if db_url:
        # Log connection attempt (không log full URL để bảo mật)
        url_parts = db_url.split('@')
        if len(url_parts) > 1:
            safe_url = f"mongodb+srv://***@{url_parts[1].split('/')[0]}"
        else:
            safe_url = "mongodb://***"
        print(f"Connecting to MongoDB: {safe_url}")
        
        db = MongoDb(db_url=db_url)
        print("MongoDB connection established successfully")
    else:
        print("Warning: AGNO_MONGO_URL not set, running without database")
        print("To enable database features, set AGNO_MONGO_URL in your .env file")
except Exception as e:
    print(f"Warning: Failed to initialize MongoDb: {e}")
    print("Continuing without database - cache and history features will be disabled")
    print("Note: API will still work, but without caching")
    db = None

vocab_agent = Agent(
    model=AzureOpenAI(id="gpt-4.1"),
    markdown=True,
    instructions=SYSTEM_PROMPT,
    id='vocab_agent',
    db=db,  # db có thể là None nếu không kết nối được
    add_history_to_context=True if db else False,
    num_history_runs=15 if db else 0,
    read_chat_history=True if db else False,
    store_tool_messages=False,
    enable_agentic_state=True if db else False,
)
