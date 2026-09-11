import uuid
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.team import TeamMember


def get_current_business_id(
    x_business_id: str = Header(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    try:
        business_id = uuid.UUID(x_business_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid business ID")

    member = db.query(TeamMember).filter(
        TeamMember.user_id == current_user.id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")

    return business_id
