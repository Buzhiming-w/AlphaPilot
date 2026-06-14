from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from .security import hash_password, new_token, verify_password


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    display_name: str
    role: str = "user"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UserQuota:
    user_id: str
    daily_limit: int = 3
    used_today: int = 0
    usage_date: date = field(default_factory=date.today)


@dataclass
class AnalysisJob:
    id: str
    user_id: str
    ticker: str
    trade_date: str
    mode: str
    status: str = "queued"
    selected_analysts: list[str] = field(default_factory=lambda: ["market"])
    result_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnalysisResult:
    id: str
    job_id: str
    normalized: dict[str, Any]
    raw_state: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AlphaPilotStore:
    """Small in-memory repository for the local MVP and tests.

    The public methods mirror the database operations the production SQL layer
    will need, keeping the API layer independent from the storage choice.
    """

    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.users_by_email: dict[str, str] = {}
        self.tokens: dict[str, str] = {}
        self.quotas: dict[str, UserQuota] = {}
        self.jobs: dict[str, AnalysisJob] = {}
        self.results: dict[str, AnalysisResult] = {}
        self.create_user(
            email="admin@alphapilot.dev",
            password="admin",
            display_name="AlphaPilot Admin",
            role="admin",
        )

    def create_user(
        self,
        email: str,
        password: str,
        display_name: str,
        role: str = "user",
    ) -> User:
        normalized_email = email.strip().lower()
        if normalized_email in self.users_by_email:
            raise ValueError("Email already registered")
        user = User(
            id=str(uuid4()),
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=display_name.strip() or normalized_email,
            role=role,
        )
        self.users[user.id] = user
        self.users_by_email[user.email] = user.id
        self.quotas[user.id] = UserQuota(user_id=user.id)
        return user

    def authenticate(self, email: str, password: str) -> str | None:
        user = self.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            return None
        token = new_token()
        self.tokens[token] = user.id
        return token

    def get_user_by_email(self, email: str) -> User | None:
        user_id = self.users_by_email.get(email.strip().lower())
        return self.users.get(user_id) if user_id else None

    def get_user_by_token(self, token: str) -> User | None:
        user_id = self.tokens.get(token)
        return self.users.get(user_id) if user_id else None

    def get_quota(self, user_id: str) -> UserQuota:
        quota = self.quotas[user_id]
        today = date.today()
        if quota.usage_date != today:
            quota.used_today = 0
            quota.usage_date = today
        return quota

    def consume_quota(self, user_id: str) -> UserQuota:
        quota = self.get_quota(user_id)
        if quota.used_today >= quota.daily_limit:
            raise ValueError("Daily quota exhausted")
        quota.used_today += 1
        return quota

    def set_user_controls(
        self,
        user_id: str,
        *,
        is_active: bool | None = None,
        daily_limit: int | None = None,
    ) -> User:
        user = self.users[user_id]
        if is_active is not None:
            user.is_active = is_active
        if daily_limit is not None:
            self.quotas[user_id].daily_limit = daily_limit
        return user

    def create_job(
        self,
        user_id: str,
        ticker: str,
        trade_date: str,
        mode: str,
        selected_analysts: list[str] | None = None,
    ) -> AnalysisJob:
        job = AnalysisJob(
            id=str(uuid4()),
            user_id=user_id,
            ticker=ticker.strip().upper(),
            trade_date=trade_date,
            mode=mode,
            selected_analysts=selected_analysts or ["market"],
        )
        self.jobs[job.id] = job
        return job

    def complete_job(
        self,
        job_id: str,
        normalized: dict[str, Any],
        raw_state: dict[str, Any],
    ) -> AnalysisJob:
        job = self.jobs[job_id]
        result = AnalysisResult(
            id=str(uuid4()),
            job_id=job_id,
            normalized=normalized,
            raw_state=raw_state,
        )
        self.results[result.id] = result
        job.status = "completed"
        job.result_id = result.id
        job.updated_at = datetime.now(timezone.utc)
        return job

    def fail_job(self, job_id: str, error: str) -> AnalysisJob:
        job = self.jobs[job_id]
        job.status = "failed"
        job.error = error
        job.updated_at = datetime.now(timezone.utc)
        return job

    def list_jobs_for_user(self, user: User) -> list[AnalysisJob]:
        if user.role == "admin":
            return sorted(self.jobs.values(), key=lambda job: job.created_at, reverse=True)
        return sorted(
            [job for job in self.jobs.values() if job.user_id == user.id],
            key=lambda job: job.created_at,
            reverse=True,
        )
