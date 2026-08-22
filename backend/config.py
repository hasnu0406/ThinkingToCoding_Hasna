import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
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
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_API_BASE_URL = os.getenv("CEREBRAS_API_BASE_URL", "https://api.cerebras.ai/v1")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_API_BASE_URL = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")

# ── LLM Model Configuration ──
GROQ_MODEL       = os.getenv("GROQ_MODEL",       "llama-3.3-70b-versatile")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL",  "meta-llama/llama-3.3-70b-instruct")
CEREBRAS_MODEL   = os.getenv("CEREBRAS_MODEL",    "gpt-oss-120b")
NVIDIA_MODEL     = os.getenv("NVIDIA_MODEL",      "nvidia/llama-3.1-nemotron-70b-instruct")
NVIDIA_FALLBACK_MODEL = os.getenv("NVIDIA_FALLBACK_MODEL", "meta/llama-3.1-8b-instruct")

# ── Azure OpenAI Configuration ──
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-11-20")

# ── Sampling Parameters ──
JSON_TEMPERATURE = float(os.getenv("JSON_TEMPERATURE", "0.1"))
JSON_MAX_TOKENS  = int(os.getenv("JSON_MAX_TOKENS",    "1200"))
TEXT_TEMPERATURE = float(os.getenv("TEXT_TEMPERATURE", "0.6"))
TEXT_MAX_TOKENS  = int(os.getenv("TEXT_MAX_TOKENS",    "1024"))
