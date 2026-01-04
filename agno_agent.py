import json
import random
from pathlib import Path

from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from dotenv import load_dotenv
from agno.db.sqlite import SqliteDb
from system_prompt import SYSTEM_PROMPT


def get_random_words(num_words: int = 3) -> str:
    """Use this function to get random words from sounds.json.

    Args:
        num_words (int): Number of words to return. Defaults to 3.
    """

    sounds_path = Path(__file__).resolve().parent / "sounds.json"
    with sounds_path.open("r", encoding="utf-8") as handle:
        sounds = json.load(handle)

    words = list(sounds.keys())
    if num_words <= 0 or not words:
        return json.dumps([])

    sample_count = min(num_words, len(words))
    random_words = random.sample(words, sample_count)
    return json.dumps(random_words)

load_dotenv()

db = SqliteDb(db_file="tmp/data.db")

vocab_agent = Agent(
    model=AzureOpenAI(id="gpt-4.1"),
    markdown=True,
    instructions=SYSTEM_PROMPT,
    id='vocab_agent',
    db=db,
    add_history_to_context=True,
    num_history_runs=15,
    read_chat_history=True,
    tools=[get_random_words],
)
