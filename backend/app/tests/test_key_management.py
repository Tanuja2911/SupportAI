import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.business import Business
from app.core.config import get_settings
from app.services.llm_service import resolve_llm_credentials
from app.services.rag_engine import RAGEngine, LLM_PROVIDERS


class TestKeyManagementResolution:
    def test_resolve_llm_credentials_platform_default(self, clean_env):
        """A tenant without custom key resolves to platform default GEMINI_API_KEY with 'gemini' provider."""
        biz = Business(
            name="Platform Default Corp",
            slug=f"pf-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="gemini",
            llm_api_key=None,
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "platform_default_gemini_test_key_12345"

    def test_resolve_llm_credentials_none_business(self, clean_env):
        """Calling resolve_llm_credentials(None) resolves to platform default GEMINI_API_KEY."""
        provider, key = resolve_llm_credentials(None)
        assert provider == "gemini"
        assert key == "platform_default_gemini_test_key_12345"

    def test_resolve_llm_credentials_tenant_byok_openai_precedence(self, clean_env):
        """A tenant with custom OpenAI key overrides platform default."""
        biz = Business(
            name="BYOK OpenAI Corp",
            slug=f"byok-oa-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="openai",
            llm_api_key="sk-proj-custom-openai-key-999",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "openai"
        assert key == "sk-proj-custom-openai-key-999"

    def test_resolve_llm_credentials_tenant_byok_anthropic(self, clean_env):
        """A tenant with custom Anthropic key resolves correctly."""
        biz = Business(
            name="BYOK Anthropic Corp",
            slug=f"byok-ant-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="anthropic",
            llm_api_key="claude-custom-key-888",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "anthropic"
        assert key == "claude-custom-key-888"

    def test_resolve_llm_credentials_tenant_byok_empty_provider_defaults_to_gemini(self, clean_env):
        """A tenant with custom key and empty provider defaults to 'gemini'."""
        biz = Business(
            name="Custom Key Default Provider",
            slug=f"custom-def-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="",
            llm_api_key="gemini-custom-key-777",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "gemini-custom-key-777"

    def test_resolve_llm_credentials_whitespace_key_falls_back_to_platform(self, clean_env):
        """A tenant with whitespace-only llm_api_key gracefully falls back to platform default key."""
        biz = Business(
            name="Whitespace Key Corp",
            slug=f"ws-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="openai",
            llm_api_key="    \t  \n  ",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "platform_default_gemini_test_key_12345"

    def test_resolve_llm_credentials_empty_key_falls_back_to_platform(self, clean_env):
        """A tenant with empty string llm_api_key gracefully falls back to platform default key."""
        biz = Business(
            name="Empty Key Corp",
            slug=f"empty-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="gemini",
            llm_api_key="",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "platform_default_gemini_test_key_12345"

    def test_resolve_llm_credentials_missing_both_raises_400(self, monkeypatch):
        """When neither tenant nor platform has an API key, raises HTTPException 400."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        biz = Business(
            name="Missing Key Corp",
            slug=f"missing-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="gemini",
            llm_api_key=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            resolve_llm_credentials(biz)
        assert exc_info.value.status_code == 400
        assert "No LLM API key configured" in exc_info.value.detail


class TestAISettingsRouteKeyManagement:
    def test_get_ai_settings_metadata_platform_active(self, client: TestClient, test_business: Business, auth_headers: dict, clean_env):
        """GET /api/ai-settings/{bid} reports platform default is active when no custom key configured."""
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is False
        assert data["is_using_platform_default"] is True
        assert data["llm_provider"] == "gemini"

    def test_get_ai_settings_metadata_custom_key_active(self, client: TestClient, db: Session, test_business: Business, auth_headers: dict, clean_env):
        """GET /api/ai-settings/{bid} reports custom key is active when BYOK key configured."""
        test_business.llm_provider = "openai"
        test_business.llm_api_key = "sk-custom-test-key-123"
        db.commit()
        db.refresh(test_business)

        res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is True
        assert data["is_using_platform_default"] is False
        assert data["llm_provider"] == "openai"

    def test_get_ai_settings_metadata_no_platform_no_custom_key(self, client: TestClient, test_business: Business, auth_headers: dict, monkeypatch):
        """GET /api/ai-settings/{bid} reports neither active when platform key is also absent."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

        res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is False
        assert data["is_using_platform_default"] is False

    def test_put_ai_settings_updates_custom_key(self, client: TestClient, db: Session, test_business: Business, auth_headers: dict, clean_env):
        """PUT /api/ai-settings/{bid} updates provider and custom key."""
        payload = {
            "llm_provider": "anthropic",
            "llm_api_key": "claude-new-key-123",
        }
        res = client.put(f"/api/ai-settings/{test_business.id}", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is True
        assert data["is_using_platform_default"] is False
        assert data["llm_provider"] == "anthropic"

        db.refresh(test_business)
        assert test_business.llm_provider == "anthropic"
        assert test_business.llm_api_key == "claude-new-key-123"

    def test_put_ai_settings_clears_key_reverting_to_platform_default_empty_string(self, client: TestClient, db: Session, test_business: Business, auth_headers: dict, clean_env):
        """PUT /api/ai-settings/{bid} with empty string clears key and reverts to platform default."""
        # Set custom key first
        test_business.llm_api_key = "sk-to-be-cleared"
        db.commit()

        payload = {
            "llm_provider": "gemini",
            "llm_api_key": "",
        }
        res = client.put(f"/api/ai-settings/{test_business.id}", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is False
        assert data["is_using_platform_default"] is True

        db.refresh(test_business)
        assert test_business.llm_api_key is None

    def test_put_ai_settings_clears_key_reverting_to_platform_default_null_key(self, client: TestClient, db: Session, test_business: Business, auth_headers: dict, clean_env):
        """PUT /api/ai-settings/{bid} with None/null clears key and reverts to platform default."""
        test_business.llm_api_key = "sk-to-be-cleared"
        db.commit()

        payload = {
            "llm_provider": "gemini",
            "llm_api_key": None,
        }
        res = client.put(f"/api/ai-settings/{test_business.id}", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is False
        assert data["is_using_platform_default"] is True

        db.refresh(test_business)
        assert test_business.llm_api_key is None

    def test_put_ai_settings_clears_key_reverting_to_platform_default_whitespace_key(self, client: TestClient, db: Session, test_business: Business, auth_headers: dict, clean_env):
        """PUT /api/ai-settings/{bid} with whitespace-only key clears key and reverts to platform default."""
        test_business.llm_api_key = "sk-to-be-cleared"
        db.commit()

        payload = {
            "llm_provider": "gemini",
            "llm_api_key": "     ",
        }
        res = client.put(f"/api/ai-settings/{test_business.id}", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is False
        assert data["is_using_platform_default"] is True

        db.refresh(test_business)
        assert test_business.llm_api_key is None


class TestRAGEngineCredentialIntegration:
    def test_rag_engine_queries_with_platform_fallback(self, clean_env, mock_embedding_service, mock_llm_service, test_business: Business):
        """RAGEngine query succeeds using platform default when tenant key is None."""
        engine = RAGEngine(business=test_business)
        result = engine.query("What is your return policy?")
        assert result["confidence"] > 0.0
        assert "mock Gemini AI response" in result["answer"]

    def test_rag_engine_queries_with_byok_key(self, clean_env, mock_embedding_service, test_business: Business, monkeypatch):
        """RAGEngine query uses tenant custom provider and key."""
        test_business.llm_provider = "openai"
        test_business.llm_api_key = "sk-custom-tenant-key-777"

        recorded = []
        def fake_openai(api_key: str, prompt: str) -> str:
            recorded.append({"provider": "openai", "api_key": api_key})
            return "Answer from custom OpenAI mock."

        monkeypatch.setitem(LLM_PROVIDERS, "openai", fake_openai)

        engine = RAGEngine(business=test_business)
        result = engine.query("What is your return policy?")
        assert result["answer"] == "Answer from custom OpenAI mock."
        assert len(recorded) == 1
        assert recorded[0]["api_key"] == "sk-custom-tenant-key-777"

    def test_rag_engine_missing_all_keys_graceful_fallback(self, monkeypatch, test_business: Business):
        """When neither tenant nor platform has an API key, query returns 0.0 confidence friendly fallback."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

        class DummyEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Return docs", "doc_id": "doc-1", "score": 0.9}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = DummyEmbedding()

        result = engine.query("What is your return policy?")
        assert result["confidence"] == 0.0
        assert "No API key configured" in result["answer"]
