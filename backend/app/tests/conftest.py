import os
import uuid
import json
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# 1. Transparent SQLite String UUID Monkey-Patch
# PostgreSQL driver coerces string literals to UUID automatically.
# SQLite lacks native UUID support, so PG_UUID.bind_processor expects a uuid.UUID object.
# In FastAPI routes, JWT tokens decode user_id as str. This monkey-patch converts str to uuid.UUID.
_orig_bind_processor = PG_UUID.bind_processor


def _patched_bind_processor(self, dialect):
    proc = _orig_bind_processor(self, dialect)
    if proc is None:
        return None

    def process(value):
        if value is not None and isinstance(value, str):
            try:
                value = uuid.UUID(value)
            except (ValueError, AttributeError):
                pass
        return proc(value)

    return process


PG_UUID.bind_processor = _patched_bind_processor

# 2. Import all model classes before mapper configuration / create_all
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.team import TeamMember
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, Message, ConversationStatus, MessageSender
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.faq import FAQOverride
from app.models.analytics import AnalyticsEvent
from app.models.knowledge_gap import KnowledgeGap

from app.main import app
from app.core.security import hash_password, create_access_token
from app.core.config import get_settings


# 3. In-memory SQLite engine with StaticPool for total test isolation & speed
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(db: Session):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# 4. Zero-network mock fixtures
@pytest.fixture
def mock_llm_service(monkeypatch):
    recorded_calls = []

    def fake_gemini(api_key: str, prompt: str) -> str:
        recorded_calls.append({"provider": "gemini", "api_key": api_key, "prompt": prompt})
        if "generate 5-8 frequently asked questions" in prompt:
            return json.dumps([{"question": "How do returns work?", "answer": "Items can be returned within 30 days."}])
        if "potential gaps in the business's knowledge base" in prompt:
            return json.dumps([
                {
                    "topic": "Refund Timeline",
                    "description": "Customer queries asking how long refunds take",
                    "suggestion": "Add refund processing timeline documentation",
                    "query_count": 4,
                    "sample_queries": ["When do I get my refund?", "How long does a refund take?"],
                }
            ])
        return "This is a deterministic mock Gemini AI response for testing."

    def fake_openai(api_key: str, prompt: str) -> str:
        recorded_calls.append({"provider": "openai", "api_key": api_key, "prompt": prompt})
        return "This is a deterministic mock OpenAI AI response for testing."

    def fake_anthropic(api_key: str, prompt: str) -> str:
        recorded_calls.append({"provider": "anthropic", "api_key": api_key, "prompt": prompt})
        return "This is a deterministic mock Anthropic AI response for testing."

    from app.services.rag_engine import LLM_PROVIDERS
    monkeypatch.setitem(LLM_PROVIDERS, "gemini", fake_gemini)
    monkeypatch.setitem(LLM_PROVIDERS, "openai", fake_openai)
    monkeypatch.setitem(LLM_PROVIDERS, "anthropic", fake_anthropic)
    monkeypatch.setattr(
        "app.services.rag_engine.LLM_PROVIDERS",
        LLM_PROVIDERS,
    )
    return recorded_calls


@pytest.fixture
def mock_embedding_service(monkeypatch):
    recorded_searches = []

    def fake_search(self, business_id: str, query: str, top_k: int = 5):
        recorded_searches.append({"business_id": business_id, "query": query, "top_k": top_k})
        q_lower = query.lower()
        if "return" in q_lower or "refund" in q_lower or "policy" in q_lower:
            return [
                {
                    "chunk": "Our return policy allows items to be returned within 30 days of purchase for a full refund.",
                    "doc_id": "mock-doc-return-policy",
                    "score": 0.88,
                }
            ]
        elif "shipping" in q_lower or "delivery" in q_lower:
            return [
                {
                    "chunk": "Standard shipping takes 3-5 business days across the continental US.",
                    "doc_id": "mock-doc-shipping",
                    "score": 0.82,
                }
            ]
        return []

    monkeypatch.setattr("app.services.embedding_service.EmbeddingService.search", fake_search)
    return recorded_searches


@pytest.fixture
def clean_env(monkeypatch):
    settings = get_settings()
    orig_key = getattr(settings, "GEMINI_API_KEY", "")
    get_settings.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "platform_default_gemini_test_key_12345")
    settings.GEMINI_API_KEY = "platform_default_gemini_test_key_12345"
    yield
    settings.GEMINI_API_KEY = orig_key
    get_settings.cache_clear()


# 5. Core seed data fixtures
@pytest.fixture
def test_user(db: Session) -> User:
    user = User(
        email="testowner@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Test Owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_business(db: Session) -> Business:
    business = Business(
        name="SupportAI Testing Enterprises",
        slug=f"supportai-test-{uuid.uuid4().hex[:8]}",
        description="Business instance for automated test suite",
        api_key=f"sec_{uuid.uuid4().hex}",
        llm_provider="gemini",
        llm_api_key=None,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@pytest.fixture
def test_team_member(db: Session, test_user: User, test_business: Business) -> TeamMember:
    member = TeamMember(
        business_id=test_business.id,
        user_id=test_user.id,
        role=UserRole.OWNER,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@pytest.fixture
def test_widget_config(db: Session, test_business: Business) -> WidgetConfig:
    config = WidgetConfig(
        business_id=test_business.id,
        bot_name="SupportBot",
        welcome_message="Hello! How can I help you today?",
        primary_color="#6366f1",
        position="bottom-right",
        allowed_domains=["example.com", "app.example.com"],
        allow_localhost=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@pytest.fixture
def auth_headers(test_user: User, test_business: Business, test_team_member: TeamMember) -> dict:
    token = create_access_token({"sub": str(test_user.id)})
    return {
        "Authorization": f"Bearer {token}",
        "X-Business-Id": str(test_business.id),
    }


@pytest.fixture
def viewer_user(db: Session, test_business: Business) -> User:
    user = User(
        email="viewer@example.com",
        hashed_password=hash_password("ViewerPass123!"),
        full_name="Viewer User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    member = TeamMember(
        business_id=test_business.id,
        user_id=user.id,
        role=UserRole.VIEWER,
    )
    db.add(member)
    db.commit()
    return user


@pytest.fixture
def viewer_headers(viewer_user: User, test_business: Business) -> dict:
    token = create_access_token({"sub": str(viewer_user.id)})
    return {
        "Authorization": f"Bearer {token}",
        "X-Business-Id": str(test_business.id),
    }
