from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from typing import Any
from uuid import uuid4

from .security import hash_password, new_token, verify_password
from .settings import get_admin_email, get_admin_password


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


@dataclass
class AnalysisProgressEvent:
    id: str
    job_id: str
    stage_key: str
    stage_label: str
    status: str
    summary: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ApiUsageLog:
    id: str
    user_id: str | None
    endpoint: str
    provider: str | None = None
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WatchlistItem:
    id: str
    user_id: str
    ticker: str
    company_name: str
    market: str
    exchange: str
    currency: str
    note: str | None = None
    source: str = "manual"
    last_analysis_job_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CompareWorkflowSymbol:
    id: str
    compare_workflow_id: str
    ticker: str
    company_name: str
    market: str
    exchange: str
    currency: str
    analysis_job_id: str | None = None
    order_index: int = 0


@dataclass
class CompareWorkflow:
    id: str
    user_id: str
    symbols: list[CompareWorkflowSymbol]
    start_date: str | None
    end_date: str | None
    analysis_anchor: str | None
    source: str = "manual"
    status: str = "draft"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Security:
    id: str
    symbol: str
    normalized_symbol: str
    name: str
    normalized_name: str
    exchange: str
    market: str = "US"
    currency: str = "USD"
    asset_type: str = "stock"
    is_etf: bool = False
    cik: str | None = None
    status: str = "active"
    source: str = "manual"
    raw_payload: dict[str, Any] = field(default_factory=dict)
    first_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delisted_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SecurityAlias:
    id: str
    security_id: str
    alias: str
    normalized_alias: str
    alias_type: str = "manual"
    confidence: str = "high"
    source: str = "manual"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SecurityMasterSyncRun:
    id: str
    source: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    inserted_count: int = 0
    updated_count: int = 0
    deactivated_count: int = 0
    error: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


