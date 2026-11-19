from backend.memory import ConversationMemory


def test_memory_keeps_recent_turns_and_compacts_older_context():
    memory = ConversationMemory(redis_url="", max_recent_turns=2)
    for turn in range(5):
        memory.append(
            "session-1",
            f"question {turn}",
            f"answer {turn}",
            summarize=lambda text: "summary includes " + text[:80],
        )
    state = memory.load("session-1")
    assert len(state["messages"]) == 4
    assert "question 0" in state["summary"]
    assert state["messages"][-1]["content"] == "answer 4"


def test_memory_redacts_pii_but_preserves_an_order_id():
    memory = ConversationMemory(redis_url="")
    state = memory.append(
        "session-2",
        "My email is jane@example.com; order ORD-123",
        "I can help with that order.",
    )
    stored = str(state)
    assert "jane@example.com" not in stored
    assert "ORD-123" in stored
