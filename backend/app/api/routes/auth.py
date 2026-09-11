import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.team import TeamMember
from app.models.widget import WidgetConfig
from app.models.user import UserRole
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, GoogleAuthRequest, UserUpdate
from app.schemas.business import BusinessCreate, BusinessResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/business", response_model=BusinessResponse)
def create_business(data: BusinessCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    slug = data.name.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    existing = db.query(Business).filter(Business.slug == slug).first()
    if existing:
        slug = f"{slug}-{secrets.token_hex(3)}"

    business = Business(
        name=data.name,
        slug=slug,
        description=data.description,
        website=data.website,
        api_key=secrets.token_hex(32),
    )
    db.add(business)
    db.flush()

    team_member = TeamMember(
        user_id=current_user.id,
        business_id=business.id,
        role=UserRole.OWNER,
    )
    db.add(team_member)

    widget = WidgetConfig(business_id=business.id)
    db.add(widget)

    db.commit()
    db.refresh(business)
    return BusinessResponse.model_validate(business)


@router.get("/my-businesses", response_model=list[BusinessResponse])
def get_my_businesses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    business_ids = [m.business_id for m in memberships]
    if not business_ids:
        return []
    businesses = db.query(Business).filter(Business.id.in_(business_ids)).all()
    return [BusinessResponse.model_validate(b) for b in businesses]
