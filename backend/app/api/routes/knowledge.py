import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.team import TeamMember
from app.schemas.document import DocumentResponse, DocumentURLUpload
from app.api.deps import get_current_business_id

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
settings = get_settings()


@router.get("/{business_id}/documents", response_model=list[DocumentResponse])
def list_documents(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_team_access(db, current_user.id, business_id)
    docs = db.query(Document).filter(Document.business_id == business_id).order_by(Document.created_at.desc()).all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("/{business_id}/upload", response_model=DocumentResponse)
async def upload_document(
    business_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_team_access(db, current_user.id, business_id, require_role=["owner", "agent"])

    allowed_types = {"application/pdf": "pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx", "text/plain": "txt"}
    file_type = allowed_types.get(file.content_type)
    if not file_type:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    upload_dir = os.path.join(settings.UPLOAD_DIR, str(business_id))
    os.makedirs(upload_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_id}.{file_type}")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB")

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        business_id=business_id,
        title=file.filename or "Untitled",
        file_type=file_type,
        file_path=file_path,
        status=DocumentStatus.PENDING,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    from app.services.document_processor import process_document_task
    process_document_task.delay(str(doc.id))

    return DocumentResponse.model_validate(doc)


@router.post("/{business_id}/url", response_model=DocumentResponse)
def upload_url(
    business_id: uuid.UUID,
    data: DocumentURLUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_team_access(db, current_user.id, business_id, require_role=["owner", "agent"])

    doc = Document(
        business_id=business_id,
        title=data.title or data.url,
        file_type="url",
        source_url=data.url,
        status=DocumentStatus.PENDING,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    from app.services.document_processor import process_document_task
    process_document_task.delay(str(doc.id))

    return DocumentResponse.model_validate(doc)


@router.delete("/{business_id}/documents/{doc_id}")
def delete_document(
    business_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_team_access(db, current_user.id, business_id, require_role=["owner", "agent"])

    doc = db.query(Document).filter(Document.id == doc_id, Document.business_id == business_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"detail": "Document deleted"}


def _verify_team_access(db: Session, user_id, business_id, require_role=None):
    member = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.business_id == business_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this business")
    if require_role and member.role.value not in require_role:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return member
