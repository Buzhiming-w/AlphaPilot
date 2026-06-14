from fastapi.testclient import TestClient
import pytest

from alphapilot.backend.app import create_app
from alphapilot.backend.sqlalchemy_store import SqlAlchemyAlphaPilotStore


@pytest.fixture()
def database_url(tmp_path):
    return f"sqlite:///{tmp_path / 'alphapilot_test.db'}"


@pytest.mark.unit
def test_sqlalchemy_store_persists_users_tokens_quota_and_results(database_url):
    first_store = SqlAlchemyAlphaPilotStore(database_url=database_url)
    user = first_store.create_user(
        email="persist@example.com",
        password="pass-1234",
        display_name="Persistent User",
    )
    token = first_store.authenticate("persist@example.com", "pass-1234")
    quota = first_store.consume_quota(user.id)
    job = first_store.create_job(
        user_id=user.id,
        ticker="nvda",
        trade_date="2024-05-10",
        mode="demo",
    )
    completed = first_store.complete_job(
        job.id,
        normalized={"decision": "Overweight", "sections": {"final": "ok"}},
        raw_state={"company_of_interest": "NVDA"},
    )

    second_store = SqlAlchemyAlphaPilotStore(database_url=database_url)
    persisted_user = second_store.get_user_by_token(token)
    persisted_job = second_store.get_job(completed.id)
    persisted_result = second_store.get_result(completed.result_id)
    persisted_quota = second_store.get_quota(user.id)

    assert persisted_user.email == "persist@example.com"
    assert persisted_quota.used_today == quota.used_today == 1
    assert persisted_job.status == "completed"
    assert persisted_job.ticker == "NVDA"
    assert persisted_result.normalized["decision"] == "Overweight"
    assert persisted_result.raw_state["company_of_interest"] == "NVDA"


@pytest.mark.unit
def test_sqlalchemy_store_flushes_users_before_creating_quota(monkeypatch, database_url):
    flush_calls = 0

    from sqlalchemy.orm import Session

    original_flush = Session.flush

    def counting_flush(self, *args, **kwargs):
        nonlocal flush_calls
        flush_calls += 1
        return original_flush(self, *args, **kwargs)

    monkeypatch.setattr(Session, "flush", counting_flush)

    store = SqlAlchemyAlphaPilotStore(database_url=database_url)
    store.create_user(
        email="flush-order@example.com",
        password="pass-1234",
        display_name="Flush Order",
    )

    assert flush_calls >= 2


@pytest.mark.unit
def test_create_app_can_use_sqlalchemy_database_url(database_url):
    app = create_app(database_url=database_url)
    client = TestClient(app)

    registered = client.post(
        "/auth/register",
        json={
            "email": "api-sql@example.com",
            "password": "pass-1234",
            "display_name": "API SQL",
        },
    )
    assert registered.status_code == 201

    login = client.post(
        "/auth/login",
        json={"email": "api-sql@example.com", "password": "pass-1234"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    created = client.post(
        "/analysis",
        json={"ticker": "NVDA", "trade_date": "2024-05-10", "mode": "demo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201

    detail = client.get(
        f"/analysis/{created.json()['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == 200
    assert detail.json()["result"]["decision"] == "Overweight"
