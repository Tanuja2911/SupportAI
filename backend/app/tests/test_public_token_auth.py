import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.user import User
from app.models.document import Document, DocumentStatus


class TestPublicTokenDecouplingAndAuth:
    def test_business_creation_returns_public_and_secret_keys(self, client: TestClient, db: Session, test_user: User):
        """POST /api/auth/business provisions and returns both public_key (pk_...) and api_key."""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "name": f"New Company {uuid.uuid4().hex[:6]}",
            "description": "Public key testing business",
            "website": "https://newcompany.example.com",
        }
        res = client.post("/api/auth/business", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert "public_key" in data
        assert "api_key" in data
        assert data["public_key"].startswith("pk_")
        assert len(data["public_key"]) >= 35
        assert data["public_key"] != data["api_key"]

        # Verify persisted in database
        biz = db.query(Business).filter(Business.id == data["id"]).first()
        assert biz is not None
        assert biz.public_key == data["public_key"]
        assert biz.api_key == data["api_key"]

    def test_public_token_allows_chat_greeting(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        """POST /api/chat/{public_key} successfully returns greeting."""
        payload = {"message": "hello", "customer_name": "Public Visitor"}
        res = client.post(f"/api/chat/{test_business.public_key}", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "conversation_id" in data
        assert data["message"] == test_widget_config.welcome_message
        assert data["confidence_score"] == 1.0

    def test_public_token_allows_chat_rag_query(self, client: TestClient, db: Session, test_business: Business, test_user: User, clean_env, mock_embedding_service, mock_llm_service):
        """POST /api/chat/{public_key} performs RAG query successfully when docs are loaded."""
        doc = Document(
            business_id=test_business.id,
            title="Return Policy Guide",
            file_type="txt",
            file_path="/mock/returns.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        payload = {"message": "What is the return policy?", "customer_name": "Public Visitor"}
        res = client.post(f"/api/chat/{test_business.public_key}", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "conversation_id" in data
        assert data["confidence_score"] > 0.0
        assert len(data["sources"]) > 0

    def test_public_token_allows_widget_embed_config(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        """GET /api/widget/embed/{public_key} successfully returns widget configuration."""
        res = client.get(f"/api/widget/embed/{test_business.public_key}")
        assert res.status_code == 200
        data = res.json()
        assert data["bot_name"] == test_widget_config.bot_name
        assert data["primary_color"] == test_widget_config.primary_color
        assert data["welcome_message"] == test_widget_config.welcome_message

    def test_secret_key_backward_compatibility_on_chat(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        """POST /api/chat/{api_key} continues to function for backward compatibility."""
        payload = {"message": "hi", "customer_name": "Legacy Visitor"}
        res = client.post(f"/api/chat/{test_business.api_key}", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == test_widget_config.welcome_message

    def test_secret_key_backward_compatibility_on_embed(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        """GET /api/widget/embed/{api_key} continues to function for backward compatibility."""
        res = client.get(f"/api/widget/embed/{test_business.api_key}")
        assert res.status_code == 200
        data = res.json()
        assert data["bot_name"] == test_widget_config.bot_name

    def test_invalid_token_returns_404_on_chat(self, client: TestClient):
        """POST /api/chat/{invalid_token} returns HTTP 404 with exact detail 'Invalid API key'."""
        res = client.post("/api/chat/invalid_nonexistent_token_9999", json={"message": "hello"})
        assert res.status_code == 404
        assert res.json()["detail"] == "Invalid API key"

    def test_invalid_token_returns_404_on_embed(self, client: TestClient):
        """GET /api/widget/embed/{invalid_token} returns HTTP 404 with exact detail 'Invalid API key'."""
        res = client.get("/api/widget/embed/invalid_nonexistent_token_9999")
        assert res.status_code == 404
        assert res.json()["detail"] == "Invalid API key"

    def test_public_key_rejected_on_admin_conversations(self, client: TestClient, test_business: Business):
        """GET /api/conversations/{bid} with Bearer {public_key} is rejected with HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/conversations/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_public_key_rejected_on_admin_analytics(self, client: TestClient, test_business: Business):
        """GET /api/analytics/{bid}/dashboard with Bearer {public_key} is rejected with HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/analytics/{test_business.id}/dashboard", headers=headers)
        assert res.status_code == 401

    def test_public_key_rejected_on_admin_team(self, client: TestClient, test_business: Business):
        """GET /api/team/{bid}/members with Bearer {public_key} is rejected with HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/team/{test_business.id}/members", headers=headers)
        assert res.status_code == 401

    def test_public_key_rejected_on_admin_ai_settings(self, client: TestClient, test_business: Business):
        """GET /api/ai-settings/{bid} with Bearer {public_key} is rejected with HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_public_key_rejected_on_admin_widget_config(self, client: TestClient, test_business: Business):
        """GET /api/widget/{bid}/config with Bearer {public_key} is rejected with HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/widget/{test_business.id}/config", headers=headers)
        assert res.status_code == 401

    def test_public_key_rejected_on_admin_knowledge_documents(self, client: TestClient, test_business: Business):
        """GET /api/knowledge/{bid}/documents with Bearer {public_key} is rejected with HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/knowledge/{test_business.id}/documents", headers=headers)
        assert res.status_code == 401

    def test_public_key_rejected_on_admin_faq(self, client: TestClient, test_business: Business):
        """GET /api/faq/{bid} with Bearer {public_key} is rejected with HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/faq/{test_business.id}", headers=headers)
        assert res.status_code == 401
