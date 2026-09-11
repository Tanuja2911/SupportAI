import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=False)
    sample_queries = Column(Text, nullable=False)
    query_count = Column(Integer, default=1)
    avg_confidence = Column(Float, default=0.0)
    status = Column(String(20), default="open")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
