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
    llm_provider: str
    llm_api_key: str


class LLMSettingsResponse(BaseModel):
    llm_provider: str | None
    has_api_key: bool

    class Config:
        from_attributes = True


class BusinessResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    website: str | None
    api_key: str
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
