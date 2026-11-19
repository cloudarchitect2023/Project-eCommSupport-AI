from fastapi.testclient import TestClient

from backend import api


class FakeAgent:
    async def respond(self, **kwargs):
        return {
            "answer": "Order ORD-1 is shipped.",
            "sources": [],
            "evidence": [],
            "tools": ["check_order_status"],
            "latency_ms": 4.2,
            "model": "offline-demo",
        }


def test_health_endpoint_reports_configuration_without_secrets():
    response = TestClient(api.app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "api_key" not in response.json()


def test_chat_endpoint_validates_strategy_and_forwards_request(monkeypatch):
    monkeypatch.setattr(api, "agent", FakeAgent())
    response = TestClient(api.app).post(
        "/chat",
        json={
            "question": "Check order ORD-1",
            "session_id": "test-session",
            "customer_id": "demo-customer",
            "retrieval_strategy": "multi_query",
        },
    )
    assert response.status_code == 200
    assert response.json()["tools"] == ["check_order_status"]
    invalid = TestClient(api.app).post(
        "/chat",
        json={
            "question": "Check order ORD-1",
            "session_id": "test-session",
            "customer_id": "demo-customer",
            "retrieval_strategy": "raw-sql",
        },
    )
    assert invalid.status_code == 422
