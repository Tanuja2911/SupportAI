from pydantic import BaseModel, model_validator
from uuid import UUID
from datetime import datetime


class BusinessCreate(BaseModel):
    name: str
    description: str | None = None
    website: str | None = None


class BusinessUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    website: str | None = None


class LLMSettingsUpdate(BaseModel):
    llm_provider: str = "gemini"
    llm_api_key: str | None = None


class LLMSettingsResponse(BaseModel):
    llm_provider: str | None
    has_api_key: bool
    is_using_platform_default: bool = False

    class Config:
        from_attributes = True


class LLMTestConnectionRequest(BaseModel):
    provider: str = "gemini"  # "gemini" | "openai"
    api_key: str | None = None  # candidate key, or None to test active saved/platform key
    business_id: str | None = None


class LLMTestConnectionResponse(BaseModel):
    status: str  # "connected" | "error"
    provider: str  # "gemini" | "openai"
    model: str | None = None
    latency_ms: int | None = None
    message: str
    error_code: str | None = None
    diagnostic: str | None = None
    action_hint: str | None = None
    is_platform_default: bool = False


class BusinessResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    website: str | None
    api_key: str
    public_key: str
    llm_provider: str | None
    has_llm_key: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def compute_has_llm_key(cls, data):
        if hasattr(data, "llm_api_key"):
            data = {c.name: getattr(data, c.name) for c in data.__table__.columns}
            data["has_llm_key"] = bool(data.get("llm_api_key"))
        elif isinstance(data, dict):
            data["has_llm_key"] = bool(data.get("llm_api_key"))
        return data


class TeamMemberAdd(BaseModel):
    email: str
    role: str = "viewer"


class TeamMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: str
    created_at: datetime
