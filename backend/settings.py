from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def setting(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def bool_setting(name: str, default: bool = False) -> bool:
    value = setting(name, str(default)).lower()
    return value in {"1", "true", "yes", "on"}


DATABASE_URL = setting(
    "DATABASE_URL", f"sqlite:///{(PROJECT_ROOT / 'data' / 'ecomm_support.db').as_posix()}"
)
OPENAI_API_KEY = setting("OPENAI_API_KEY")
OPENAI_SIMPLE_MODEL = setting("OPENAI_SIMPLE_MODEL", "gpt-4o-mini")
OPENAI_COMPLEX_MODEL = setting("OPENAI_COMPLEX_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = setting("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
PINECONE_API_KEY = setting("PINECONE_API_KEY")
PINECONE_INDEX = setting("PINECONE_INDEX")
PINECONE_NAMESPACE = setting("PINECONE_NAMESPACE", "company-policies")
UPSTASH_REDIS_URL = setting("UPSTASH_REDIS_URL")
LANGSMITH_TRACING = bool_setting("LANGSMITH_TRACING")
CHAT_MAX_RECENT_TURNS = max(2, int(setting("CHAT_MAX_RECENT_TURNS", "4")))


def ensure_data_directory() -> None:
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
