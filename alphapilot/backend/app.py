from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .engine_service import AnalysisEngineService
from .queue import AnalysisQueue, InlineAnalysisQueue, RedisAnalysisQueue
from .rate_limit import InMemoryRateLimiter, RateLimiter, RedisRateLimiter
from .schemas import (
    AdminUserPatch,
    AnalysisCreateRequest,
    AnalysisDetailResponse,
    AnalysisJobResponse,
    CompareCreateRequest,
    CompareWorkflowResponse,
    CopilotRouteRequest,
    CopilotRouteResponse,
    LoginRequest,
    RegisterRequest,
    RoutedSymbolResponse,
    TokenResponse,
    UserResponse,
    WatchlistCreateRequest,
    WatchlistItemResponse,
)
from .settings import (
    get_database_url,
    get_queue_backend,
    get_rate_limit,
    get_rate_limit_window_seconds,
    get_redis_url,
    is_rate_limit_enabled,
)
from .store import AlphaPilotStore, AnalysisJob, User, UserQuota
from .sqlalchemy_store import SqlAlchemyAlphaPilotStore
from .workflow_router import WorkflowDraft, WorkflowRouter


Store = AlphaPilotStore | SqlAlchemyAlphaPilotStore


def _create_queue() -> AnalysisQueue:
    if get_queue_backend() == "redis":
        return RedisAnalysisQueue(get_redis_url())
    return InlineAnalysisQueue()


def _create_rate_limiter() -> RateLimiter | None:
    if not is_rate_limit_enabled():
        return None
    if get_queue_backend() == "redis":
        return RedisRateLimiter(
            get_redis_url(),
            limit=get_rate_limit(),
            window_seconds=get_rate_limit_window_seconds(),
        )
    return InMemoryRateLimiter(
        limit=get_rate_limit(),
        window_seconds=get_rate_limit_window_seconds(),
    )


def _quota_payload(quota: UserQuota) -> dict[str, int]:
    return {"daily_limit": quota.daily_limit, "used_today": quota.used_today}


def _user_payload(store: Store, user: User) -> UserResponse:
    quota = store.get_quota(user.id)
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        quota=_quota_payload(quota),
    )


