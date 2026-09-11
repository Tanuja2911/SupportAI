import os
import json
import logging
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("supportiq", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text_from_url(url: str) -> str:
    import requests
    from bs4 import BeautifulSoup
    response = requests.get(url, timeout=15, headers={"User-Agent": "SupportAI Bot"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


@celery_app.task(name="process_document")
def process_document_task(document_id: str):
    from app.models.user import User
    from app.models.business import Business
    from app.models.team import TeamMember
    from app.models.document import Document, DocumentChunk, DocumentStatus
    from app.models.conversation import Conversation, Message
    from app.models.widget import WidgetConfig
    from app.models.faq import FAQOverride
    from app.models.analytics import AnalyticsEvent

    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    doc = None

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return

        doc.status = DocumentStatus.PROCESSING
        db.commit()

        if doc.file_type == "pdf":
            text = extract_text_from_pdf(doc.file_path)
        elif doc.file_type == "docx":
            text = extract_text_from_docx(doc.file_path)
        elif doc.file_type == "txt":
            with open(doc.file_path, "r") as f:
                text = f.read()
        elif doc.file_type == "url":
            text = extract_text_from_url(doc.source_url)
        else:
            raise ValueError(f"Unsupported file type: {doc.file_type}")

        chunks = chunk_text(text)

        from app.services.embedding_service import EmbeddingService
        embedding_svc = EmbeddingService()

        for i, chunk_text_content in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=doc.id,
                content=chunk_text_content,
                chunk_index=i,
                token_count=len(chunk_text_content.split()),
            )
            db.add(chunk)

        db.flush()

        embeddings = embedding_svc.encode(chunks)
        embedding_svc.add_to_index(str(doc.business_id), chunks, embeddings, [str(doc.id)] * len(chunks))

        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.READY
        db.commit()

        logger.info(f"Document {document_id} processed: {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()
