import json
import logging
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.core.database import get_db
from app.core.security import get_current_user
from app.models.business import Business
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.faq import FAQOverride
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.chat import FAQCreate, FAQResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/faq", tags=["faq"])


@router.get("/{business_id}", response_model=list[FAQResponse])
def list_faqs(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)
    faqs = db.query(FAQOverride).filter(FAQOverride.business_id == business_id).order_by(FAQOverride.created_at.desc()).all()
    return [FAQResponse.model_validate(f) for f in faqs]


@router.post("/{business_id}", response_model=FAQResponse)
def create_faq(
    business_id: uuid.UUID,
    data: FAQCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id, require_role=["owner", "agent"])
    faq = FAQOverride(
        business_id=business_id,
        question=data.question,
        answer=data.answer,
        created_by=current_user.id,
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return FAQResponse.model_validate(faq)


@router.delete("/{business_id}/{faq_id}")
def delete_faq(
    business_id: uuid.UUID,
    faq_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id, require_role=["owner", "agent"])
    faq = db.query(FAQOverride).filter(FAQOverride.id == faq_id, FAQOverride.business_id == business_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(faq)
    db.commit()
    return {"detail": "FAQ deleted"}


@router.post("/{business_id}/auto-generate")
def auto_generate_faqs(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id, require_role=["owner", "agent"])

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    ready_docs = db.query(Document).filter(
        Document.business_id == business_id,
        Document.status == DocumentStatus.READY,
    ).all()

    if not ready_docs:
        raise HTTPException(status_code=400, detail="No processed documents found. Upload and process documents first.")

    doc_ids = [d.id for d in ready_docs]
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id.in_(doc_ids)
    ).order_by(DocumentChunk.chunk_index).limit(30).all()

    if not chunks:
        raise HTTPException(status_code=400, detail="No document content found.")

    combined_text = "\n\n".join([c.content for c in chunks])
    if len(combined_text) > 8000:
        combined_text = combined_text[:8000]

    prompt = f"""Analyze the following business documentation and generate 5-8 frequently asked questions (FAQs) that customers would likely ask, along with clear, concise answers based on the content.

Documentation:
{combined_text}

Return ONLY a valid JSON array of objects with "question" and "answer" keys. No markdown, no explanation, just the JSON array.
Example format:
[{{"question": "What is your return policy?", "answer": "We offer a 30-day return policy..."}}]"""

    from app.services.llm_service import classify_llm_error, resolve_llm_credentials
    provider, api_key = resolve_llm_credentials(business)

    try:
        from app.services.rag_engine import LLM_PROVIDERS, _call_gemini
        call_fn = LLM_PROVIDERS.get(provider, _call_gemini)
        raw = call_fn(api_key, prompt)
    except Exception as error:
        details = classify_llm_error(error, provider, api_key)
        logger.warning(
            "Auto-FAQ provider request failed (%s): %s",
            details["error_code"],
            details["diagnostic"],
        )
        raise HTTPException(
            status_code=502,
            detail={
                "message": details["user_message"],
                "error_code": details["error_code"],
                "diagnostic": details["diagnostic"],
                "action_hint": details["action_hint"],
            },
        ) from error

    try:
        suggestions = _parse_faq_suggestions(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        logger.warning("Auto-FAQ provider returned an invalid FAQ payload")
        raise HTTPException(
            status_code=502,
            detail={
                "message": "The AI provider returned an unreadable FAQ response. Please try again.",
                "error_code": "INVALID_PROVIDER_RESPONSE",
                "diagnostic": "Expected a JSON array of FAQ objects with non-empty question and answer fields.",
                "action_hint": "Retry generation or choose another provider in AI Settings.",
            },
        )

    return {"suggestions": suggestions}


def _parse_faq_suggestions(raw: str) -> list[dict[str, str]]:
    """Accept a JSON array directly or embedded in common provider markdown wrappers."""
    if not isinstance(raw, str):
        raise TypeError("FAQ response must be text")
    if not raw.strip():
        raise ValueError("Empty FAQ response")

    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            raise
        payload = json.loads(match.group(0))

    if not isinstance(payload, list):
        raise TypeError("FAQ response must be a JSON array")

    result = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        question = item.get("question")
        answer = item.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            continue
        question = question.strip()
        answer = answer.strip()
        if question and answer:
            result.append({"question": question, "answer": answer})
        if len(result) == 8:
            break

    if not result:
        raise ValueError("No valid FAQ pairs generated")
    return result


def _verify_access(db, user_id, business_id, require_role=None):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")
    if require_role and member.role.value not in require_role:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
