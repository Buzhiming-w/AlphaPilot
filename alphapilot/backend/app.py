from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .engine_service import AnalysisEngineService
from .queue import AnalysisQueue, InlineAnalysisQueue, RedisAnalysisQueue
from .rate_limit import InMemoryRateLimiter, RateLimiter, RedisRateLimiter
from .schemas import (
    AdminUserPatch,
    AnalysisCreateRequest,
    AnalysisDetailResponse,
    AnalysisJobResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
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
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is disabled")
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
