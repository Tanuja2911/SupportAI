from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.business import Business
from app.models.team import TeamMember
from app.schemas.business import (
    LLMSettingsUpdate,
    LLMSettingsResponse,
    LLMTestConnectionRequest,
    LLMTestConnectionResponse,
)
from app.services.llm_service import (
    resolve_llm_credentials,
    test_llm_connection,
    SUPPORTED_PROVIDERS,
)

router = APIRouter(prefix="/api/ai-settings", tags=["ai-settings"])



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
    settings = get_settings()
    has_custom = bool(business.llm_api_key and business.llm_api_key.strip())
    has_platform = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    return LLMSettingsResponse(
        llm_provider=business.llm_provider or "gemini",
        has_api_key=has_custom,
        is_using_platform_default=(not has_custom) and has_platform,
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

    raw_key = data.llm_api_key.strip() if data.llm_api_key else None
    business.llm_api_key = raw_key if raw_key else None
    business.llm_provider = data.llm_provider
    db.commit()
    db.refresh(business)

    settings = get_settings()
    has_custom = bool(business.llm_api_key and business.llm_api_key.strip())
    has_platform = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    return LLMSettingsResponse(
        llm_provider=business.llm_provider or "gemini",
        has_api_key=has_custom,
        is_using_platform_default=(not has_custom) and has_platform,
    )


@router.post("/test-connection", response_model=LLMTestConnectionResponse)
def test_connection_general(
    data: LLMTestConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = data.provider.strip().lower() if data.provider else "gemini"
    api_key = data.api_key.strip() if data.api_key and data.api_key.strip() else None
    is_platform = False

    business = None
    if data.business_id:
        business = _get_business(data.business_id, current_user, db)
    else:
        member = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).first()
        if member:
            business = db.query(Business).filter(Business.id == member.business_id).first()

    if not api_key:
        try:
            resolved_provider, resolved_key = resolve_llm_credentials(business)
            provider = resolved_provider
            api_key = resolved_key
            is_platform = not bool(business and business.llm_api_key and business.llm_api_key.strip())
        except HTTPException:
            return LLMTestConnectionResponse(
                status="error",
                provider=provider,
                model=None,
                latency_ms=None,
                message="No LLM API key configured.",
                diagnostic="Neither a custom business key nor a platform default key is available.",
                action_hint="Please enter a valid API key to test.",
                is_platform_default=False,
            )

    result = test_llm_connection(provider=provider, api_key=api_key)
    result["is_platform_default"] = is_platform
    return LLMTestConnectionResponse(**result)


@router.post("/{business_id}/test-connection", response_model=LLMTestConnectionResponse)
def test_connection_business(
    business_id: str,
    data: LLMTestConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = _get_business(business_id, current_user, db)

    provider = data.provider.strip().lower() if data.provider else "gemini"
    api_key = data.api_key.strip() if data.api_key and data.api_key.strip() else None
    is_platform = False

    if not api_key:
        try:
            resolved_provider, resolved_key = resolve_llm_credentials(business)
            provider = resolved_provider
            api_key = resolved_key
            is_platform = not bool(business.llm_api_key and business.llm_api_key.strip())
        except HTTPException:
            return LLMTestConnectionResponse(
                status="error",
                provider=provider,
                model=None,
                latency_ms=None,
                message="No LLM API key configured for this business or platform.",
                diagnostic="Neither a custom business key nor a platform default key is available.",
                action_hint="Enter a valid API key in AI Settings.",
                is_platform_default=False,
            )

    result = test_llm_connection(provider=provider, api_key=api_key)
    result["is_platform_default"] = is_platform
    return LLMTestConnectionResponse(**result)
