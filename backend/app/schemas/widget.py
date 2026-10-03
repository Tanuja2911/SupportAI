import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WidgetConfigUpdate(BaseModel):
    bot_name: str | None = None
    welcome_message: str | None = None
    primary_color: str | None = None
    position: str | None = None
    show_branding: bool | None = None
    auto_open_delay: str | None = None
    placeholder_text: str | None = None
    allowed_domains: list[str] | None = None
    allow_localhost: bool | None = None

    @field_validator("primary_color")
    @classmethod
    def validate_primary_color(cls, value):
        if value is not None:
            value = value.strip()
            if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", value):
                raise ValueError("Primary color must be a valid hex color (for example, #6366f1).")
        return value


class WidgetConfigResponse(BaseModel):
    id: UUID
    bot_name: str
    welcome_message: str
    primary_color: str
    position: str
    show_branding: bool
    placeholder_text: str
    auto_open_delay: str | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    allow_localhost: bool = True

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def coerce_allowed_domains(cls, v):
        return v if v is not None else []

    @field_validator("allow_localhost", mode="before")
    @classmethod
    def coerce_allow_localhost(cls, v):
        return v if v is not None else True

    class Config:
        from_attributes = True
