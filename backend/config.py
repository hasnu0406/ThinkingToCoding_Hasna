import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Multi-key support: comma-separated list in GROQ_API_KEYS, fallback to single GROQ_API_KEY
_multi_keys_raw = os.getenv("GROQ_API_KEYS", "")
if _multi_keys_raw.strip():
    GROQ_API_KEYS: list[str] = [k.strip() for k in _multi_keys_raw.split(",") if k.strip()]
elif GROQ_API_KEY:
    GROQ_API_KEYS = [GROQ_API_KEY]
else:
    GROQ_API_KEYS = []

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")