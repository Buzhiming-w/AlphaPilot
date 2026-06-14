from fastapi.testclient import TestClient
import pytest

from alphapilot.backend.app import create_app
from alphapilot.backend.result_normalizer import load_demo_result, normalize_engine_state
from alphapilot.backend.store import AlphaPilotStore


@pytest.fixture()
def client():
    store = AlphaPilotStore()
    app = create_app(store=store)
    return TestClient(app)


def _register_and_login(client, email="user@example.com", password="pass-1234"):
    register = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert register.status_code == 201

    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


@pytest.mark.unit
def test_register_login_and_me_flow(client):
    token = _register_and_login(client)

    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"
    assert me.json()["role"] == "user"
    assert me.json()["is_active"] is True


@pytest.mark.unit
def test_analysis_creation_consumes_quota_and_exposes_demo_result(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/analysis",
        json={"ticker": "NVDA", "trade_date": "2024-05-10", "mode": "demo"},
        headers=headers,
    )
    assert created.status_code == 201
    job = created.json()
    assert job["ticker"] == "NVDA"
    assert job["status"] == "completed"
    assert job["result_id"]

    detail = client.get(f"/analysis/{job['id']}", headers=headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["result"]["decision"] == "Overweight"
    assert "market" in payload["result"]["sections"]

    me = client.get("/me", headers=headers).json()
    assert me["quota"]["used_today"] == 1
    assert me["quota"]["daily_limit"] == 3


@pytest.mark.unit
def test_public_demo_reference_does_not_require_auth_or_consume_quota(client):
    response = client.get("/demo/reference")

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "Overweight"
    assert payload["ticker"] == "NVDA"
    assert "final" in payload["sections"]


@pytest.mark.unit
def test_load_demo_result_uses_packaged_fixture_outside_runtime_workdir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    normalized, raw_state = load_demo_result()

    assert normalized["decision"] == "Overweight"
    assert normalized["ticker"] == "NVDA"
    assert raw_state["company_of_interest"] == "NVDA"


@pytest.mark.unit
def test_inactive_user_cannot_create_analysis(client):
    token = _register_and_login(client)
    admin_login = client.post(
        "/auth/login", json={"email": "admin@alphapilot.dev", "password": "admin"}
    )
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    user_id = client.get("/me", headers={"Authorization": f"Bearer {token}"}).json()["id"]
    patched = client.patch(
        f"/admin/users/{user_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert patched.status_code == 200

    blocked = client.post(
        "/analysis",
        json={"ticker": "AAPL", "trade_date": "2024-05-10", "mode": "demo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "User account is disabled"


@pytest.mark.unit
def test_normalize_engine_state_handles_logged_trader_decision_name():
    state = {
        "company_of_interest": "NVDA",
        "trade_date": "2024-05-10",
        "market_report": "Market report",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        "investment_plan": "Investment plan",
        "trader_investment_decision": "Trader decision",
        "final_trade_decision": "Final decision",
    }

    normalized = normalize_engine_state(state, processed_decision="Overweight")

    assert normalized["ticker"] == "NVDA"
    assert normalized["decision"] == "Overweight"
    assert normalized["sections"]["trader"] == "Trader decision"
    assert normalized["sections"]["final"] == "Final decision"
