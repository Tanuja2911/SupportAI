import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message, ConversationStatus, MessageSender
from app.models.document import Document, DocumentStatus
from app.models.team import TeamMember
from app.schemas.analytics import DashboardStats, DailyStats

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/{business_id}/dashboard", response_model=DashboardStats)
def get_dashboard(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)

    total_convs = db.query(func.count(Conversation.id)).filter(Conversation.business_id == business_id).scalar() or 0
    active_convs = db.query(func.count(Conversation.id)).filter(Conversation.business_id == business_id, Conversation.status == ConversationStatus.ACTIVE).scalar() or 0
    escalated_convs = db.query(func.count(Conversation.id)).filter(Conversation.business_id == business_id, Conversation.status == ConversationStatus.ESCALATED).scalar() or 0
    resolved_convs = db.query(func.count(Conversation.id)).filter(Conversation.business_id == business_id, Conversation.status == ConversationStatus.RESOLVED).scalar() or 0

    conv_ids = db.query(Conversation.id).filter(Conversation.business_id == business_id).subquery()
    total_msgs = db.query(func.count(Message.id)).filter(Message.conversation_id.in_(conv_ids)).scalar() or 0
    ai_msgs = db.query(func.count(Message.id)).filter(Message.conversation_id.in_(conv_ids), Message.sender == MessageSender.AI).scalar() or 0
    avg_conf = db.query(func.avg(Message.confidence_score)).filter(Message.conversation_id.in_(conv_ids), Message.sender == MessageSender.AI).scalar() or 0.0

    total_docs = db.query(func.count(Document.id)).filter(Document.business_id == business_id).scalar() or 0
    ready_docs = db.query(func.count(Document.id)).filter(Document.business_id == business_id, Document.status == DocumentStatus.READY).scalar() or 0

    return DashboardStats(
        total_conversations=total_convs,
        active_conversations=active_convs,
        escalated_conversations=escalated_convs,
        resolved_conversations=resolved_convs,
        total_messages=total_msgs,
        ai_messages=ai_msgs,
        avg_confidence=round(float(avg_conf), 3),
        total_documents=total_docs,
        ready_documents=ready_docs,
    )


@router.get("/{business_id}/daily", response_model=list[DailyStats])
def get_daily_stats(
    business_id: uuid.UUID,
    days: int = Query(default=30, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    daily = db.query(
        cast(Conversation.created_at, Date).label("date"),
        func.count(Conversation.id).label("conversations"),
    ).filter(
        Conversation.business_id == business_id,
        Conversation.created_at >= since,
    ).group_by(cast(Conversation.created_at, Date)).order_by(cast(Conversation.created_at, Date)).all()

    return [DailyStats(date=str(d.date), conversations=d.conversations, messages=0) for d in daily]


def _verify_access(db, user_id, business_id, require_role=None):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not a member of this business")
