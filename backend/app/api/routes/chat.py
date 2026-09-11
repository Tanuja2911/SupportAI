import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.business import Business
from app.models.conversation import Conversation, Message, ConversationStatus, MessageSender
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_engine import RAGEngine

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/{api_key}", response_model=ChatResponse)
def customer_chat(
    api_key: str,
    data: ChatRequest,
    db: Session = Depends(get_db),
):
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Invalid API key")

    if data.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == data.conversation_id,
            Conversation.business_id == business.id,
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            business_id=business.id,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
        )
        db.add(conversation)
        db.flush()

    customer_msg = Message(
        conversation_id=conversation.id,
        sender=MessageSender.CUSTOMER,
        content=data.message,
    )
    db.add(customer_msg)

    if conversation.status == ConversationStatus.ESCALATED:
        db.commit()
        return ChatResponse(
            conversation_id=conversation.id,
            message="Your conversation has been escalated to a human agent. They'll be with you shortly.",
            confidence_score=1.0,
            is_escalated=True,
        )

    from app.models.faq import FAQOverride
    faq = db.query(FAQOverride).filter(
        FAQOverride.business_id == business.id,
        FAQOverride.is_active == True,
    ).all()

    for f in faq:
        if f.question.lower() in data.message.lower() or data.message.lower() in f.question.lower():
            ai_msg = Message(
                conversation_id=conversation.id,
                sender=MessageSender.AI,
                content=f.answer,
                confidence_score=1.0,
                sources_json=json.dumps([{"type": "faq", "question": f.question}]),
            )
            db.add(ai_msg)
            db.commit()
            return ChatResponse(
                conversation_id=conversation.id,
                message=f.answer,
                confidence_score=1.0,
                sources=[{"type": "faq", "question": f.question}],
            )

    rag = RAGEngine(str(business.id), llm_provider=business.llm_provider, llm_api_key=business.llm_api_key)
    result = rag.query(data.message, db)

    is_escalated = result["confidence"] < 0.1
    if is_escalated:
        conversation.status = ConversationStatus.ESCALATED

    ai_msg = Message(
        conversation_id=conversation.id,
        sender=MessageSender.AI,
        content=result["answer"],
        confidence_score=result["confidence"],
        sources_json=json.dumps(result["sources"]),
        is_escalation_trigger=is_escalated,
    )
    db.add(ai_msg)
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        message=result["answer"],
        confidence_score=result["confidence"],
        sources=result["sources"],
        is_escalated=is_escalated,
    )
