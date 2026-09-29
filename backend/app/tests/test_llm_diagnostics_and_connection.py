import json
import uuid
import time
import httpx
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.user import User, UserRole
from app.models.team import TeamMember
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services import llm_service
from app.services.llm_service import (
    classify_llm_error,
    test_llm_connection as probe_llm_connection,
    resolve_llm_credentials,
    _call_anthropic,
    _call_openai,
    _post_with_retries,
)
from app.services.rag_engine import RAGEngine, LLM_PROVIDERS, _build_bounded_context, _call_gemini, _call_nvidia_nim


class TestLLMErrorClassification:
    """Test exception classification into structured diagnostic categories without credential leakage."""

    def test_classify_invalid_api_key_gemini(self):
        exc = Exception("google.api_core.exceptions.InvalidArgument: 400 API_KEY_INVALID")
        result = classify_llm_error(exc, "gemini")
        assert result["error_code"] == "INVALID_API_KEY"
        assert "invalid or unconfigured API key" in result["user_message"]
        assert "authentication failed" in result["diagnostic"]
        assert "AI Settings" in result["action_hint"]

    def test_classify_invalid_api_key_openai(self):
        exc = Exception("Client error '401 Unauthorized' for url: invalid_api_key")
        result = classify_llm_error(exc, "openai")
        assert result["error_code"] == "INVALID_API_KEY"
        assert "authentication failed" in result["diagnostic"]
        assert "OpenAI" in result["action_hint"]

    def test_classify_quota_exceeded_gemini(self):
        exc = Exception("google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded for quota metric")
        result = classify_llm_error(exc, "gemini")
        assert result["error_code"] == "QUOTA_EXCEEDED"
        assert "usage or billing limit" in result["user_message"]
        assert "429" in result["diagnostic"]

    def test_classify_quota_exceeded_openai(self):
        exc = Exception("Client error '429 Too Many Requests' insufficient_quota")
        result = classify_llm_error(exc, "openai")
        assert result["error_code"] == "QUOTA_EXCEEDED"
        assert "429" in result["diagnostic"]

    def test_classify_temporary_rate_limit_separately_from_quota(self):
        result = classify_llm_error(RuntimeError("Provider API HTTP 429: too many requests"), "openai")
        assert result["error_code"] == "RATE_LIMITED"
        assert "Wait briefly" in result["action_hint"]

    def test_classify_gemini_model_not_found(self):
        result = classify_llm_error(RuntimeError("Gemini API HTTP 404: model not found"), "gemini")
        assert result["error_code"] == "MODEL_NOT_FOUND"
        assert "model is unavailable" in result["user_message"]
        assert "gemini-3.8-flash" in result["action_hint"]

    def test_classify_gemini_project_generation_access_denied(self):
        result = classify_llm_error(
            RuntimeError("Gemini API HTTP 403: Your project has been denied access. Please contact support."),
            "gemini",
            "AIza-secret",
        )
        assert result["error_code"] == "PROVIDER_ACCESS_DENIED"
        assert "denied generation access" in result["user_message"]
        assert "denied access" in result["diagnostic"]
        assert "AIza-secret" not in result["diagnostic"]
        assert "authorization key" in result["action_hint"]

    def test_classify_timeout(self):
        exc = httpx.TimeoutException("ReadTimeout: The read operation timed out after 30 seconds")
        result = classify_llm_error(exc, "gemini")
        assert result["error_code"] == "TIMEOUT"
        assert "timed out" in result["user_message"]
        assert "connection timed out" in result["diagnostic"]

    def test_classify_generic_provider_error_backward_compatibility(self):
        """CRITICAL: For generic exceptions like 503, user_message must match exact legacy fallback string."""
        exc = RuntimeError("Upstream LLM 503 Service Unavailable")
        result = classify_llm_error(exc, "gemini")
        assert result["error_code"] == "PROVIDER_ERROR"
        assert result["user_message"] == "I'm having trouble generating a response right now. Please try again."
        assert "RuntimeError" in result["diagnostic"]

    def test_classify_swapped_arguments(self):
        """Support swapped positional arguments (provider, exception)."""
        exc = RuntimeError("API_KEY_INVALID")
        result = classify_llm_error("openai", exc)
        assert result["error_code"] == "INVALID_API_KEY"

    def test_credential_leakage_prevention(self):
        """Secret key present in exception must NEVER appear in user_message or diagnostic."""
        secret_key = "AIzaSy_SUPER_SECRET_KEY_12345"
        exc = Exception(f"Failed with key {secret_key}: 401 Unauthorized invalid_api_key")
        result = classify_llm_error(exc, "gemini")
        assert secret_key not in result["user_message"]
        assert secret_key not in result["diagnostic"]
        assert secret_key not in (result["action_hint"] or "")


