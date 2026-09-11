import uuid
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.business import Business
from app.models.team import TeamMember
from app.models.conversation import Conversation, Message, MessageSender
from app.models.knowledge_gap import KnowledgeGap

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/knowledge-gaps", tags=["knowledge-gaps"])


def _verify_access(db, user_id, business_id):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")


@router.get("/{business_id}")
def get_knowledge_gaps(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)
    gaps = db.query(KnowledgeGap).filter(
        KnowledgeGap.business_id == business_id,
    ).order_by(KnowledgeGap.query_count.desc()).all()

    return [
        {
            "id": str(g.id),
            "topic": g.topic,
            "description": g.description,
            "suggestion": g.suggestion,
            "sample_queries": json.loads(g.sample_queries) if g.sample_queries.startswith("[") else [g.sample_queries],
            "query_count": g.query_count,
            "avg_confidence": g.avg_confidence,
            "status": g.status,
            "created_at": g.created_at.isoformat(),
        }
        for g in gaps
    ]


@router.post("/{business_id}/analyze")
def analyze_knowledge_gaps(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    conversations = db.query(Conversation).filter(
        Conversation.business_id == business_id
    ).all()
    conv_ids = [c.id for c in conversations]

    if not conv_ids:
        raise HTTPException(status_code=400, detail="No conversations to analyze yet.")

    low_conf_messages = db.query(Message).filter(
        Message.conversation_id.in_(conv_ids),
        Message.sender == MessageSender.AI,
        Message.confidence_score < 0.6,
        Message.confidence_score > 0.0,
    ).all()

    customer_queries = []
    for msg in low_conf_messages:
        prev_msg = db.query(Message).filter(
            Message.conversation_id == msg.conversation_id,
            Message.sender == MessageSender.CUSTOMER,
            Message.created_at < msg.created_at,
        ).order_by(Message.created_at.desc()).first()

        if prev_msg:
            customer_queries.append({
                "query": prev_msg.content,
                "confidence": msg.confidence_score,
                "ai_response": msg.content[:200],
            })

    escalated_convs = db.query(Conversation).filter(
        Conversation.business_id == business_id,
        Conversation.status == "ESCALATED",
    ).all()
    for conv in escalated_convs:
        first_msg = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.sender == MessageSender.CUSTOMER,
        ).order_by(Message.created_at).first()
        if first_msg:
            customer_queries.append({
                "query": first_msg.content,
                "confidence": 0.0,
                "ai_response": "[escalated]",
            })

    if not customer_queries:
        return {"gaps": [], "message": "No knowledge gaps detected. Your knowledge base is covering queries well."}

    queries_text = "\n".join([
        f"- \"{q['query']}\" (confidence: {q['confidence']:.0%})"
        for q in customer_queries[:30]
    ])

    prompt = f"""Analyze these customer support queries that received low-confidence AI responses or were escalated. These represent potential gaps in the business's knowledge base.

Queries:
{queries_text}

Group them into distinct topic clusters. For each cluster, provide:
1. A short topic name
2. A description of what customers are asking about
3. A specific suggestion for what content/document the business should add
4. The approximate number of queries in this cluster

Return ONLY a valid JSON array. No markdown, no explanation.
Format:
[{{"topic": "Refund Policy", "description": "Customers frequently ask about refund timelines and eligibility", "suggestion": "Add a document covering your refund policy including timelines, eligibility criteria, and the refund process", "query_count": 5, "sample_queries": ["How do I get a refund?", "What is your return policy?"]}}]"""

    provider = business.llm_provider or "gemini"
    api_key = business.llm_api_key
    if not api_key and provider == "gemini":
        api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="No LLM API key configured. Add one in AI Settings.")

    try:
        from app.services.rag_engine import LLM_PROVIDERS, _call_gemini
        call_fn = LLM_PROVIDERS.get(provider, _call_gemini)
        raw = call_fn(api_key, prompt)

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        gaps_data = json.loads(raw)
        if not isinstance(gaps_data, list):
            raise ValueError("Not a list")

        db.query(KnowledgeGap).filter(
            KnowledgeGap.business_id == business_id,
            KnowledgeGap.status == "open",
        ).delete()

        total_queries = len(customer_queries)
        saved_gaps = []
        for g in gaps_data:
            if not isinstance(g, dict) or "topic" not in g:
                continue
            samples = g.get("sample_queries", [])
            gap = KnowledgeGap(
                business_id=business_id,
                topic=g["topic"],
                description=g.get("description", ""),
                suggestion=g.get("suggestion", ""),
                sample_queries=json.dumps(samples if isinstance(samples, list) else []),
                query_count=g.get("query_count", 1),
                avg_confidence=sum(q["confidence"] for q in customer_queries) / len(customer_queries) if customer_queries else 0,
            )
            db.add(gap)
            saved_gaps.append(gap)

        db.commit()

        return {
            "gaps_found": len(saved_gaps),
            "total_low_confidence_queries": total_queries,
            "message": f"Found {len(saved_gaps)} knowledge gaps from {total_queries} low-confidence queries.",
        }

    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response: {raw[:200]}")
        raise HTTPException(status_code=500, detail="AI returned an invalid response. Please try again.")
    except Exception as e:
        logger.error(f"Knowledge gap analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.patch("/{business_id}/{gap_id}")
def update_gap_status(
    business_id: uuid.UUID,
    gap_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)
    gap = db.query(KnowledgeGap).filter(
        KnowledgeGap.id == gap_id,
        KnowledgeGap.business_id == business_id,
    ).first()
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    gap.status = "resolved"
    db.commit()
    return {"detail": "Marked as resolved"}
