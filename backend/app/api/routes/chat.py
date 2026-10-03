import json
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.origin_guard import validate_origin
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, Message, ConversationStatus, MessageSender
from app.models.faq import FAQOverride
from app.models.document import Document, DocumentStatus
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_engine import RAGEngine

router = APIRouter(prefix="/api/chat", tags=["chat"])

ESCALATION_PATTERN = re.compile(
    r"\b("
    r"(?:talk|speak|connect(?: me)?)\s+(?:to|with)\s+(?:an?\s+)?(?:human|agent|person|representative|support\s+team)"
    r"|(?:need|want)\s+(?:to\s+(?:talk|speak)\s+(?:to|with)\s+(?:an?\s+)?(?:human|agent|person|representative)|(?:an?\s+)?(?:human|live agent|representative)|real person\s+support)"
    r"|human\s+support(?:\s+please)?"
    r"|live\s+agent(?:\s+please)?"
    r"|human\s+agent(?:\s+please)?"
    r"|representative\s+please"
    r"|contact\s+support(?:\s+team)?"
    r"|real\s+person\s+support"
    r")\b",
    re.IGNORECASE,
)

GREETING_PATTERN = re.compile(
    r"^(?:"
    r"(?:hi|hello|hey|greetings|howdy|sup|yo|good\s+(?:morning|afternoon|evening|day)|morning|afternoon|evening)"
    r"(?:\s+there)?"
    r")"
    r"(?:\s*[,!.-]?\s*"
    r"(?:can\s+you\s+help(?:\s+me)?|how\s+are\s+you(?:\s+doing)?|how\x27s\s+it\s+going|i\s+need\s+(?:some\s+)?help|quick\s+question|what\x27s\s+up)"
    r")?"
    r"[\s!.,?]*$",
    re.IGNORECASE,
)

GRATITUDE_PATTERN = re.compile(
    r"^(?:thanks(?:\s+(?:a\s+lot|a\s+million|a\s+ton|a\s+bunch|so\s+much|very\s+much|again))?|thank\s+you(?:\s+(?:so\s+much|very\s+much))?|many\s+thanks|(?:much|greatly)\s+appreciated|appreciate\s+it)[\s!.,?]*$",
    re.IGNORECASE,
)

CLOSING_PATTERN = re.compile(
    r"^(?:bye(?:\s+bye)?|goodbye|good\s+bye|have\s+a\s+(?:nice|great|good)\s+(?:day|one|evening|weekend)|see\s+(?:you|ya)(?:\s+later)?(?:\s+alligator)?|take\s+care|cya)[\s!.,?]*$",
    re.IGNORECASE,
)

IDENTITY_HELP_PATTERN = re.compile(
    r"^(?:"
    r"who\s+are\s+you"
    r"|what\s+can\s+you\s+do"
    r"|what\s+do\s+you\s+do"
    r"|how\s+can\s+you\s+help(?:\s+me)?"
    r"|tell\s+me\s+about\s+yourself"
    r"|help(?:\s+me)?"
    r")[\s!.,?]*$",
    re.IGNORECASE,
)


