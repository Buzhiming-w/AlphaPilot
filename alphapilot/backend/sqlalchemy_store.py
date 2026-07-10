from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .db_models import (
    AnalysisJobRecord,
    AnalysisProgressEventRecord,
    AnalysisResultRecord,
    ApiUsageLogRecord,
    Base,
    CompareWorkflowRecord,
    CompareWorkflowSymbolRecord,
    SecurityAliasRecord,
    SecurityMasterSyncRunRecord,
    SecurityRecord,
    UserQuotaRecord,
    UserRecord,
    UserTokenRecord,
    WatchlistItemRecord,
)
from .security import hash_password, new_token, verify_password
from .settings import get_admin_email, get_admin_password, is_admin_password_configured
from .store import (
    AnalysisJob,
    AnalysisProgressEvent,
    AnalysisResult,
    ApiUsageLog,
    CompareWorkflow,
    CompareWorkflowSymbol,
    Security,
    SecurityAlias,
    SecurityMasterSyncRun,
    User,
    UserQuota,
    WatchlistItem,
    normalize_security_text,
)


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
        admin_email = get_admin_email()
        admin_password = get_admin_password()
        with self.session_factory() as session:
            existing = self._get_user_record_by_email(session, admin_email)
            if existing:
                if is_admin_password_configured() and not verify_password(
                    admin_password, existing.password_hash
                ):
                    existing.password_hash = hash_password(admin_password)
                    session.commit()
                return
            user = UserRecord(
                id=str(uuid4()),
                email=admin_email,
                password_hash=hash_password(admin_password),
                display_name="AlphaPilot Admin",
                role="admin",
            )
            session.add(user)
            session.flush()
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
            session.flush()
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

    def create_analysis_progress_event(
        self,
        *,
        job_id: str,
        stage_key: str,
        stage_label: str,
        status: str,
        summary: str | None = None,
    ) -> AnalysisProgressEvent:
        with self.session_factory() as session:
            record = AnalysisProgressEventRecord(
                id=str(uuid4()),
                job_id=job_id,
                stage_key=stage_key,
                stage_label=stage_label,
                status=status,
                summary=summary,
            )
            session.add(record)
            session.commit()
            return self._to_progress_event(record)

    def list_analysis_progress_events(self, job_id: str) -> list[AnalysisProgressEvent]:
        with self.session_factory() as session:
            records = session.scalars(
                select(AnalysisProgressEventRecord)
                .where(AnalysisProgressEventRecord.job_id == job_id)
                .order_by(AnalysisProgressEventRecord.created_at.asc())
            )
            return [self._to_progress_event(record) for record in records]

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

    def update_result_normalized(self, result_id: str, normalized: dict[str, Any]) -> AnalysisResult:
        with self.session_factory() as session:
            record = session.get(AnalysisResultRecord, result_id)
            if not record:
                raise KeyError(result_id)
            record.normalized = normalized
            session.commit()
            return self._to_result(record)

    def delete_analysis_job(self, user_id: str, job_id: str) -> bool:
        with self.session_factory() as session:
            job = session.scalar(
                select(AnalysisJobRecord).where(
                    AnalysisJobRecord.id == job_id,
                    AnalysisJobRecord.user_id == user_id,
                )
            )
            if not job:
                raise KeyError(job_id)
            for event in session.scalars(
                select(AnalysisProgressEventRecord).where(AnalysisProgressEventRecord.job_id == job_id)
            ):
                session.delete(event)
            for result in session.scalars(
                select(AnalysisResultRecord).where(AnalysisResultRecord.job_id == job_id)
            ):
                session.delete(result)
            session.delete(job)
            session.commit()
            return True

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

    def create_watchlist_item(
        self,
        *,
        user_id: str,
        ticker: str,
        company_name: str,
        market: str,
        exchange: str,
        currency: str,
        note: str | None = None,
        source: str = "manual",
        last_analysis_job_id: str | None = None,
    ) -> WatchlistItem:
        with self.session_factory() as session:
            record = WatchlistItemRecord(
                id=str(uuid4()),
                user_id=user_id,
                ticker=ticker.strip().upper(),
                company_name=company_name,
                market=market,
                exchange=exchange,
                currency=currency,
                note=note,
                source=source,
                last_analysis_job_id=last_analysis_job_id,
            )
            session.add(record)
            session.commit()
            return self._to_watchlist_item(record)

    def list_watchlist_items(self, user_id: str) -> list[WatchlistItem]:
        with self.session_factory() as session:
            records = session.scalars(
                select(WatchlistItemRecord)
                .where(WatchlistItemRecord.user_id == user_id)
                .order_by(WatchlistItemRecord.created_at.desc())
            )
            return [self._to_watchlist_item(record) for record in records]

    def delete_watchlist_item(self, user_id: str, item_id: str) -> bool:
        with self.session_factory() as session:
            record = session.scalar(
                select(WatchlistItemRecord).where(
                    WatchlistItemRecord.id == item_id,
                    WatchlistItemRecord.user_id == user_id,
                )
            )
            if not record:
                raise KeyError(item_id)
            session.delete(record)
            session.commit()
            return True

    def create_compare_workflow(
        self,
        *,
        user_id: str,
        symbols: list[dict[str, str]],
        start_date: str | None,
        end_date: str | None,
        analysis_anchor: str | None,
        source: str = "manual",
        status: str = "draft",
    ) -> CompareWorkflow:
        with self.session_factory() as session:
            workflow = CompareWorkflowRecord(
                id=str(uuid4()),
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                analysis_anchor=analysis_anchor,
                source=source,
                status=status,
            )
            session.add(workflow)
            session.flush()
            symbol_records = [
                CompareWorkflowSymbolRecord(
                    id=str(uuid4()),
                    compare_workflow_id=workflow.id,
                    ticker=symbol["ticker"].strip().upper(),
                    company_name=symbol["company_name"],
                    market=symbol["market"],
                    exchange=symbol["exchange"],
                    currency=symbol["currency"],
                    order_index=index,
                )
                for index, symbol in enumerate(symbols)
            ]
            session.add_all(symbol_records)
            session.commit()
            return self._to_compare_workflow(workflow, symbol_records)

    def get_compare_workflow(self, user_id: str, workflow_id: str) -> CompareWorkflow | None:
        with self.session_factory() as session:
            workflow = session.scalar(
                select(CompareWorkflowRecord).where(
                    CompareWorkflowRecord.id == workflow_id,
                    CompareWorkflowRecord.user_id == user_id,
                )
            )
            if not workflow:
                return None
            symbols = list(
                session.scalars(
                    select(CompareWorkflowSymbolRecord)
                    .where(CompareWorkflowSymbolRecord.compare_workflow_id == workflow.id)
                    .order_by(CompareWorkflowSymbolRecord.order_index.asc())
                )
            )
            return self._to_compare_workflow(workflow, symbols)

    def list_compare_workflows(self, user_id: str) -> list[CompareWorkflow]:
        with self.session_factory() as session:
            workflows = list(
                session.scalars(
                    select(CompareWorkflowRecord)
                    .where(CompareWorkflowRecord.user_id == user_id)
                    .order_by(CompareWorkflowRecord.created_at.desc())
                )
            )
            results: list[CompareWorkflow] = []
            for workflow in workflows:
                symbols = list(
                    session.scalars(
                        select(CompareWorkflowSymbolRecord)
                        .where(CompareWorkflowSymbolRecord.compare_workflow_id == workflow.id)
                        .order_by(CompareWorkflowSymbolRecord.order_index.asc())
                    )
                )
                results.append(self._to_compare_workflow(workflow, symbols))
            return results

    def delete_compare_workflow(self, user_id: str, workflow_id: str) -> bool:
        with self.session_factory() as session:
            workflow = session.scalar(
                select(CompareWorkflowRecord).where(
                    CompareWorkflowRecord.id == workflow_id,
                    CompareWorkflowRecord.user_id == user_id,
                )
            )
            if not workflow:
                raise KeyError(workflow_id)
            session.execute(
                delete(CompareWorkflowSymbolRecord).where(
                    CompareWorkflowSymbolRecord.compare_workflow_id == workflow_id
                )
            )
            session.delete(workflow)
            session.commit()
            return True

    def upsert_security(
        self,
        *,
        symbol: str,
        name: str,
        exchange: str,
        market: str = "US",
        currency: str = "USD",
        asset_type: str = "stock",
        is_etf: bool = False,
        cik: str | None = None,
        status: str = "active",
        source: str = "manual",
        raw_payload: dict[str, Any] | None = None,
    ) -> tuple[Security, bool]:
        normalized_symbol = normalize_security_text(symbol)
        canonical_symbol = symbol.strip().upper()
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            record = session.scalar(
                select(SecurityRecord).where(
                    SecurityRecord.market == market,
                    SecurityRecord.symbol == canonical_symbol,
                )
            )
            created = record is None
            if record is None:
                record = SecurityRecord(
                    id=str(uuid4()),
                    symbol=canonical_symbol,
                    normalized_symbol=normalized_symbol,
                    name=name,
                    normalized_name=normalize_security_text(name),
                    exchange=exchange,
                    market=market,
                    currency=currency,
                    asset_type=asset_type,
                    is_etf=is_etf,
                    cik=cik,
                    status=status,
                    source=source,
                    raw_payload=raw_payload or {},
                    first_seen_at=now,
                    last_seen_at=now,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
            else:
                record.name = name
                record.normalized_name = normalize_security_text(name)
                record.exchange = exchange
                record.currency = currency
                record.asset_type = asset_type
                record.is_etf = is_etf
                record.cik = cik or record.cik
                record.status = status
                record.source = source
                record.raw_payload = raw_payload or {}
                record.last_seen_at = now
                record.updated_at = now
            session.commit()
            return self._to_security(record), created

    def add_security_alias(
        self,
        *,
        security_id: str,
        alias: str,
        alias_type: str = "manual",
        confidence: str = "high",
        source: str = "manual",
    ) -> SecurityAlias:
        normalized_alias = normalize_security_text(alias)
        with self.session_factory() as session:
            record = session.scalar(
                select(SecurityAliasRecord).where(
                    SecurityAliasRecord.security_id == security_id,
                    SecurityAliasRecord.normalized_alias == normalized_alias,
                )
            )
            if record is None:
                record = SecurityAliasRecord(
                    id=str(uuid4()),
                    security_id=security_id,
                    alias=alias,
                    normalized_alias=normalized_alias,
                    alias_type=alias_type,
                    confidence=confidence,
                    source=source,
                )
                session.add(record)
            else:
                record.alias = alias
                record.alias_type = alias_type
                record.confidence = confidence
                record.source = source
                record.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._to_security_alias(record)

    def search_security_master(self, query: str, limit: int = 5) -> list[tuple[Security, str, str]]:
        from .store import AlphaPilotStore

        normalized_query = normalize_security_text(query)
        if not normalized_query:
            return []
        with self.session_factory() as session:
            securities = list(
                session.scalars(select(SecurityRecord).where(SecurityRecord.status == "active"))
            )
            aliases = list(session.scalars(select(SecurityAliasRecord)))
        aliases_by_security: dict[str, list[SecurityAliasRecord]] = {}
        for alias in aliases:
            aliases_by_security.setdefault(alias.security_id, []).append(alias)
        scored: list[tuple[int, SecurityRecord, str, str]] = []
        for security in securities:
            terms = [
                (security.normalized_symbol, "Exact ticker match", "high"),
                (security.normalized_name, "Exact company name match", "high"),
            ]
            terms.extend(
                (
                    alias.normalized_alias,
                    f"{alias.alias_type.replace('_', ' ').title()} match",
                    alias.confidence,
                )
                for alias in aliases_by_security.get(security.id, [])
            )
            score, reason, confidence = AlphaPilotStore._score_security_terms(normalized_query, terms)
            if score > 0:
                scored.append((score, security, reason, confidence))
        scored.sort(key=lambda item: (-item[0], item[1].symbol))
        return [
            (self._to_security(security), reason, confidence)
            for _, security, reason, confidence in scored[:limit]
        ]

    def create_security_master_sync_run(
        self,
        *,
        source: str,
        status: str,
        started_at: datetime,
        finished_at: datetime | None,
        inserted_count: int = 0,
        updated_count: int = 0,
        deactivated_count: int = 0,
        error: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> SecurityMasterSyncRun:
        with self.session_factory() as session:
            record = SecurityMasterSyncRunRecord(
                id=str(uuid4()),
                source=source,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                inserted_count=inserted_count,
                updated_count=updated_count,
                deactivated_count=deactivated_count,
                error=error,
                raw_metadata=raw_metadata or {},
            )
            session.add(record)
            session.commit()
            return self._to_security_master_sync_run(record)

    def latest_security_master_sync_run(self) -> SecurityMasterSyncRun | None:
        with self.session_factory() as session:
            record = session.scalar(
                select(SecurityMasterSyncRunRecord).order_by(
                    SecurityMasterSyncRunRecord.finished_at.desc(),
                    SecurityMasterSyncRunRecord.started_at.desc(),
                )
            )
            return self._to_security_master_sync_run(record) if record else None

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
    def _to_progress_event(record: AnalysisProgressEventRecord) -> AnalysisProgressEvent:
        return AnalysisProgressEvent(
            id=record.id,
            job_id=record.job_id,
            stage_key=record.stage_key,
            stage_label=record.stage_label,
            status=record.status,
            summary=record.summary,
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

    @staticmethod
    def _to_watchlist_item(record: WatchlistItemRecord) -> WatchlistItem:
        return WatchlistItem(
            id=record.id,
            user_id=record.user_id,
            ticker=record.ticker,
            company_name=record.company_name,
            market=record.market,
            exchange=record.exchange,
            currency=record.currency,
            note=record.note,
            source=record.source,
            last_analysis_job_id=record.last_analysis_job_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_compare_workflow(
        record: CompareWorkflowRecord,
        symbols: list[CompareWorkflowSymbolRecord],
    ) -> CompareWorkflow:
        return CompareWorkflow(
            id=record.id,
            user_id=record.user_id,
            symbols=[SqlAlchemyAlphaPilotStore._to_compare_symbol(symbol) for symbol in symbols],
            start_date=record.start_date,
            end_date=record.end_date,
            analysis_anchor=record.analysis_anchor,
            source=record.source,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_compare_symbol(record: CompareWorkflowSymbolRecord) -> CompareWorkflowSymbol:
        return CompareWorkflowSymbol(
            id=record.id,
            compare_workflow_id=record.compare_workflow_id,
            ticker=record.ticker,
            company_name=record.company_name,
            market=record.market,
            exchange=record.exchange,
            currency=record.currency,
            analysis_job_id=record.analysis_job_id,
            order_index=record.order_index,
        )

    @staticmethod
    def _to_security(record: SecurityRecord) -> Security:
        return Security(
            id=record.id,
            symbol=record.symbol,
            normalized_symbol=record.normalized_symbol,
            name=record.name,
            normalized_name=record.normalized_name,
            exchange=record.exchange,
            market=record.market,
            currency=record.currency,
            asset_type=record.asset_type,
            is_etf=record.is_etf,
            cik=record.cik,
            status=record.status,
            source=record.source,
            raw_payload=record.raw_payload,
            first_seen_at=record.first_seen_at,
            last_seen_at=record.last_seen_at,
            delisted_at=record.delisted_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_security_alias(record: SecurityAliasRecord) -> SecurityAlias:
        return SecurityAlias(
            id=record.id,
            security_id=record.security_id,
            alias=record.alias,
            normalized_alias=record.normalized_alias,
            alias_type=record.alias_type,
            confidence=record.confidence,
            source=record.source,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_security_master_sync_run(record: SecurityMasterSyncRunRecord) -> SecurityMasterSyncRun:
        return SecurityMasterSyncRun(
            id=record.id,
            source=record.source,
            started_at=record.started_at,
            finished_at=record.finished_at,
            status=record.status,
            inserted_count=record.inserted_count,
            updated_count=record.updated_count,
            deactivated_count=record.deactivated_count,
            error=record.error,
            raw_metadata=record.raw_metadata,
        )
