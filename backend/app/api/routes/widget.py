import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.team import TeamMember
from app.schemas.widget import WidgetConfigUpdate, WidgetConfigResponse

router = APIRouter(prefix="/api/widget", tags=["widget"])


@router.get("/{business_id}/config", response_model=WidgetConfigResponse)
def get_widget_config(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)
    config = db.query(WidgetConfig).filter(WidgetConfig.business_id == business_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Widget config not found")
    return WidgetConfigResponse.model_validate(config)


@router.put("/{business_id}/config", response_model=WidgetConfigResponse)
def update_widget_config(
    business_id: uuid.UUID,
    data: WidgetConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id, require_role=["owner"])
    config = db.query(WidgetConfig).filter(WidgetConfig.business_id == business_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Widget config not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return WidgetConfigResponse.model_validate(config)


@router.get("/embed/{api_key}", response_model=WidgetConfigResponse)
def get_embed_config(api_key: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.api_key == api_key).first()
    if not business:
        raise HTTPException(status_code=404, detail="Invalid API key")
    config = db.query(WidgetConfig).filter(WidgetConfig.business_id == business.id).first()
    return WidgetConfigResponse.model_validate(config)


def _verify_access(db, user_id, business_id, require_role=None):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")
    if require_role and member.role.value not in require_role:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
