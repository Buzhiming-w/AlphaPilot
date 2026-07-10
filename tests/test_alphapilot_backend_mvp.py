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
def test_admin_analysis_creation_bypasses_daily_quota(client):
    admin_login = client.post(
        "/auth/login", json={"email": "admin@alphapilot.dev", "password": "admin"}
    )
    assert admin_login.status_code == 200
    headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    admin_me = client.get("/me", headers=headers).json()
    user_id = admin_me["id"]
    patched = client.patch(
        f"/admin/users/{user_id}",
        json={"daily_limit": 0},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["quota"]["daily_limit"] == 0

    created = client.post(
        "/analysis",
        json={"ticker": "NVDA", "trade_date": "2024-05-10", "mode": "demo"},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["status"] == "completed"
    me_after = client.get("/me", headers=headers).json()
    assert me_after["quota"]["used_today"] == 0


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


@pytest.mark.unit
def test_copilot_route_requires_auth(client):
    response = client.post("/copilot/route", json={"message": "Compare NVDA and AMD"})

    assert response.status_code == 401


@pytest.mark.unit
def test_copilot_route_returns_draft_without_consuming_quota(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    draft = client.post(
        "/copilot/route",
        json={"message": "帮我比较黄仁勋的公司和 AMD，从 2024 年初到现在"},
        headers=headers,
    )

    assert draft.status_code == 200
    payload = draft.json()
    assert payload["intent"] == "compare"
    assert [symbol["ticker"] for symbol in payload["symbols"]] == ["NVDA", "AMD"]
    assert [group["query"] for group in payload["candidate_groups"]] == ["黄仁勋", "AMD"]
    assert payload["unresolved_entities"] == []
    assert payload["start_date"] == "2024-01-01"
    assert payload["requires_confirmation"] is True

    me = client.get("/me", headers=headers).json()
    assert me["quota"]["used_today"] == 0


@pytest.mark.unit
def test_copilot_route_returns_unresolved_entities_for_draft_refinement(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    draft = client.post(
        "/copilot/route",
        json={"message": "比较 NVDA 和 Neverland Robotics"},
        headers=headers,
    )

    assert draft.status_code == 200
    payload = draft.json()
    assert payload["intent"] == "clarify"
    assert [symbol["ticker"] for symbol in payload["symbols"]] == ["NVDA"]
    assert payload["unresolved_entities"] == ["Neverland Robotics"]
    assert payload["requires_confirmation"] is False


@pytest.mark.unit
def test_watchlist_add_list_and_delete_for_owner(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/watchlist",
        json={
            "ticker": "nvda",
            "company_name": "NVIDIA Corporation",
            "market": "US",
            "exchange": "NASDAQ",
            "currency": "USD",
            "note": "AI infrastructure leader",
            "source": "copilot",
        },
        headers=headers,
    )

    assert created.status_code == 201
    item = created.json()
    assert item["ticker"] == "NVDA"
    assert item["note"] == "AI infrastructure leader"

    listed = client.get("/watchlist", headers=headers)
    assert listed.status_code == 200
    assert [entry["id"] for entry in listed.json()] == [item["id"]]

    deleted = client.delete(f"/watchlist/{item['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/watchlist", headers=headers).json() == []


@pytest.mark.unit
def test_compare_create_and_get_for_owner(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/compare",
        json={
            "symbols": [
                {
                    "ticker": "NVDA",
                    "company_name": "NVIDIA Corporation",
                    "market": "US",
                    "exchange": "NASDAQ",
                    "currency": "USD",
                },
                {
                    "ticker": "AMD",
                    "company_name": "Advanced Micro Devices, Inc.",
                    "market": "US",
                    "exchange": "NASDAQ",
                    "currency": "USD",
                },
            ],
            "start_date": "2024-01-01",
            "end_date": "2026-06-15",
            "analysis_anchor": "2026-06-15",
            "source": "copilot",
        },
        headers=headers,
    )

    assert created.status_code == 201
    workflow = created.json()
    assert workflow["status"] == "draft"
    assert [symbol["ticker"] for symbol in workflow["symbols"]] == ["NVDA", "AMD"]

    fetched = client.get(f"/compare/{workflow['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == workflow["id"]


@pytest.mark.unit
def test_inactive_user_cannot_create_watchlist_or_compare(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    admin_login = client.post(
        "/auth/login", json={"email": "admin@alphapilot.dev", "password": "admin"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    user_id = client.get("/me", headers=headers).json()["id"]
    client.patch(
        f"/admin/users/{user_id}",
        json={"is_active": False},
        headers=admin_headers,
    )

    watchlist = client.post(
        "/watchlist",
        json={
            "ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "market": "US",
            "exchange": "NASDAQ",
            "currency": "USD",
        },
        headers=headers,
    )
    compare = client.post(
        "/compare",
        json={
            "symbols": [
                {
                    "ticker": "NVDA",
                    "company_name": "NVIDIA Corporation",
                    "market": "US",
                    "exchange": "NASDAQ",
                    "currency": "USD",
                },
                {
                    "ticker": "AMD",
                    "company_name": "Advanced Micro Devices, Inc.",
                    "market": "US",
                    "exchange": "NASDAQ",
                    "currency": "USD",
                },
            ],
            "source": "copilot",
        },
        headers=headers,
    )

    assert watchlist.status_code == 403
    assert compare.status_code == 403
