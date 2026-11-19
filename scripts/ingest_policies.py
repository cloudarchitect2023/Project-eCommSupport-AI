from __future__ import annotations

import json

from backend.settings import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    PINECONE_API_KEY,
    PINECONE_INDEX,
    PINECONE_NAMESPACE,
    PROJECT_ROOT,
)


def main() -> None:
    if not OPENAI_API_KEY or not PINECONE_API_KEY or not PINECONE_INDEX:
        raise RuntimeError(
            "Set OPENAI_API_KEY, PINECONE_API_KEY, and PINECONE_INDEX in .env first."
        )
    from openai import OpenAI
    from pinecone import Pinecone

    documents = [
        json.loads(line)
        for line in (PROJECT_ROOT / "data" / "policies.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    openai = OpenAI(api_key=OPENAI_API_KEY)
    index = Pinecone(api_key=PINECONE_API_KEY).Index(PINECONE_INDEX)
    records = []
    for document in documents:
        vector = openai.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL, input=document["text"]
        ).data[0].embedding
        records.append(
            {
                "id": document["id"],
                "values": vector,
                "metadata": {
                    "text": document["text"],
                    "title": document["title"],
                    "source": document["source"],
                },
            }
        )
    index.upsert(vectors=records, namespace=PINECONE_NAMESPACE)
    print(f"Indexed {len(records)} policy documents in namespace {PINECONE_NAMESPACE!r}.")


if __name__ == "__main__":
    main()
