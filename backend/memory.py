from __future__ import annotations

import json
from typing import Any, Callable

from backend.guardrails import redact_pii
from backend.settings import CHAT_MAX_RECENT_TURNS, UPSTASH_REDIS_URL


class ConversationMemory:
    """Redis-backed rolling memory with an explicit bounded local fallback."""

    def __init__(
        self,
        redis_url: str = UPSTASH_REDIS_URL,
        max_recent_turns: int = CHAT_MAX_RECENT_TURNS,
    ):
        self.max_recent_turns = max(2, max_recent_turns)
        self._local: dict[str, dict[str, Any]] = {}
        self._redis = None
        if redis_url:
            try:
                import redis
            except ImportError as exc:
                raise RuntimeError("Install the redis package to use Upstash memory.") from exc
            self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        if not session_id or len(session_id) > 100:
            raise ValueError("Provide a valid session ID.")
        return f"ecomm-support:conversation:{session_id}"

    def load(self, session_id: str) -> dict[str, Any]:
        key = self._key(session_id)
        raw = self._redis.get(key) if self._redis else None
        if raw:
            return json.loads(raw)
        return self._local.get(key, {"summary": "", "messages": []}).copy()

    def append(
        self,
        session_id: str,
        user_text: str,
        assistant_text: str,
        summarize: Callable[[str], str] | None = None,
    ) -> dict[str, Any]:
        key = self._key(session_id)
        state = self.load(session_id)
        state["messages"].extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": assistant_text},
            ]
        )
        cutoff = self.max_recent_turns * 2
        if len(state["messages"]) > cutoff:
            old_messages = state["messages"][:-cutoff]
            old_text = "\n".join(
                f"{item['role']}: {item['content']}" for item in old_messages
            )
            old_text = f"{state['summary']}\n{old_text}".strip()
            summary = summarize(old_text) if summarize else old_text[-1200:]
            state["summary"] = str(redact_pii(summary))[:1600]
            state["messages"] = state["messages"][-cutoff:]
        safe_state = redact_pii(state)
        serialized = json.dumps(safe_state, ensure_ascii=True)
        if self._redis:
            self._redis.set(key, serialized)
        else:
            self._local[key] = safe_state
        return safe_state