def _job_payload(job: AnalysisJob) -> AnalysisJobResponse:
    return AnalysisJobResponse(
        id=job.id,
        ticker=job.ticker,
        trade_date=job.trade_date,
        mode=job.mode,
        status=job.status,
        selected_analysts=job.selected_analysts,
        result_id=job.result_id,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _routed_symbol_payload(symbol) -> RoutedSymbolResponse:
    return RoutedSymbolResponse(
        ticker=symbol.ticker,
        company_name=symbol.company_name,
        market=symbol.market,
        exchange=symbol.exchange,
        currency=symbol.currency,
        confidence=getattr(symbol, "confidence", None),
        match_reason=getattr(symbol, "match_reason", None),
    )


def _copilot_payload(draft: WorkflowDraft) -> CopilotRouteResponse:
    return CopilotRouteResponse(
        intent=draft.intent,
        symbols=[_routed_symbol_payload(symbol) for symbol in draft.symbols],
        start_date=draft.start_date,
        end_date=draft.end_date,
        analysis_anchor=draft.analysis_anchor,
        requires_confirmation=draft.requires_confirmation,
        message=draft.message,
    )


def _watchlist_payload(item) -> WatchlistItemResponse:
    return WatchlistItemResponse(
        id=item.id,
        ticker=item.ticker,
        company_name=item.company_name,
        market=item.market,
        exchange=item.exchange,
        currency=item.currency,
        note=item.note,
        source=item.source,
        last_analysis_job_id=item.last_analysis_job_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _compare_payload(workflow) -> CompareWorkflowResponse:
    return CompareWorkflowResponse(
        id=workflow.id,
        symbols=[
            {
                "id": symbol.id,
                "ticker": symbol.ticker,
                "company_name": symbol.company_name,
                "market": symbol.market,
                "exchange": symbol.exchange,
                "currency": symbol.currency,
                "analysis_job_id": symbol.analysis_job_id,
                "order_index": symbol.order_index,
            }
            for symbol in workflow.symbols
        ],
        start_date=workflow.start_date,
        end_date=workflow.end_date,
        analysis_anchor=workflow.analysis_anchor,
        source=workflow.source,
        status=workflow.status,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def create_app(
    *,
    store: Store | None = None,
    database_url: str | None = None,
    engine: AnalysisEngineService | None = None,
    queue: AnalysisQueue | None = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    app = FastAPI(title="AlphaPilot API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    resolved_database_url = database_url or get_database_url()
    app.state.store = store or (
        SqlAlchemyAlphaPilotStore(resolved_database_url)
        if resolved_database_url
        else AlphaPilotStore()
    )
    app.state.engine = engine or AnalysisEngineService()
    app.state.queue = queue or _create_queue()
    app.state.rate_limiter = rate_limiter if rate_limiter is not None else _create_rate_limiter()
    app.state.workflow_router = WorkflowRouter()

    def enforce_rate_limit(request: Request, bucket: str) -> None:
        limiter = app.state.rate_limiter
        if not limiter:
            return
        client_host = request.client.host if request.client else "unknown"
        if not limiter.allow(f"{bucket}:{client_host}"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

    def current_user(authorization: str | None = Header(default=None)) -> User:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        token = authorization.removeprefix("Bearer ").strip()
        user = app.state.store.get_user_by_token(token)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user

    def admin_user(user: User = Depends(current_user)) -> User:
        if user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
        return user

    def ensure_active_user(user: User) -> None:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is disabled")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/demo/reference")
    def demo_reference(request: Request) -> dict:
        enforce_rate_limit(request, "demo")
        normalized, _ = app.state.engine.run_demo()
        return normalized

    @app.post("/auth/register", response_model=UserResponse, status_code=201)
    def register(payload: RegisterRequest, request: Request) -> UserResponse:
        enforce_rate_limit(request, "auth")
        try:
            user = app.state.store.create_user(
                email=str(payload.email),
                password=payload.password,
                display_name=payload.display_name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _user_payload(app.state.store, user)

    @app.post("/auth/login", response_model=TokenResponse)
    def login(payload: LoginRequest, request: Request) -> TokenResponse:
        enforce_rate_limit(request, "auth")
        token = app.state.store.authenticate(str(payload.email), payload.password)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return TokenResponse(access_token=token)

    @app.get("/me", response_model=UserResponse)
    def me(user: User = Depends(current_user)) -> UserResponse:
        return _user_payload(app.state.store, user)

    @app.post("/analysis", response_model=AnalysisJobResponse, status_code=201)
    def create_analysis(
        payload: AnalysisCreateRequest,
        request: Request,
        user: User = Depends(current_user),
    ) -> AnalysisJobResponse:
        enforce_rate_limit(request, "analysis")
        ensure_active_user(user)
        try:
            app.state.store.consume_quota(user.id)
        except ValueError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc

        job = app.state.store.create_job(
            user_id=user.id,
            ticker=payload.ticker,
            trade_date=payload.trade_date,
            mode=payload.mode,
            selected_analysts=payload.selected_analysts,
        )
        if payload.mode == "live":
            app.state.queue.enqueue(job.id)
            return _job_payload(job)
        try:
            normalized, raw_state = app.state.engine.run_demo()
            job = app.state.store.complete_job(job.id, normalized, raw_state)
        except Exception as exc:  # pragma: no cover - exercised by integration tests later
            job = app.state.store.fail_job(job.id, str(exc))
        return _job_payload(job)

    @app.get("/analysis", response_model=list[AnalysisJobResponse])
    def list_analysis(user: User = Depends(current_user)) -> list[AnalysisJobResponse]:
        return [_job_payload(job) for job in app.state.store.list_jobs_for_user(user)]

    @app.get("/analysis/{job_id}", response_model=AnalysisDetailResponse)
    def analysis_detail(
        job_id: str,
        user: User = Depends(current_user),
    ) -> AnalysisDetailResponse:
        job = app.state.store.get_job(job_id)
        if not job or (user.role != "admin" and job.user_id != user.id):
            raise HTTPException(status_code=404, detail="Analysis job not found")
        result = app.state.store.get_result(job.result_id)
        return AnalysisDetailResponse(
            job=_job_payload(job),
            result=result.normalized if result else None,
        )

    @app.post("/copilot/route", response_model=CopilotRouteResponse)
    def copilot_route(
        payload: CopilotRouteRequest,
        request: Request,
        _: User = Depends(current_user),
    ) -> CopilotRouteResponse:
        enforce_rate_limit(request, "copilot")
        draft = app.state.workflow_router.route(payload.message)
        return _copilot_payload(draft)

    @app.get("/watchlist", response_model=list[WatchlistItemResponse])
    def list_watchlist(user: User = Depends(current_user)) -> list[WatchlistItemResponse]:
        return [_watchlist_payload(item) for item in app.state.store.list_watchlist_items(user.id)]

    @app.post("/watchlist", response_model=WatchlistItemResponse, status_code=201)
    def create_watchlist_item(
        payload: WatchlistCreateRequest,
        user: User = Depends(current_user),
    ) -> WatchlistItemResponse:
        ensure_active_user(user)
        item = app.state.store.create_watchlist_item(
            user_id=user.id,
            ticker=payload.ticker,
            company_name=payload.company_name,
            market=payload.market,
            exchange=payload.exchange,
            currency=payload.currency,
            note=payload.note,
            source=payload.source,
        )
        return _watchlist_payload(item)

    @app.delete("/watchlist/{item_id}", status_code=204)
    def delete_watchlist_item(
        item_id: str,
        user: User = Depends(current_user),
    ) -> Response:
        try:
            app.state.store.delete_watchlist_item(user.id, item_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Watchlist item not found") from exc
        return Response(status_code=204)

    @app.post("/compare", response_model=CompareWorkflowResponse, status_code=201)
    def create_compare(
        payload: CompareCreateRequest,
        user: User = Depends(current_user),
    ) -> CompareWorkflowResponse:
        ensure_active_user(user)
        workflow = app.state.store.create_compare_workflow(
            user_id=user.id,
            symbols=[symbol.model_dump() for symbol in payload.symbols],
            start_date=payload.start_date,
            end_date=payload.end_date,
            analysis_anchor=payload.analysis_anchor or payload.end_date,
            source=payload.source,
        )
        return _compare_payload(workflow)

    @app.get("/compare/{compare_id}", response_model=CompareWorkflowResponse)
    def get_compare(
        compare_id: str,
        user: User = Depends(current_user),
    ) -> CompareWorkflowResponse:
        workflow = app.state.store.get_compare_workflow(user.id, compare_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Compare workflow not found")
        return _compare_payload(workflow)

    @app.get("/admin/users", response_model=list[UserResponse])
    def list_users(_: User = Depends(admin_user)) -> list[UserResponse]:
        return [_user_payload(app.state.store, user) for user in app.state.store.list_users()]

    @app.patch("/admin/users/{user_id}", response_model=UserResponse)
    def patch_user(
        user_id: str,
        payload: AdminUserPatch,
        _: User = Depends(admin_user),
    ) -> UserResponse:
        try:
            user = app.state.store.set_user_controls(
                user_id,
                is_active=payload.is_active,
                daily_limit=payload.daily_limit,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="User not found") from exc
        return _user_payload(app.state.store, user)

    return app


app = create_app()
