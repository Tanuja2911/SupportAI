from pydantic import BaseModel
from datetime import datetime


class DashboardStats(BaseModel):
    total_conversations: int
    active_conversations: int
    escalated_conversations: int
    resolved_conversations: int
    total_messages: int
    ai_messages: int
    avg_confidence: float
    total_documents: int
    ready_documents: int


class DailyStats(BaseModel):
    date: str
    conversations: int
    messages: int


class TopQuestion(BaseModel):
    question: str
    count: int
    avg_confidence: float


class ContentGap(BaseModel):
    question: str
    count: int
    last_asked: datetime
