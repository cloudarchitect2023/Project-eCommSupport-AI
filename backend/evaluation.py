from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from backend.settings import PROJECT_ROOT


def load_golden_dataset() -> list[dict[str, Any]]:
    source = PROJECT_ROOT / "data" / "golden_dataset.jsonl"
    return [
        json.loads(line)
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def score_results(
    examples: list[dict[str, Any]], results: list[dict[str, Any]]
) -> dict[str, Any]:
    if len(examples) != len(results) or not examples:
        raise ValueError("Provide one non-empty result for every golden example.")
    tool_correct = []
    unsupported_policy_claims = []
    latencies = []
    for example, result in zip(examples, results):
        expected = example["expected_tool"]
        actual_tools = result.get("tools", [])
        tool_correct.append(
            (expected == "decline" and not actual_tools)
            or (expected != "decline" and expected in actual_tools)
        )
        is_policy_case = expected == "search_policies"
        answer = result.get("answer", "")
        has_citation = bool(re.search(r"\[\d+\]", answer))
        has_source = bool(result.get("sources"))
        unsupported_policy_claims.append(
            is_policy_case and not (has_citation and has_source)
        )
        latencies.append(float(result.get("latency_ms", 0.0)))

    return {
        "examples": len(examples),
        "tool_call_accuracy": round(sum(tool_correct) / len(tool_correct), 4),
        "uncited_policy_answer_rate": round(
            sum(unsupported_policy_claims) / max(1, sum(
                example["expected_tool"] == "search_policies" for example in examples
            )),
            4,
        ),
        "mean_latency_ms": round(sum(latencies) / len(latencies), 2),
    }


def retrieval_metrics(
    relevant_ids: set[str], ranked_ids: list[str]
) -> dict[str, float]:
    if not relevant_ids:
        raise ValueError("At least one relevant document ID is required.")
    hits = [index for index, item in enumerate(ranked_ids, start=1) if item in relevant_ids]
    return {
        "recall_at_k": round(len(set(ranked_ids) & relevant_ids) / len(relevant_ids), 4),
        "reciprocal_rank": round(1 / hits[0], 4) if hits else 0.0,
    }


def results_path() -> Path:
    return PROJECT_ROOT / "data" / "evaluation-results.json"
