import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message, ConversationStatus, MessageSender
from app.models.team import TeamMember
from app.schemas.chat import ConversationResponse, MessageResponse, EscalationAction

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/{business_id}", response_model=list[ConversationResponse])
def list_conversations(
    business_id: uuid.UUID,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)

    query = db.query(Conversation).filter(Conversation.business_id == business_id)
    if status:
        query = query.filter(Conversation.status == status)
    conversations = query.order_by(Conversation.updated_at.desc()).all()

    result = []
    for conv in conversations:
        msg_count = db.query(func.count(Message.id)).filter(Message.conversation_id == conv.id).scalar()
        resp = ConversationResponse.model_validate(conv)
        resp.message_count = msg_count
        result.append(resp)
    return result


@router.get("/{business_id}/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    business_id: uuid.UUID,
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.business_id == business_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/{business_id}/{conversation_id}/escalate")
def handle_escalation(
    business_id: uuid.UUID,
    conversation_id: uuid.UUID,
    data: EscalationAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id, require_role=["owner", "agent"])

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.business_id == business_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if data.action == "respond" and data.agent_response:
        msg = Message(
            conversation_id=conversation_id,
            sender=MessageSender.AGENT,
            content=data.agent_response,
            confidence_score=1.0,
        )
        db.add(msg)
        conv.status = ConversationStatus.ACTIVE
        conv.assigned_agent_id = current_user.id
    elif data.action == "resolve":
        conv.status = ConversationStatus.RESOLVED
    elif data.action == "close":
        conv.status = ConversationStatus.CLOSED

    db.commit()
    return {"detail": f"Conversation {data.action}d"}


def _verify_access(db, user_id, business_id, require_role=None):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")
    if require_role and member.role.value not in require_role:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
