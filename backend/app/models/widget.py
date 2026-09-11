import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), unique=True, nullable=False)
    bot_name = Column(String(100), default="Support Assistant")
    welcome_message = Column(Text, default="Hi! How can I help you today?")
    primary_color = Column(String(7), default="#6366f1")
    position = Column(String(20), default="bottom-right")
    show_branding = Column(Boolean, default=True)
    auto_open_delay = Column(String(10), nullable=True)
    placeholder_text = Column(String(255), default="Type your question...")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="widget_config")
