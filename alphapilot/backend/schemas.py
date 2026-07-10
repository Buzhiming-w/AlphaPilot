from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QuotaResponse(BaseModel):
    daily_limit: int
    used_today: int


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    is_active: bool
    quota: QuotaResponse


class AnalysisCreateRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    trade_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    mode: Literal["demo", "live"] = "demo"
    selected_analysts: list[str] = Field(default_factory=lambda: ["market"])


class AnalysisJobResponse(BaseModel):
    id: str
    ticker: str
    trade_date: str
    mode: str
    status: str
    selected_analysts: list[str]
    result_id: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class AnalysisDetailResponse(BaseModel):
    job: AnalysisJobResponse
    result: dict[str, Any] | None


class AnalysisProgressEventResponse(BaseModel):
    id: str
    job_id: str
    stage_key: str
    stage_label: str
    status: str
    summary: str | None
    created_at: datetime


class AdminUserPatch(BaseModel):
    is_active: bool | None = None
    daily_limit: int | None = Field(default=None, ge=0, le=100)


class CopilotRouteRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class RoutedSymbolResponse(BaseModel):
    ticker: str
    company_name: str
    market: str
    exchange: str
    currency: str
    confidence: str | None = None
    match_reason: str | None = None


class RoutedCandidateGroupResponse(BaseModel):
    query: str
    candidates: list[RoutedSymbolResponse]


class CopilotRouteResponse(BaseModel):
    intent: str
    symbols: list[RoutedSymbolResponse]
    candidate_groups: list[RoutedCandidateGroupResponse] = []
    unresolved_entities: list[str] = []
    start_date: str | None
    end_date: str | None
    analysis_anchor: str | None
    requires_confirmation: bool
    message: str


class WatchlistCreateRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)
    company_name: str = Field(min_length=1, max_length=255)
    market: str = Field(min_length=1, max_length=32)
    exchange: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=1, max_length=16)
    note: str | None = Field(default=None, max_length=1000)
    source: str = Field(default="manual", max_length=32)


class WatchlistItemResponse(BaseModel):
    id: str
    ticker: str
    company_name: str
    market: str
    exchange: str
    currency: str
    note: str | None
    source: str
    last_analysis_job_id: str | None
    created_at: datetime
    updated_at: datetime


class CompareSymbolRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=32)
    company_name: str = Field(min_length=1, max_length=255)
    market: str = Field(min_length=1, max_length=32)
    exchange: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=1, max_length=16)


class CompareCreateRequest(BaseModel):
    symbols: list[CompareSymbolRequest] = Field(min_length=2, max_length=5)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    analysis_anchor: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    source: str = Field(default="manual", max_length=32)


class CompareSymbolResponse(BaseModel):
    id: str
    ticker: str
    company_name: str
    market: str
    exchange: str
    currency: str
    analysis_job_id: str | None
    order_index: int


class CompareWorkflowResponse(BaseModel):
    id: str
    symbols: list[CompareSymbolResponse]
    start_date: str | None
    end_date: str | None
    analysis_anchor: str | None
    source: str
    status: str
    created_at: datetime
    updated_at: datetime
