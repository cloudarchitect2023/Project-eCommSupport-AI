from types import SimpleNamespace

from backend.evaluation import retrieval_metrics
from backend.rag import PolicyRetriever


class FakeIndex:
    def __init__(self):
        self.queries = []

    def query(self, vector, top_k, include_metadata, namespace):
        self.queries.append((vector, namespace))
        name = vector[0]
        docs = {
            "simple question": [("returns-window", 0.9), ("damaged-items", 0.7)],
            "hypothetical answer": [("damaged-items", 0.95), ("returns-window", 0.8)],
            "variant query": [("extended-warranty", 0.92)],
        }
        matches = [
            {
                "id": doc_id,
                "score": score,
                "metadata": {
                    "text": f"Evidence for {doc_id}",
                    "title": doc_id,
                    "source": "policy.md",
                },
            }
            for doc_id, score in docs.get(name, [])
        ]
        return SimpleNamespace(matches=matches[:top_k])


def test_simple_hyde_and_multi_query_retrieval():
    index = FakeIndex()
    retriever = PolicyRetriever(
        index=index,
        embed=lambda text: [text],
        generate=lambda prompt: (
            "hypothetical answer"
            if "hypothetical" in prompt
            else "variant query\nsecond variant"
        ),
        namespace="test",
    )
    simple = retriever.retrieve("simple question", "simple")
    hyde = retriever.retrieve("simple question", "hyde")
    multi = retriever.retrieve("simple question", "multi_query")
    assert simple[0]["id"] == "returns-window"
    assert hyde[0]["id"] == "damaged-items"
    assert multi[0]["id"] == "extended-warranty"
    assert len(index.queries) == 5
    assert all(namespace == "test" for _, namespace in index.queries)


def test_retrieval_metrics_calculate_recall_and_reciprocal_rank():
    assert retrieval_metrics({"a", "b"}, ["x", "b", "a"]) == {
        "recall_at_k": 1.0,
        "reciprocal_rank": 0.5,
    }
