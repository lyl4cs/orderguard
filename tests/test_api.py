import pytest
from fastapi.testclient import TestClient

from orderguard import api

client = TestClient(api.app)


@pytest.fixture(autouse=True)
def fresh_history(monkeypatch):
    api.recent_orders.clear()
    monkeypatch.setattr(api, "STORE_MEDIAN_CENTS", 4000)


def order_json(**overrides):
    data = {
        "order_id": "1001",
        "email": "jane@example.com",
        "total_cents": 4000,
        "billing": {"country": "US", "province": "IL", "zip_code": "60462"},
        "shipping": {"country": "US", "province": "IL", "zip_code": "60462"},
        "is_first_order": False,
        "created_at": "2026-01-01T12:00:00Z",
        "ip": "203.0.113.10",
    }
    data.update(overrides)
    return data


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_normal_order_is_approved():
    response = client.post("/score", json=order_json())
    assert response.status_code == 200
    assert response.json() == {"order_id": "1001", "decision": "approve", "score": 0, "reasons": []}


def test_risky_order_returns_reasons():
    body = order_json(
        total_cents=24000,
        is_first_order=True,
        shipping={"country": "CA", "province": "ON", "zip_code": "K1A 0B1"},
    )
    data = client.post("/score", json=body).json()
    assert data["decision"] == "decline"
    assert data["score"] == 75
    assert len(data["reasons"]) == 3


def test_velocity_uses_earlier_requests():
    for i, minute in enumerate(["00", "02", "04"]):
        response = client.post(
            "/score",
            json=order_json(order_id=f"v-{i}", created_at=f"2026-01-01T12:{minute}:00Z"),
        )
    assert response.json()["score"] == 30
    assert "3 orders from this email" in response.json()["reasons"][0]


def test_retried_order_is_stored_once():
    client.post("/score", json=order_json())
    client.post("/score", json=order_json())
    assert len(api.recent_orders) == 1


def test_missing_timezone_is_treated_as_utc():
    response = client.post("/score", json=order_json(created_at="2026-01-01T12:00:00"))
    assert response.status_code == 200


@pytest.mark.parametrize(
    "bad",
    [
        {"total_cents": -1},
        {"email": "not-an-email"},
        {"billing": {"country": "USA", "province": "IL", "zip_code": "60462"}},
        {"order_id": ""},
    ],
)
def test_bad_input_returns_422(bad):
    assert client.post("/score", json=order_json(**bad)).status_code == 422


def test_missing_field_returns_422():
    body = order_json()
    del body["email"]
    assert client.post("/score", json=body).status_code == 422
