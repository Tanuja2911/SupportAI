from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.team import TeamMember
from app.schemas.business import LLMSettingsUpdate, LLMSettingsResponse

router = APIRouter(prefix="/api/ai-settings", tags=["ai-settings"])

SUPPORTED_PROVIDERS = ["gemini", "openai", "anthropic"]


def _get_business(business_id: str, user: User, db: Session) -> Business:
    member = db.query(TeamMember).filter(
        TeamMember.business_id == business_id,
        TeamMember.user_id == user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.get("/{business_id}", response_model=LLMSettingsResponse)
def get_ai_settings(
    business_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business(business_id, current_user, db)
    return LLMSettingsResponse(
        llm_provider=business.llm_provider,
        has_api_key=bool(business.llm_api_key),
    )


@router.put("/{business_id}", response_model=LLMSettingsResponse)
def update_ai_settings(
    business_id: str,
    data: LLMSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business(business_id, current_user, db)

    if data.llm_provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Provider must be one of: {', '.join(SUPPORTED_PROVIDERS)}")

    business.llm_provider = data.llm_provider
    business.llm_api_key = data.llm_api_key
    db.commit()

    return LLMSettingsResponse(
        llm_provider=business.llm_provider,
        has_api_key=bool(business.llm_api_key),
    )
