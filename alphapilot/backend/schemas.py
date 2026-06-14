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


class AdminUserPatch(BaseModel):
    is_active: bool | None = None
    daily_limit: int | None = Field(default=None, ge=0, le=100)
