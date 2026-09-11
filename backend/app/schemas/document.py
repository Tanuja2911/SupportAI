from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    file_type: str
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentURLUpload(BaseModel):
    url: str
    title: str | None = None