def normalize_security_text(value: str) -> str:
    return " ".join(
        value.casefold()
        .replace("，", " ")
        .replace(",", " ")
        .replace(".", "")
        .replace("-", " ")
        .split()
    )


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
        self.progress_events: dict[str, list[AnalysisProgressEvent]] = {}
        self.usage_logs: list[ApiUsageLog] = []
        self.watchlist_items: dict[str, WatchlistItem] = {}
        self.compare_workflows: dict[str, CompareWorkflow] = {}
        self.securities: dict[str, Security] = {}
        self.security_by_market_symbol: dict[tuple[str, str], str] = {}
        self.security_aliases: dict[str, SecurityAlias] = {}
        self.security_sync_runs: list[SecurityMasterSyncRun] = []
        self.create_user(
            email=get_admin_email(),
            password=get_admin_password(),
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

    def create_analysis_progress_event(
        self,
        *,
        job_id: str,
        stage_key: str,
        stage_label: str,
        status: str,
        summary: str | None = None,
    ) -> AnalysisProgressEvent:
        event = AnalysisProgressEvent(
            id=str(uuid4()),
            job_id=job_id,
            stage_key=stage_key,
            stage_label=stage_label,
            status=status,
            summary=summary,
        )
        self.progress_events.setdefault(job_id, []).append(event)
        return event

    def list_analysis_progress_events(self, job_id: str) -> list[AnalysisProgressEvent]:
        return list(self.progress_events.get(job_id, []))

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

    def mark_job_running(self, job_id: str) -> AnalysisJob:
        job = self.jobs[job_id]
        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        return job

    def fail_job(self, job_id: str, error: str) -> AnalysisJob:
        job = self.jobs[job_id]
        job.status = "failed"
        job.error = error
        job.updated_at = datetime.now(timezone.utc)
        return job

    def get_job(self, job_id: str) -> AnalysisJob | None:
        return self.jobs.get(job_id)

    def get_result(self, result_id: str | None) -> AnalysisResult | None:
        return self.results.get(result_id) if result_id else None

    def update_result_normalized(self, result_id: str, normalized: dict[str, Any]) -> AnalysisResult:
        result = self.results[result_id]
        result.normalized = normalized
        return result

    def delete_analysis_job(self, user_id: str, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or job.user_id != user_id:
            raise KeyError(job_id)
        if job.result_id:
            self.results.pop(job.result_id, None)
        self.progress_events.pop(job_id, None)
        del self.jobs[job_id]
        return True

    def list_jobs_for_user(self, user: User) -> list[AnalysisJob]:
        if user.role == "admin":
            return sorted(self.jobs.values(), key=lambda job: job.created_at, reverse=True)
        return sorted(
            [job for job in self.jobs.values() if job.user_id == user.id],
            key=lambda job: job.created_at,
            reverse=True,
        )

    def list_users(self) -> list[User]:
        return list(self.users.values())

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
        log = ApiUsageLog(
            id=str(uuid4()),
            user_id=user_id,
            endpoint=endpoint,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
        self.usage_logs.append(log)
        return log

    def list_usage_logs(self) -> list[ApiUsageLog]:
        return list(self.usage_logs)

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
        item = WatchlistItem(
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
        self.watchlist_items[item.id] = item
        return item

    def list_watchlist_items(self, user_id: str) -> list[WatchlistItem]:
        return sorted(
            [item for item in self.watchlist_items.values() if item.user_id == user_id],
            key=lambda item: item.created_at,
            reverse=True,
        )

    def delete_watchlist_item(self, user_id: str, item_id: str) -> bool:
        item = self.watchlist_items.get(item_id)
        if not item or item.user_id != user_id:
            raise KeyError(item_id)
        del self.watchlist_items[item_id]
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
        workflow_id = str(uuid4())
        workflow_symbols = [
            CompareWorkflowSymbol(
                id=str(uuid4()),
                compare_workflow_id=workflow_id,
                ticker=symbol["ticker"].strip().upper(),
                company_name=symbol["company_name"],
                market=symbol["market"],
                exchange=symbol["exchange"],
                currency=symbol["currency"],
                order_index=index,
            )
            for index, symbol in enumerate(symbols)
        ]
        workflow = CompareWorkflow(
            id=workflow_id,
            user_id=user_id,
            symbols=workflow_symbols,
            start_date=start_date,
            end_date=end_date,
            analysis_anchor=analysis_anchor,
            source=source,
            status=status,
        )
        self.compare_workflows[workflow.id] = workflow
        return workflow

    def get_compare_workflow(self, user_id: str, workflow_id: str) -> CompareWorkflow | None:
        workflow = self.compare_workflows.get(workflow_id)
        if not workflow or workflow.user_id != user_id:
            return None
        return workflow

    def list_compare_workflows(self, user_id: str) -> list[CompareWorkflow]:
        return sorted(
            [workflow for workflow in self.compare_workflows.values() if workflow.user_id == user_id],
            key=lambda workflow: workflow.created_at,
            reverse=True,
        )

    def delete_compare_workflow(self, user_id: str, workflow_id: str) -> bool:
        workflow = self.compare_workflows.get(workflow_id)
        if not workflow or workflow.user_id != user_id:
            raise KeyError(workflow_id)
        del self.compare_workflows[workflow_id]
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
        key = (market, symbol.strip().upper())
        now = datetime.now(timezone.utc)
        existing_id = self.security_by_market_symbol.get(key)
        if existing_id:
            security = self.securities[existing_id]
            security.name = name
            security.normalized_name = normalize_security_text(name)
            security.exchange = exchange
            security.currency = currency
            security.asset_type = asset_type
            security.is_etf = is_etf
            security.cik = cik or security.cik
            security.status = status
            security.source = source
            security.raw_payload = raw_payload or {}
            security.last_seen_at = now
            security.updated_at = now
            return security, False
        security = Security(
            id=str(uuid4()),
            symbol=symbol.strip().upper(),
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
        self.securities[security.id] = security
        self.security_by_market_symbol[key] = security.id
        return security, True

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
        for existing in self.security_aliases.values():
            if existing.security_id == security_id and existing.normalized_alias == normalized_alias:
                existing.alias = alias
                existing.alias_type = alias_type
                existing.confidence = confidence
                existing.source = source
                existing.updated_at = datetime.now(timezone.utc)
                return existing
        record = SecurityAlias(
            id=str(uuid4()),
            security_id=security_id,
            alias=alias,
            normalized_alias=normalized_alias,
            alias_type=alias_type,
            confidence=confidence,
            source=source,
        )
        self.security_aliases[record.id] = record
        return record

    def search_security_master(self, query: str, limit: int = 5) -> list[tuple[Security, str, str]]:
        normalized_query = normalize_security_text(query)
        if not normalized_query:
            return []
        aliases_by_security: dict[str, list[SecurityAlias]] = {}
        for alias in self.security_aliases.values():
            aliases_by_security.setdefault(alias.security_id, []).append(alias)
        scored: list[tuple[int, Security, str, str]] = []
        for security in self.securities.values():
            if security.status != "active":
                continue
            terms = [
                (security.normalized_symbol, "Exact ticker match", "high"),
                (security.normalized_name, "Exact company name match", "high"),
            ]
            terms.extend(
                (alias.normalized_alias, f"{alias.alias_type.replace('_', ' ').title()} match", alias.confidence)
                for alias in aliases_by_security.get(security.id, [])
            )
            score, reason, confidence = self._score_security_terms(normalized_query, terms)
            if score > 0:
                scored.append((score, security, reason, confidence))
        scored.sort(key=lambda item: (-item[0], item[1].symbol))
        return [(security, reason, confidence) for _, security, reason, confidence in scored[:limit]]

    @staticmethod
    def _score_security_terms(
        normalized_query: str,
        terms: list[tuple[str, str, str]],
    ) -> tuple[int, str, str]:
        for term, reason, confidence in terms:
            if normalized_query == term:
                return 100 if "ticker" in reason.lower() else 92, reason, confidence
        for term, reason, confidence in terms:
            if normalized_query in term or term in normalized_query:
                return 74, reason if "match" in reason.lower() else "Partial text match", confidence or "medium"
        best = max((SequenceMatcher(None, normalized_query, term).ratio(), reason) for term, reason, _ in terms)
        if len(normalized_query) >= 4 and best[0] >= 0.82:
            return int(best[0] * 60), "Fuzzy text match", "medium"
        return 0, "", "low"

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
        run = SecurityMasterSyncRun(
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
        self.security_sync_runs.append(run)
        return run

    def latest_security_master_sync_run(self) -> SecurityMasterSyncRun | None:
        if not self.security_sync_runs:
            return None
        return sorted(
            self.security_sync_runs,
            key=lambda run: run.finished_at or run.started_at,
            reverse=True,
        )[0]
