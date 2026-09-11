from pydantic import BaseModel
from uuid import UUID


class WidgetConfigUpdate(BaseModel):
    bot_name: str | None = None
    welcome_message: str | None = None
    primary_color: str | None = None
    position: str | None = None
    show_branding: bool | None = None
    auto_open_delay: str | None = None
    placeholder_text: str | None = None


class WidgetConfigResponse(BaseModel):
    id: UUID
    bot_name: str
    welcome_message: str
    primary_color: str
    position: str
    show_branding: bool
    placeholder_text: str

    class Config:
        from_attributes = True
