from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None
    customer_name: str | None = None
    customer_email: str | None = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: str
    confidence_score: float
    sources: list[dict] = []
    is_escalated: bool = False


class ConversationResponse(BaseModel):
    id: UUID
    customer_name: str | None
    customer_email: str | None
    status: str
    satisfaction_rating: float | None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: UUID
    sender: str
    content: str
    confidence_score: float | None
    sources_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class EscalationAction(BaseModel):
    action: str
    agent_response: str | None = None


class FAQCreate(BaseModel):
    question: str
    answer: str


class FAQResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