@router.post("/{token}", response_model=ChatResponse)
def customer_chat(
    token: str,
    data: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # 1. Lookup Business by public_key or api_key (404 if invalid)
    business = db.query(Business).filter((Business.public_key == token) | (Business.api_key == token)).first()
    if not business:
        raise HTTPException(status_code=404, detail="Invalid API key")

    # 2. Origin Guard validation (403 if disallowed, BEFORE DB mutation or RAG execution)
    origin = request.headers.get("origin")
    referer = request.headers.get("referer") or request.headers.get("referrer")
    cfg = business.widget_config or db.query(WidgetConfig).filter(WidgetConfig.business_id == business.id).first()
    allowed_domains = (cfg.allowed_domains if cfg else None) or []
    allow_localhost = cfg.allow_localhost if (cfg and cfg.allow_localhost is not None) else True

    if not validate_origin(origin, referer, allowed_domains, allow_localhost):
        raise HTTPException(status_code=403, detail="Origin not allowed")

    # 3. Conversation lookup or creation
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

    sanitized_message = data.message.replace("\x00", "") if data.message else ""
    customer_msg = Message(
        conversation_id=conversation.id,
        sender=MessageSender.CUSTOMER,
        content=sanitized_message,
    )
    db.add(customer_msg)

    clean_msg = sanitized_message.strip()

    # 4. Strict Explicit Human Escalation Check
    if ESCALATION_PATTERN.search(clean_msg):
        conversation.status = ConversationStatus.ESCALATED
        esc_msg = "I have escalated this conversation to our human support team. A representative will be with you shortly."
        ai_msg = Message(
            conversation_id=conversation.id,
            sender=MessageSender.AI,
            content=esc_msg,
            confidence_score=1.0,
            sources_json=json.dumps([]),
            is_escalation_trigger=True,
        )
        db.add(ai_msg)
        db.commit()
        return ChatResponse(
            conversation_id=conversation.id,
            message=esc_msg,
            confidence_score=1.0,
            sources=[],
            is_escalated=True,
        )

    # 5. Conversational Intent Detection (Greetings, Gratitude, Closings, Identity/Help)
    is_conv_intent = False
    conv_response = ""

    if GREETING_PATTERN.match(clean_msg):
        is_conv_intent = True
        conv_response = cfg.welcome_message if (cfg and cfg.welcome_message) else "Hello! How can I help you today?"
    elif GRATITUDE_PATTERN.match(clean_msg):
        is_conv_intent = True
        conv_response = "You're very welcome! Let me know if there's anything else I can help you with."
    elif CLOSING_PATTERN.match(clean_msg):
        is_conv_intent = True
        conv_response = "Goodbye! Have a great day, and feel free to reach out if you need anything else."
    elif IDENTITY_HELP_PATTERN.match(clean_msg):
        is_conv_intent = True
        conv_response = (
            "I am your AI customer support assistant. I can answer questions about our products, "
            "services, policies, and store information. How can I help you today?"
        )

    if is_conv_intent:
        if conversation.status == ConversationStatus.ESCALATED:
            conversation.status = ConversationStatus.ACTIVE
        ai_msg = Message(
            conversation_id=conversation.id,
            sender=MessageSender.AI,
            content=conv_response,
            confidence_score=1.0,
            sources_json=json.dumps([]),
            is_escalation_trigger=False,
        )
        db.add(ai_msg)
        db.commit()
        return ChatResponse(
            conversation_id=conversation.id,
            message=conv_response,
            confidence_score=1.0,
            sources=[],
            is_escalated=False,
        )

    # If an agent is assigned, let the human agent respond
    if conversation.status == ConversationStatus.ESCALATED and conversation.assigned_agent_id:
        db.commit()
        return ChatResponse(
            conversation_id=conversation.id,
            message="A support agent has been assigned to your conversation and will be with you shortly.",
            confidence_score=1.0,
            is_escalated=True,
        )

    # 6. FAQ Overrides Check
    faq = db.query(FAQOverride).filter(
        FAQOverride.business_id == business.id,
        FAQOverride.is_active == True,
    ).all()

    if clean_msg:
        m_clean = clean_msg.lower()
        for f in faq:
            q_clean = f.question.strip().lower()
            q_clean_base = q_clean.strip("?!. ")
            if q_clean == m_clean or (len(q_clean_base) >= 4 and q_clean_base in m_clean):
                if conversation.status == ConversationStatus.ESCALATED:
                    conversation.status = ConversationStatus.ACTIVE
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
                    is_escalated=False,
                )

    # 7. Check if any documents are uploaded and processed yet
    ready_docs = db.query(Document).filter(
        Document.business_id == business.id,
        Document.status == DocumentStatus.READY,
    ).count()

    if ready_docs == 0:
        empty_msg = (
            "I don't have any knowledge base documents loaded yet. "
            "Please upload your documents in the SupportAI dashboard under Knowledge Base so I can assist you."
        )
        ai_msg = Message(
            conversation_id=conversation.id,
            sender=MessageSender.AI,
            content=empty_msg,
            confidence_score=1.0,
            sources_json=json.dumps([]),
        )
        db.add(ai_msg)
        db.commit()
        return ChatResponse(
            conversation_id=conversation.id,
            message=empty_msg,
            confidence_score=1.0,
            sources=[],
            is_escalated=False,
        )

    # 8. RAG Execution
    rag = RAGEngine(
        str(business.id),
        business=business,
        llm_provider=business.llm_provider,
        llm_api_key=business.llm_api_key,
    )
    result = rag.query(clean_msg or data.message, db)

    # Low-confidence RAG fallback without falsely locking conversation into ESCALATED
    answer = result["answer"]
    error_code = result.get("error_code")
    diagnostic = result.get("diagnostic")
    action_hint = result.get("action_hint")

    if result["confidence"] < 0.1 and not result.get("sources"):
        if "No API key configured" not in answer and not error_code:
            answer = (
                "I don't have enough information in my knowledge base to answer that, "
                "but I can connect you with our team if needed."
            )

    ai_msg = Message(
        conversation_id=conversation.id,
        sender=MessageSender.AI,
        content=answer,
        confidence_score=result["confidence"],
        sources_json=json.dumps(result["sources"]),
        is_escalation_trigger=False,
    )
    db.add(ai_msg)
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        message=answer,
        confidence_score=result["confidence"],
        sources=result["sources"],
        is_escalated=False,
        error_code=error_code,
        diagnostic=diagnostic,
        action_hint=action_hint,
    )