class TestProviderRequestResilience:
    def test_retries_retry_after_and_caps_wait(self, monkeypatch):
        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "90"}
        rate_limited.json.return_value = {"error": {"message": "rate limit"}}
        success = MagicMock()
        success.status_code = 200
        waits = []
        responses = iter([rate_limited, success])
        calls = []

        def mock_post(url, **kwargs):
            calls.append(url)
            return next(responses)

        monkeypatch.setattr(httpx, "post", mock_post)
        monkeypatch.setattr(llm_service.time, "sleep", waits.append)
        result = _post_with_retries("https://provider.test", timeout=httpx.Timeout(5))
        assert result is success
        assert len(calls) == 2
        assert waits == [llm_service.MAX_RETRY_DELAY_SECONDS]

    def test_does_not_retry_exhausted_quota_or_auth_failures(self, monkeypatch):
        for status, message in ((429, "insufficient_quota"), (401, "invalid api key")):
            response = MagicMock()
            response.status_code = status
            response.headers = {}
            response.json.return_value = {"error": {"message": message}}
            calls = []
            monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: calls.append(args[0]) or response)
            result = _post_with_retries("https://provider.test", timeout=httpx.Timeout(5))
            assert result is response
            assert len(calls) == 1

    def test_does_not_retry_ambiguous_read_timeout(self, monkeypatch):
        calls = []

        def timeout_post(*args, **kwargs):
            calls.append(args[0])
            raise httpx.ReadTimeout("provider stopped responding")

        monkeypatch.setattr(httpx, "post", timeout_post)
        with pytest.raises(httpx.ReadTimeout):
            _post_with_retries("https://provider.test", timeout=httpx.Timeout(5))
        assert len(calls) == 1

    def test_bounded_retry_after_parsing(self):
        response = MagicMock()
        response.headers = {"Retry-After": "90"}
        assert llm_service._retry_delay(response, 1) == llm_service.MAX_RETRY_DELAY_SECONDS


class TestGeminiRestCall:
    def test_uses_the_same_stable_model_and_protects_key_in_header(self, monkeypatch):
        def mock_post(url, **kwargs):
            assert url.endswith("/models/gemini-3.8-flash:generateContent")
            assert "AIzaSySecret" not in url
            assert kwargs["headers"]["x-goog-api-key"] == "AIzaSySecret"
            assert kwargs["json"]["systemInstruction"]["parts"]
            response = MagicMock()
            response.is_success = True
            response.json.return_value = {
                "candidates": [{"content": {"parts": [{"text": "A helpful answer."}]}}]
            }
            return response

        monkeypatch.setattr(httpx, "post", mock_post)
        assert _call_gemini("AIzaSySecret", "Question") == "A helpful answer."

    def test_openai_uses_current_fast_model_with_low_reasoning_effort(self, monkeypatch):
        def mock_post(url, **kwargs):
            assert url.endswith("/v1/chat/completions")
            assert kwargs["json"]["model"] == "gpt-6-luna"
            assert kwargs["json"]["reasoning_effort"] == "none"
            response = MagicMock()
            response.is_success = True
            response.json.return_value = {"choices": [{"message": {"content": "OpenAI answer"}}]}
            return response

        monkeypatch.setattr(httpx, "post", mock_post)
        assert _call_openai("sk-test", "Question") == "OpenAI answer"

    def test_anthropic_disables_adaptive_thinking_for_support_latency(self, monkeypatch):
        def mock_post(url, **kwargs):
            assert kwargs["json"]["model"] == "claude-sonnet-5"
            assert kwargs["json"]["thinking"] == {"type": "disabled"}
            response = MagicMock()
            response.is_success = True
            response.json.return_value = {"content": [{"type": "text", "text": "Anthropic answer"}]}
            return response

        monkeypatch.setattr(httpx, "post", mock_post)
        assert _call_anthropic("sk-test", "Question") == "Anthropic answer"

    def test_nvidia_reasoning_text_is_never_returned_as_customer_answer(self, monkeypatch):
        response = MagicMock()
        response.is_success = True
        response.json.return_value = {
            "choices": [{"message": {"content": "", "reasoning_content": "private reasoning"}}]
        }
        monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response)
        with pytest.raises(RuntimeError, match="did not include generated text") as error:
            _call_nvidia_nim("nvapi-test", "Question")
        assert "private reasoning" not in str(error.value)

    def test_nvidia_nim_uses_openai_compatible_chat_completion(self, monkeypatch):
        def mock_post(url, **kwargs):
            assert url == "https://integrate.api.nvidia.com/v1/chat/completions"
            assert kwargs["headers"]["Authorization"] == "Bearer nvapi-secret-test"
            assert kwargs["json"]["model"] == "openai/gpt-oss-20b"
            assert kwargs["json"]["temperature"] == 1
            assert kwargs["json"]["top_p"] == 1
            assert kwargs["json"]["max_tokens"] == 4096
            assert kwargs["json"]["stream"] is False
            response = MagicMock()
            response.status_code = 200
            response.is_success = True
            response.json.return_value = {"choices": [{"message": {"content": "NIM response"}}]}
            return response

        monkeypatch.setattr(httpx, "post", mock_post)
        assert _call_nvidia_nim("nvapi-secret-test", "Question") == "NIM response"


