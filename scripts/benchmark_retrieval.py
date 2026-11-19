from __future__ import annotations

import json

from backend.evaluation import load_golden_dataset, retrieval_metrics
from backend.rag import STRATEGIES, PolicyRetriever
from backend.settings import PROJECT_ROOT


def main() -> None:
    examples = [
        item for item in load_golden_dataset() if item.get("expected_policy_ids")
    ]
    retriever = PolicyRetriever()
    detailed: dict[str, list[dict]] = {}
    summary: dict[str, dict[str, float]] = {}
    for strategy in sorted(STRATEGIES):
        rows = []
        recalls, reciprocal_ranks = [], []
        for example in examples:
            results = retriever.retrieve(example["question"], strategy)
            metrics = retrieval_metrics(
                set(example["expected_policy_ids"]),
                [item["id"] for item in results],
            )
            recalls.append(metrics["recall_at_k"])
            reciprocal_ranks.append(metrics["reciprocal_rank"])
            rows.append(
                {
                    "question": example["question"],
                    "expected_policy_ids": example["expected_policy_ids"],
                    "retrieved_policy_ids": [item["id"] for item in results],
                    **metrics,
                }
            )
        detailed[strategy] = rows
        summary[strategy] = {
            "queries": len(rows),
            "mean_recall_at_k": round(sum(recalls) / len(recalls), 4),
            "mean_reciprocal_rank": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4),
        }
    report = {"summary": summary, "details": detailed}
    output = PROJECT_ROOT / "data" / "retrieval-benchmark.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Detailed results: {output}")


if __name__ == "__main__":
    main()
