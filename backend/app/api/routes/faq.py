import uuid
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.faq import FAQOverride
from app.models.team import TeamMember
from app.models.document import DocumentChunk, Document, DocumentStatus
from app.schemas.chat import FAQCreate, FAQResponse
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
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

        suggestions = json.loads(raw)
        if not isinstance(suggestions, list):
            raise ValueError("Response is not a list")

        result = []
        for item in suggestions:
            if isinstance(item, dict) and "question" in item and "answer" in item:
                result.append({
                    "question": str(item["question"]).strip(),
                    "answer": str(item["answer"]).strip(),
                })

        if not result:
            raise ValueError("No valid FAQ pairs generated")

        return {"suggestions": result}

    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response as JSON: {raw[:200]}")
        raise HTTPException(status_code=500, detail="AI returned an invalid response. Please try again.")
    except Exception as e:
        logger.error(f"Auto-FAQ generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate FAQs: {str(e)}")


def _verify_access(db, user_id, business_id, require_role=None):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")
    if require_role and member.role.value not in require_role:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