class TestRAGContextBounds:
    def test_context_is_capped_before_provider_generation(self):
        context = _build_bounded_context([{"chunk": "x" * (llm_service.MAX_PROVIDER_ATTEMPTS * 10000)}])
        assert len(context) <= 24_000

    def test_multiple_chunks_reserve_space_for_separators(self):
        context = _build_bounded_context([{"chunk": "a" * 15000}, {"chunk": "b" * 15000}])
        assert len(context) <= 24_000
        assert "\n\n---\n\n" in context


class TestLLMConnectionProbe:
    """Test minimal live completions, provider access, and credential handling."""

    def test_gemini_connection_success(self, monkeypatch):
        def mock_post(url, **kwargs):
            assert "generativelanguage.googleapis.com" in url
            assert url.endswith("/models/gemini-3.8-flash:generateContent")
            assert kwargs.get("headers", {}).get("x-goog-api-key") == "AIzaSyValidGeminiKey"
            assert kwargs["json"]["generationConfig"]["maxOutputTokens"] <= 2
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="gemini", api_key="AIzaSyValidGeminiKey")
        assert res["status"] == "connected"
        assert res["provider"] == "gemini"
        assert res["model"] == "gemini-3.8-flash"
        assert res["latency_ms"] is not None and res["latency_ms"] >= 1
        assert res["diagnostic"] is None
        assert "generated a test response" in res["message"]

    def test_gemini_connection_invalid_key_400(self, monkeypatch):
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.json.return_value = {"error": {"message": "API key not valid", "status": "INVALID_ARGUMENT"}}
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="gemini", api_key="AIzaSyBadKey")
        assert res["status"] == "error"
        assert res["provider"] == "gemini"
        assert res["model"] is None
        assert "API_KEY_INVALID" in res["diagnostic"]
        assert res["action_hint"] is not None

    def test_gemini_connection_invalid_key_403(self, monkeypatch):
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="gemini", api_key="AIzaSyForbiddenKey")
        assert res["status"] == "error"
        assert res["error_code"] == "PROVIDER_ACCESS_DENIED"
        assert "denied generation access" in res["message"]

    def test_gemini_connection_quota_exceeded_429(self, monkeypatch):
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="gemini", api_key="AIzaSyQuotaKey")
        assert res["status"] == "error"
        assert "429" in res["diagnostic"]
        assert res["error_code"] == "RATE_LIMITED"

    def test_nvidia_nim_connection_runs_a_tiny_generation(self, monkeypatch):
        def mock_post(url, **kwargs):
            assert url == "https://integrate.api.nvidia.com/v1/chat/completions"
            assert kwargs["headers"]["Authorization"] == "Bearer nvapi-valid-key"
            assert kwargs["json"]["model"] == "openai/gpt-oss-20b"
            assert kwargs["json"]["max_tokens"] <= 16
            assert kwargs["json"]["temperature"] == 1
            assert kwargs["json"]["top_p"] == 1
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
            return response

        monkeypatch.setattr(httpx, "post", mock_post)
        result = probe_llm_connection("nvidia_nim", "nvapi-valid-key")
        assert result["status"] == "connected"
        assert result["provider"] == "nvidia_nim"
        assert result["model"] == "openai/gpt-oss-20b"

    def test_openai_connection_success(self, monkeypatch):
        def mock_post(url, **kwargs):
            assert "api.openai.com" in url
            assert kwargs.get("headers", {}).get("Authorization") == "Bearer sk-valid-openai"
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="openai", api_key="sk-valid-openai")
        assert res["status"] == "connected"
        assert res["provider"] == "openai"
        assert res["model"] == "gpt-6-luna"
        assert res["latency_ms"] is not None and res["latency_ms"] >= 1
        assert "Successfully" in res["message"]

    def test_openai_connection_invalid_key_401(self, monkeypatch):
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="openai", api_key="sk-bad-openai")
        assert res["status"] == "error"
        assert res["provider"] == "openai"
        assert "401" in res["diagnostic"]
        assert "platform.openai.com" in res["action_hint"]

    def test_openai_connection_quota_exceeded_429(self, monkeypatch):
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="openai", api_key="sk-quota-openai")
        assert res["status"] == "error"
        assert "429" in res["diagnostic"]

    def test_connection_network_timeout(self, monkeypatch):
        def mock_post(url, **kwargs):
            raise httpx.TimeoutException("Read timeout on connection")

        monkeypatch.setattr(httpx, "post", mock_post)

        res = probe_llm_connection(provider="gemini", api_key="AIzaSyTimeoutKey")
        assert res["status"] == "error"
        assert "timed out" in res["message"].lower()

    def test_connection_empty_key(self):
        res = probe_llm_connection(provider="gemini", api_key="")
        assert res["status"] == "error"
        assert "missing or empty" in res["diagnostic"].lower()

    def test_connection_unsupported_provider(self):
        res = probe_llm_connection(provider="invalid_provider_xyz", api_key="key123")
        assert res["status"] == "error"
        assert "not supported" in res["diagnostic"].lower()


