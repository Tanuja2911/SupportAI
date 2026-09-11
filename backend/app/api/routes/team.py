import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.team import TeamMember
from app.schemas.business import TeamMemberAdd, TeamMemberResponse

router = APIRouter(prefix="/api/team", tags=["team"])


@router.get("/{business_id}/members", response_model=list[TeamMemberResponse])
def list_members(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id)
    members = db.query(TeamMember).filter(TeamMember.business_id == business_id).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append(TeamMemberResponse(
            id=m.id,
            user_id=m.user_id,
            email=user.email,
            full_name=user.full_name,
            role=m.role.value,
            created_at=m.created_at,
        ))
    return result


@router.post("/{business_id}/members", response_model=TeamMemberResponse)
def add_member(
    business_id: uuid.UUID,
    data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id, require_role=["owner"])

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. They must register first.")

    existing = db.query(TeamMember).filter(
        TeamMember.user_id == user.id,
        TeamMember.business_id == business_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a team member")

    member = TeamMember(
        user_id=user.id,
        business_id=business_id,
        role=UserRole(data.role),
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return TeamMemberResponse(
        id=member.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=member.role.value,
        created_at=member.created_at,
    )


@router.delete("/{business_id}/members/{member_id}")
def remove_member(
    business_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_access(db, current_user.id, business_id, require_role=["owner"])

    member = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.business_id == business_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    db.delete(member)
    db.commit()
    return {"detail": "Member removed"}


def _verify_access(db, user_id, business_id, require_role=None):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")
    if require_role and member.role.value not in require_role:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
