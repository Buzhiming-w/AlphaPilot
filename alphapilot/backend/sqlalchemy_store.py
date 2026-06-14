from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .db_models import (
    AnalysisJobRecord,
    AnalysisResultRecord,
    ApiUsageLogRecord,
    Base,
    UserQuotaRecord,
    UserRecord,
    UserTokenRecord,
)
from .security import hash_password, new_token, verify_password
from .store import AnalysisJob, AnalysisResult, ApiUsageLog, User, UserQuota


class SqlAlchemyAlphaPilotStore:
    """SQLAlchemy-backed repository for persistent AlphaPilot product data."""

    def __init__(self, database_url: str, *, create_schema: bool = True) -> None:
        self.database_url = database_url
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine: Engine = create_engine(database_url, future=True, connect_args=connect_args)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)
        if create_schema:
            Base.metadata.create_all(self.engine)
        self._seed_admin()

    def _seed_admin(self) -> None:
        with self.session_factory() as session:
            existing = self._get_user_record_by_email(session, "admin@alphapilot.dev")
            if existing:
                return
            user = UserRecord(
                id=str(uuid4()),
                email="admin@alphapilot.dev",
                password_hash=hash_password("admin"),
                display_name="AlphaPilot Admin",
                role="admin",
            )
            session.add(user)
            session.add(UserQuotaRecord(user_id=user.id))
            session.commit()

    def create_user(
        self,
        email: str,
        password: str,
        display_name: str,
        role: str = "user",
    ) -> User:
        normalized_email = email.strip().lower()
        with self.session_factory() as session:
            if self._get_user_record_by_email(session, normalized_email):
                raise ValueError("Email already registered")
            record = UserRecord(
                id=str(uuid4()),
                email=normalized_email,
                password_hash=hash_password(password),
                display_name=display_name.strip() or normalized_email,
                role=role,
            )
            session.add(record)
            session.add(UserQuotaRecord(user_id=record.id))
            session.commit()
            return self._to_user(record)

    def authenticate(self, email: str, password: str) -> str | None:
        with self.session_factory() as session:
            record = self._get_user_record_by_email(session, email.strip().lower())
            if not record or not verify_password(password, record.password_hash):
                return None
            token = new_token()
            session.add(UserTokenRecord(token=token, user_id=record.id))
            session.commit()
            return token

    def get_user_by_email(self, email: str) -> User | None:
        with self.session_factory() as session:
            record = self._get_user_record_by_email(session, email.strip().lower())
            return self._to_user(record) if record else None

    def get_user_by_token(self, token: str) -> User | None:
        with self.session_factory() as session:
            token_record = session.get(UserTokenRecord, token)
            if not token_record:
                return None
            user_record = session.get(UserRecord, token_record.user_id)
            return self._to_user(user_record) if user_record else None

    def get_quota(self, user_id: str) -> UserQuota:
        with self.session_factory() as session:
            quota = self._get_or_create_quota(session, user_id)
            self._reset_quota_if_needed(quota)
            session.commit()
            return self._to_quota(quota)

    def consume_quota(self, user_id: str) -> UserQuota:
        with self.session_factory() as session:
            quota = self._get_or_create_quota(session, user_id)
            self._reset_quota_if_needed(quota)
            if quota.used_today >= quota.daily_limit:
                raise ValueError("Daily quota exhausted")
            quota.used_today += 1
            session.commit()
            return self._to_quota(quota)

    def set_user_controls(
        self,
        user_id: str,
        *,
        is_active: bool | None = None,
        daily_limit: int | None = None,
    ) -> User:
        with self.session_factory() as session:
            user = session.get(UserRecord, user_id)
            if not user:
                raise KeyError(user_id)
            if is_active is not None:
                user.is_active = is_active
            if daily_limit is not None:
                quota = self._get_or_create_quota(session, user_id)
                quota.daily_limit = daily_limit
            session.commit()
            return self._to_user(user)

    def create_job(
        self,
        user_id: str,
        ticker: str,
        trade_date: str,
        mode: str,
        selected_analysts: list[str] | None = None,
    ) -> AnalysisJob:
        with self.session_factory() as session:
            record = AnalysisJobRecord(
                id=str(uuid4()),
                user_id=user_id,
                ticker=ticker.strip().upper(),
                trade_date=trade_date,
                mode=mode,
                selected_analysts=selected_analysts or ["market"],
            )
            session.add(record)
            session.commit()
            return self._to_job(record)

    def complete_job(
        self,
        job_id: str,
        normalized: dict[str, Any],
        raw_state: dict[str, Any],
    ) -> AnalysisJob:
        with self.session_factory() as session:
            job = session.get(AnalysisJobRecord, job_id)
            if not job:
                raise KeyError(job_id)
            result = AnalysisResultRecord(
                id=str(uuid4()),
                job_id=job_id,
                normalized=normalized,
                raw_state=raw_state,
            )
            session.add(result)
            job.status = "completed"
            job.result_id = result.id
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._to_job(job)

    def mark_job_running(self, job_id: str) -> AnalysisJob:
        with self.session_factory() as session:
            job = session.get(AnalysisJobRecord, job_id)
            if not job:
                raise KeyError(job_id)
            job.status = "running"
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._to_job(job)

    def fail_job(self, job_id: str, error: str) -> AnalysisJob:
        with self.session_factory() as session:
            job = session.get(AnalysisJobRecord, job_id)
            if not job:
                raise KeyError(job_id)
            job.status = "failed"
            job.error = error
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._to_job(job)

    def get_job(self, job_id: str) -> AnalysisJob | None:
        with self.session_factory() as session:
            record = session.get(AnalysisJobRecord, job_id)
            return self._to_job(record) if record else None

    def get_result(self, result_id: str | None) -> AnalysisResult | None:
        if not result_id:
            return None
        with self.session_factory() as session:
            record = session.get(AnalysisResultRecord, result_id)
            return self._to_result(record) if record else None

    def list_jobs_for_user(self, user: User) -> list[AnalysisJob]:
        with self.session_factory() as session:
            statement = select(AnalysisJobRecord)
            if user.role != "admin":
                statement = statement.where(AnalysisJobRecord.user_id == user.id)
            statement = statement.order_by(AnalysisJobRecord.created_at.desc())
            return [self._to_job(record) for record in session.scalars(statement)]

    def list_users(self) -> list[User]:
        with self.session_factory() as session:
            records = session.scalars(select(UserRecord).order_by(UserRecord.created_at.asc()))
            return [self._to_user(record) for record in records]

    def log_api_usage(
        self,
        *,
        user_id: str | None,
        endpoint: str,
        provider: str | None = None,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        estimated_cost_usd: float | None = None,
    ) -> ApiUsageLog:
        with self.session_factory() as session:
            record = ApiUsageLogRecord(
                id=str(uuid4()),
                user_id=user_id,
                endpoint=endpoint,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=estimated_cost_usd,
            )
            session.add(record)
            session.commit()
            return self._to_usage_log(record)

    def list_usage_logs(self) -> list[ApiUsageLog]:
        with self.session_factory() as session:
            records = session.scalars(select(ApiUsageLogRecord).order_by(ApiUsageLogRecord.created_at.asc()))
            return [self._to_usage_log(record) for record in records]

    @staticmethod
    def _get_user_record_by_email(session: Session, email: str) -> UserRecord | None:
        return session.scalar(select(UserRecord).where(UserRecord.email == email))

    @staticmethod
    def _get_or_create_quota(session: Session, user_id: str) -> UserQuotaRecord:
        quota = session.get(UserQuotaRecord, user_id)
        if quota:
            return quota
        quota = UserQuotaRecord(user_id=user_id)
        session.add(quota)
        session.flush()
        return quota

    @staticmethod
    def _reset_quota_if_needed(quota: UserQuotaRecord) -> None:
        today = date.today()
        if quota.usage_date != today:
            quota.used_today = 0
            quota.usage_date = today

    @staticmethod
    def _to_user(record: UserRecord) -> User:
        return User(
            id=record.id,
            email=record.email,
            password_hash=record.password_hash,
            display_name=record.display_name,
            role=record.role,
            is_active=record.is_active,
            created_at=record.created_at,
        )

    @staticmethod
    def _to_quota(record: UserQuotaRecord) -> UserQuota:
        return UserQuota(
            user_id=record.user_id,
            daily_limit=record.daily_limit,
            used_today=record.used_today,
            usage_date=record.usage_date,
        )

    @staticmethod
    def _to_job(record: AnalysisJobRecord) -> AnalysisJob:
        return AnalysisJob(
            id=record.id,
            user_id=record.user_id,
            ticker=record.ticker,
            trade_date=record.trade_date,
            mode=record.mode,
            status=record.status,
            selected_analysts=list(record.selected_analysts or []),
            result_id=record.result_id,
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_result(record: AnalysisResultRecord) -> AnalysisResult:
        return AnalysisResult(
            id=record.id,
            job_id=record.job_id,
            normalized=record.normalized,
            raw_state=record.raw_state,
            created_at=record.created_at,
        )

    @staticmethod
    def _to_usage_log(record: ApiUsageLogRecord) -> ApiUsageLog:
        return ApiUsageLog(
            id=record.id,
            user_id=record.user_id,
            endpoint=record.endpoint,
            provider=record.provider,
            model=record.model,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            estimated_cost_usd=float(record.estimated_cost_usd) if record.estimated_cost_usd is not None else None,
            created_at=record.created_at,
        )