class TestAISettingsConnectionRoutes:
    """Test POST /api/ai-settings/test-connection and POST /api/ai-settings/{bid}/test-connection endpoints."""

    def test_route_candidate_key_gemini_success(self, client: TestClient, auth_headers: dict, monkeypatch):
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        resp = client.post(
            "/api/ai-settings/test-connection",
            json={"provider": "gemini", "api_key": "AIzaCandidateKey123"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "connected"
        assert data["provider"] == "gemini"
        assert data["model"] == "gemini-3.8-flash"
        assert data["latency_ms"] >= 1

    def test_route_business_candidate_key_openai_invalid(
        self, client: TestClient, auth_headers: dict, test_business: Business, monkeypatch
    ):
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        resp = client.post(
            f"/api/ai-settings/{test_business.id}/test-connection",
            json={"provider": "openai", "api_key": "sk-bad-candidate"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert data["provider"] == "openai"
        assert "401" in data["diagnostic"]
        assert "sk-bad-candidate" not in data["diagnostic"]

    def test_route_resolves_active_saved_byok_key(
        self, client: TestClient, auth_headers: dict, test_business: Business, db: Session, monkeypatch
    ):
        test_business.llm_provider = "openai"
        test_business.llm_api_key = "sk-saved-byok-key-999"
        db.commit()

        captured_headers = {}

        def mock_post(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"choices": [{"message": {"content": "OK"}}]}
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        resp = client.post(
            f"/api/ai-settings/{test_business.id}/test-connection",
            json={"provider": "gemini"},  # No api_key, should resolve business BYOK openai key
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "connected"
        assert data["provider"] == "openai"
        assert captured_headers.get("Authorization") == "Bearer sk-saved-byok-key-999"
        assert data["is_platform_default"] is False

    def test_route_resolves_platform_fallback_key(
        self, client: TestClient, auth_headers: dict, test_business: Business, db: Session, clean_env, monkeypatch
    ):
        test_business.llm_api_key = None
        db.commit()

        captured_headers = {}

        def mock_post(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}
            return mock_resp

        monkeypatch.setattr(httpx, "post", mock_post)

        resp = client.post(
            f"/api/ai-settings/{test_business.id}/test-connection",
            json={},  # No api_key, should resolve platform default
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "connected"
        assert data["provider"] == "gemini"
        assert captured_headers.get("x-goog-api-key") == "platform_default_gemini_test_key_12345"
        assert data["is_platform_default"] is True

    def test_nvidia_nim_provider_can_be_saved_and_resolved(
        self, client: TestClient, auth_headers: dict, test_business: Business, db: Session
    ):
        response = client.put(
            f"/api/ai-settings/{test_business.id}",
            json={"llm_provider": "nvidia_nim", "llm_api_key": "nvapi-example-key"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["llm_provider"] == "nvidia_nim"
        db.refresh(test_business)
        assert resolve_llm_credentials(test_business) == ("nvidia_nim", "nvapi-example-key")

    def test_route_unauthorized_permission_check(self, client: TestClient, auth_headers: dict, db: Session):
        other_biz = Business(
            name="Other Tenant Org",
            slug=f"other-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
        )
        db.add(other_biz)
        db.commit()

        resp = client.post(
            f"/api/ai-settings/{other_biz.id}/test-connection",
            json={"provider": "gemini", "api_key": "AIzaSomeKey"},
            headers=auth_headers,
        )
        assert resp.status_code == 403
        assert "Not a team member" in resp.json()["detail"]


class TestChatDiagnosticsAndBackwardCompatibility:
    """Test RAG diagnostic propagation in chat route and legacy backward compatibility."""

    def test_chat_route_propagates_rag_diagnostics_on_invalid_key(
        self, client: TestClient, test_user: User, test_business: Business, db: Session, monkeypatch
    ):
        # Seed a ready document so RAG execution is reached
        doc = Document(
            business_id=test_business.id,
            title="Shipping Guide",
            file_type="txt",
            uploaded_by=test_user.id,
            status=DocumentStatus.READY,
        )
        db.add(doc)
        db.commit()

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Standard delivery takes 3-5 days.", "doc_id": "doc-shipping-1", "score": 0.85}]

        monkeypatch.setattr("app.services.rag_engine.EmbeddingService", lambda: MockEmbeddingWithDocs())

        # Exploding LLM provider with invalid API key
        def exploding_provider(api_key: str, prompt: str):
            raise Exception("google.api_core.exceptions.InvalidArgument: 400 API_KEY_INVALID")

        monkeypatch.setitem(LLM_PROVIDERS, "gemini", exploding_provider)

        resp = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "How long does shipping take?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["error_code"] == "INVALID_API_KEY"
        assert "authentication failed" in data["diagnostic"]
        assert "invalid or unconfigured API key" in data["message"]
        assert len(data["sources"]) == 1
        assert data["sources"][0]["doc_id"] == "doc-shipping-1"
        assert "relevance" in data["sources"][0]
        assert "preview" in data["sources"][0]

    def test_chat_route_greeting_preserves_clean_contract_with_no_diagnostics(
        self, client: TestClient, test_business: Business
    ):
        resp = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Hi, how are you today?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["confidence_score"] == 1.0
        assert data["is_escalated"] is False
        assert data["sources"] == []
        assert data["error_code"] is None
        assert data["diagnostic"] is None

    def test_rag_engine_dispatches_nvidia_nim_for_business_provider(self, test_business: Business, monkeypatch):
        test_business.llm_provider = "nvidia_nim"
        test_business.llm_api_key = "nvapi-test-key"
        captured = {}

        def nvidia_provider(api_key: str, prompt: str):
            captured["key"] = api_key
            captured["prompt"] = prompt
            return "Answer from NVIDIA NIM."

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Unit 1 covers introductory topics.", "doc_id": "doc-unit-1", "score": 0.8}]

        monkeypatch.setitem(LLM_PROVIDERS, "nvidia_nim", nvidia_provider)
        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()
        result = engine.query("What does Unit 1 cover?")

        assert result["answer"] == "Answer from NVIDIA NIM."
        assert captured["key"] == "nvapi-test-key"
        assert "Unit 1 covers introductory topics." in captured["prompt"]

    def test_rag_engine_generic_error_backward_compatibility(self, test_business: Business, monkeypatch):
        """Confirm generic RuntimeError produces exact legacy fallback string."""
        def exploding_provider(api_key: str, prompt: str):
            raise RuntimeError("Upstream LLM 503 Service Unavailable")

        monkeypatch.setitem(LLM_PROVIDERS, "gemini", exploding_provider)

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Doc chunk", "doc_id": "doc-1", "score": 0.9}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("Will you crash?")
        assert res["answer"] == "I'm having trouble generating a response right now. Please try again."
        assert res["confidence"] == 0.0
        assert res["error_code"] == "PROVIDER_ERROR"
        assert "RuntimeError" in res["diagnostic"]
