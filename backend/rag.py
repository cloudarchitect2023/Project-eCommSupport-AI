from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.settings import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_SIMPLE_MODEL,
    PINECONE_API_KEY,
    PINECONE_INDEX,
    PINECONE_NAMESPACE,
)

STRATEGIES = {"simple", "hyde", "multi_query"}


class PolicyRetriever:
    """Pinecone retriever with simple, HyDE, and multi-query retrieval."""

    def __init__(
        self,
        index: Any | None = None,
        embed: Callable[[str], list[float]] | None = None,
        generate: Callable[[str], str] | None = None,
        namespace: str = PINECONE_NAMESPACE,
        top_k: int = 5,
    ):
        self.namespace = namespace
        self.top_k = top_k
        self._index = index
        self._embed = embed
        self._generate = generate

    def _clients(self) -> None:
        if self._index is None:
            if not PINECONE_API_KEY or not PINECONE_INDEX:
                raise RuntimeError("Configure PINECONE_API_KEY and PINECONE_INDEX.")
            from pinecone import Pinecone

            self._index = Pinecone(api_key=PINECONE_API_KEY).Index(PINECONE_INDEX)
        if self._embed is None or self._generate is None:
            if not OPENAI_API_KEY:
                raise RuntimeError("Configure OPENAI_API_KEY for policy retrieval.")
            from openai import OpenAI

            client = OpenAI(api_key=OPENAI_API_KEY)
            self._embed = self._embed or (
                lambda text: client.embeddings.create(
                    model=OPENAI_EMBEDDING_MODEL, input=text
                ).data[0].embedding
            )
            self._generate = self._generate or (
                lambda prompt: client.chat.completions.create(
                    model=OPENAI_SIMPLE_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                ).choices[0].message.content
                or ""
            )

    def _query(self, text: str) -> list[dict[str, Any]]:
        self._clients()
        assert self._index is not None and self._embed is not None
        response = self._index.query(
            vector=self._embed(text),
            top_k=self.top_k,
            include_metadata=True,
            namespace=self.namespace,
        )
        matches = getattr(response, "matches", None)
        if matches is None:
            matches = response.get("matches", [])
        results: list[dict[str, Any]] = []
        for match in matches:
            metadata = getattr(match, "metadata", None)
            if metadata is None:
                metadata = match.get("metadata", {})
            score = getattr(match, "score", None)
            if score is None:
                score = match.get("score", 0.0)
            results.append(
                {
                    "id": getattr(match, "id", None) or match.get("id", ""),
                    "score": float(score or 0.0),
                    "text": metadata.get("text", ""),
                    "source": metadata.get("source", "policy document"),
                    "title": metadata.get("title", ""),
                }
            )
        return results

    def retrieve(self, query: str, strategy: str = "simple") -> list[dict[str, Any]]:
        if strategy not in STRATEGIES:
            raise ValueError(f"Strategy must be one of {sorted(STRATEGIES)}.")
        self._clients()
        assert self._generate is not None
        queries = [query]
        if strategy == "hyde":
            hypothetical = self._generate(
                "Write a short hypothetical policy passage that would answer this "
                "customer-support question. Do not invent company-specific facts.\n"
                f"Question: {query}"
            )
            if hypothetical.strip():
                queries = [hypothetical.strip()]
        elif strategy == "multi_query":
            variants = self._generate(
                "Create exactly three distinct search queries for the support-policy "
                "question below. Return one query per line, with no numbering.\n"
                f"Question: {query}"
            )
            queries = [line.strip("- ").strip() for line in variants.splitlines() if line.strip()]
            queries = [query, *queries[:3]]

        by_id: dict[str, dict[str, Any]] = {}
        for search_query in queries:
            for item in self._query(search_query):
                current = by_id.get(item["id"])
                if current is None or item["score"] > current["score"]:
                    by_id[item["id"]] = item
        return sorted(by_id.values(), key=lambda item: item["score"], reverse=True)[: self.top_k]
