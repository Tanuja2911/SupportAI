import uuid
import pytest
import concurrent.futures
from fastapi import HTTPException

from app.models.business import Business
from app.core.config import get_settings
from app.services.llm_service import resolve_llm_credentials
from app.services.rag_engine import RAGEngine, LLM_PROVIDERS


class TestAdversarialLLMResolution:
    """Aggressive boundary and stress tests for resolve_llm_credentials."""

    @pytest.mark.parametrize(
        "whitespace_key",
        [
            " ",
            "\t",
            "\n",
            "\r",
            "\n\r",
            "\r\n",
            " \t\n ",
            "   \t\t   \r\n\r\n   ",
            "\v\f",
            "  \t  \v  \f  \r  \n  ",
        ],
    )
    def test_whitespace_key_permutations_fallback_to_platform(self, clean_env, whitespace_key):
        """Every whitespace permutation in tenant key must trigger platform fallback with 'gemini'."""
        biz = Business(
            name="Whitespace Tenant",
            slug=f"ws-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="openai",
            llm_api_key=whitespace_key,
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini", f"Expected provider 'gemini', got '{provider}' for key repr {repr(whitespace_key)}"
        assert key == "platform_default_gemini_test_key_12345"

    @pytest.mark.parametrize(
        "raw_key,expected_key",
        [
            ("  key123  ", "key123"),
            ("\t\tsk-custom-openai-key-abc\n\n", "sk-custom-openai-key-abc"),
            ("\r\n  claude-ant-xyz-789  \r\n", "claude-ant-xyz-789"),
            ("   sk-single   ", "sk-single"),
            ("   a   ", "a"),
            ("\t  embedded-dashes-and_underscores-999  \t", "embedded-dashes-and_underscores-999"),
        ],
    )
    def test_leading_trailing_whitespace_stripped(self, clean_env, raw_key, expected_key):
        """Keys with surrounding whitespace must be returned stripped."""
        biz = Business(
            name="Padded Key Tenant",
            slug=f"pad-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="openai",
            llm_api_key=raw_key,
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "openai"
        assert key == expected_key

    @pytest.mark.parametrize(
        "tenant_provider,empty_key",
        [
            ("openai", ""),
            ("openai", "   "),
            ("openai", None),
            ("anthropic", ""),
            ("anthropic", "\t\n\r"),
            ("anthropic", None),
            ("custom-provider-x", ""),
            ("custom-provider-x", "     "),
        ],
    )
    def test_multi_provider_with_empty_key_falls_back_to_platform_gemini(
        self, clean_env, tenant_provider, empty_key
    ):
        """When tenant selects openai or anthropic but supplies no valid key,
        provider must fall back to 'gemini' and use platform GEMINI_API_KEY.
        (Cross-provider mismatch must be avoided)."""
        biz = Business(
            name="Empty Key Non-Gemini Tenant",
            slug=f"non-gem-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider=tenant_provider,
            llm_api_key=empty_key,
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini", f"Expected provider fallback to 'gemini', got '{provider}'"
        assert key == "platform_default_gemini_test_key_12345"

    @pytest.mark.parametrize(
        "empty_provider",
        [
            "",
            "   ",
            "\t\n",
            None,
        ],
    )
    def test_empty_or_whitespace_provider_defaults_to_gemini(self, clean_env, empty_provider):
        """When tenant provides a valid key but empty/whitespace/None provider, provider defaults to 'gemini'."""
        biz = Business(
            name="Blank Provider Tenant",
            slug=f"blank-p-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider=empty_provider,
            llm_api_key="valid-tenant-key-1234",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "valid-tenant-key-1234"

    @pytest.mark.parametrize(
        "padded_provider,expected_provider",
        [
            ("  openai  ", "openai"),
            ("\tanthropic\n", "anthropic"),
            ("  gemini  ", "gemini"),
        ],
    )
    def test_provider_with_whitespace_is_stripped(self, clean_env, padded_provider, expected_provider):
        """Surrounding whitespace on provider name should be stripped."""
        biz = Business(
            name="Padded Provider Tenant",
            slug=f"pad-p-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider=padded_provider,
            llm_api_key="valid-tenant-key-5678",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == expected_provider
        assert key == "valid-tenant-key-5678"

    @pytest.mark.parametrize(
        "tenant_key,platform_key",
        [
            (None, ""),
            ("", ""),
            ("   ", ""),
            ("\t\n\r", "   "),
            (None, "   \t\n  "),
            ("", None),
            (None, None),
            ("   \t ", None),
        ],
    )
    def test_both_keys_missing_or_whitespace_raises_http_400(self, monkeypatch, tenant_key, platform_key):
        """When neither tenant nor platform provides a valid key, HTTPException 400 is strictly raised."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", platform_key)

        biz = Business(
            name="No Key Tenant",
            slug=f"nokey-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="gemini",
            llm_api_key=tenant_key,
        )

        with pytest.raises(HTTPException) as exc_info:
            resolve_llm_credentials(biz)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No LLM API key configured."

    def test_none_business_missing_platform_key_raises_http_400(self, monkeypatch):
        """Calling resolve_llm_credentials(None) with missing platform key raises HTTPException 400."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

        with pytest.raises(HTTPException) as exc_info:
            resolve_llm_credentials(None)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No LLM API key configured."

    def test_platform_key_with_leading_trailing_whitespace_is_stripped(self, monkeypatch):
        """When platform key has whitespace around it, it is stripped before returning."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "   platform-key-with-spaces   \n")

        provider, key = resolve_llm_credentials(None)
        assert provider == "gemini"
        assert key == "platform-key-with-spaces"


class TestAdversarialRAGEngineBehavior:
    """Stress testing RAGEngine.query() key resolution, error shielding, and invocation contracts."""

    def test_rag_query_when_no_key_exists_returns_confidence_zero_and_fallback(
        self, monkeypatch, test_business: Business
    ):
        """RAGEngine.query() when no key is configured anywhere returns confidence: 0.0,
        empty sources, and graceful fallback message without crashing or raising unhandled exception."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

        test_business.llm_api_key = None

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Refund doc chunk", "doc_id": "doc-refund", "score": 0.95}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("How do I get a refund?")

        assert isinstance(res, dict)
        assert res["confidence"] == 0.0
        assert res["sources"] == []
        assert "No API key configured" in res["answer"]
        assert "Please add your LLM API key in AI Settings" in res["answer"]

    def test_rag_query_when_tenant_key_is_whitespace_and_platform_empty(
        self, monkeypatch, test_business: Business
    ):
        """RAGEngine.query() with whitespace tenant key and empty platform key gracefully returns fallback."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "   \t\n  ")
        test_business.llm_api_key = "   \t  "

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Pricing doc chunk", "doc_id": "doc-pricing", "score": 0.88}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("What is your price?")

        assert res["confidence"] == 0.0
        assert res["sources"] == []
        assert "No API key configured" in res["answer"]

    def test_mock_llm_receives_exact_stripped_key_and_resolved_provider_openai(
        self, clean_env, test_business: Business, monkeypatch
    ):
        """Verify mock LLM dispatch receives the exact stripped key and resolved provider for OpenAI."""
        test_business.llm_provider = "  openai  "
        test_business.llm_api_key = "  sk-adversarial-test-key-12345  \n"

        calls = []

        def mock_openai(api_key: str, prompt: str) -> str:
            calls.append({"provider": "openai", "api_key": api_key, "prompt": prompt})
            return "Adversarial OpenAI response."

        monkeypatch.setitem(LLM_PROVIDERS, "openai", mock_openai)

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Shipping takes 2 days", "doc_id": "doc-ship", "score": 0.90}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("When will my package arrive?")

        assert len(calls) == 1
        assert calls[0]["provider"] == "openai"
        assert calls[0]["api_key"] == "sk-adversarial-test-key-12345"  # Exact stripped key
        assert "Shipping takes 2 days" in calls[0]["prompt"]
        assert res["answer"] == "Adversarial OpenAI response."
        assert res["confidence"] > 0.0

    def test_mock_llm_receives_exact_stripped_key_and_resolved_provider_anthropic(
        self, clean_env, test_business: Business, monkeypatch
    ):
        """Verify mock LLM dispatch receives exact stripped key and resolved provider for Anthropic."""
        test_business.llm_provider = "anthropic"
        test_business.llm_api_key = "\tclaude-custom-key-secret-999\r\n"

        calls = []

        def mock_anthropic(api_key: str, prompt: str) -> str:
            calls.append({"provider": "anthropic", "api_key": api_key, "prompt": prompt})
            return "Adversarial Anthropic response."

        monkeypatch.setitem(LLM_PROVIDERS, "anthropic", mock_anthropic)

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Support hours 9-5", "doc_id": "doc-hours", "score": 0.85}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("What are your hours?")

        assert len(calls) == 1
        assert calls[0]["provider"] == "anthropic"
        assert calls[0]["api_key"] == "claude-custom-key-secret-999"
        assert res["answer"] == "Adversarial Anthropic response."

    def test_mock_llm_receives_stripped_platform_key_when_tenant_key_empty(
        self, monkeypatch, test_business: Business
    ):
        """When tenant has empty key, mock Gemini receives stripped platform key."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "  platform-gemini-secret-555  ")
        test_business.llm_provider = "openai"  # tenant had set openai, but key is empty
        test_business.llm_api_key = "   "

        calls = []

        def mock_gemini(api_key: str, prompt: str) -> str:
            calls.append({"provider": "gemini", "api_key": api_key, "prompt": prompt})
            return "Adversarial Gemini platform response."

        monkeypatch.setitem(LLM_PROVIDERS, "gemini", mock_gemini)

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Account policy info", "doc_id": "doc-account", "score": 0.8}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("How to reset password?")

        assert len(calls) == 1
        assert calls[0]["provider"] == "gemini"
        assert calls[0]["api_key"] == "platform-gemini-secret-555"
        assert res["answer"] == "Adversarial Gemini platform response."

    def test_rag_engine_legacy_constructor_resolution(self, clean_env, monkeypatch):
        """Verify RAGEngine instantiated with legacy kwargs (business_id, llm_provider, llm_api_key, business=None)
        correctly resolves credentials and runs query."""
        calls = []

        def mock_openai(api_key: str, prompt: str) -> str:
            calls.append({"provider": "openai", "api_key": api_key})
            return "Legacy constructor response."

        monkeypatch.setitem(LLM_PROVIDERS, "openai", mock_openai)

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Legacy knowledge chunk", "doc_id": "doc-leg", "score": 0.85}]

        engine = RAGEngine(
            business_id="leg-biz-123",
            llm_provider="openai",
            llm_api_key="  sk-legacy-key-777  ",
            business=None,
        )
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("Legacy question?")

        assert len(calls) == 1
        assert calls[0]["provider"] == "openai"
        assert calls[0]["api_key"] == "sk-legacy-key-777"
        assert res["answer"] == "Legacy constructor response."

    def test_rag_engine_handles_llm_provider_exception_without_crashing(
        self, clean_env, test_business: Business, monkeypatch
    ):
        """When the LLM provider call raises an unexpected exception (e.g. rate limit, connection drop),
        RAGEngine catches it and returns friendly error message."""
        test_business.llm_provider = "gemini"
        test_business.llm_api_key = "gem-valid-key"

        def exploding_gemini(api_key: str, prompt: str):
            raise RuntimeError("Upstream LLM 503 Service Unavailable")

        monkeypatch.setitem(LLM_PROVIDERS, "gemini", exploding_gemini)

        class MockEmbeddingWithDocs:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Doc chunk", "doc_id": "doc-1", "score": 0.9}]

        engine = RAGEngine(business=test_business)
        engine.embedding_service = MockEmbeddingWithDocs()

        res = engine.query("Will you crash?")

        assert res["answer"] == "I'm having trouble generating a response right now. Please try again."
        assert res["confidence"] == 0.0


class TestAdversarialConcurrencyStability:
    """Stress test multi-threaded concurrent resolution to ensure thread safety and no cross-talk."""

    def test_concurrent_resolution_stability_multi_tenant(self, clean_env):
        """50 concurrent threads resolving credentials across diverse tenants simultaneously.
        Must produce deterministic, isolated results with zero cross-talk or race conditions."""
        tenants = [
            # (business_instance, expected_provider, expected_key)
            (
                Business(llm_provider="openai", llm_api_key=f"sk-openai-{i}"),
                "openai",
                f"sk-openai-{i}",
            )
            for i in range(10)
        ] + [
            (
                Business(llm_provider="anthropic", llm_api_key=f"  claude-ant-{i}  "),
                "anthropic",
                f"claude-ant-{i}",
            )
            for i in range(10)
        ] + [
            (
                Business(llm_provider="gemini", llm_api_key=f"\tgemini-custom-{i}\n"),
                "gemini",
                f"gemini-custom-{i}",
            )
            for i in range(10)
        ] + [
            # Empty key falling back to platform
            (
                Business(llm_provider="openai", llm_api_key="   "),
                "gemini",
                "platform_default_gemini_test_key_12345",
            )
            for _ in range(10)
        ] + [
            # None business falling back to platform
            (
                None,
                "gemini",
                "platform_default_gemini_test_key_12345",
            )
            for _ in range(10)
        ]

        def resolve_worker(item):
            biz, exp_provider, exp_key = item
            actual_provider, actual_key = resolve_llm_credentials(biz)
            return (actual_provider == exp_provider, actual_key == exp_key, actual_provider, actual_key)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(resolve_worker, t) for t in tenants]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        for prov_ok, key_ok, act_prov, act_key in results:
            assert prov_ok is True, f"Concurrent resolution returned unexpected provider: {act_prov}"
            assert key_ok is True, f"Concurrent resolution returned unexpected key: {act_key}"

    def test_concurrent_rag_query_stability(self, clean_env, monkeypatch):
        """Multiple concurrent threads querying RAGEngine concurrently."""
        def mock_gemini(api_key: str, prompt: str) -> str:
            return f"Answer for prompt hash {len(prompt)}"

        def mock_openai(api_key: str, prompt: str) -> str:
            return f"Answer for prompt hash {len(prompt)}"

        monkeypatch.setitem(LLM_PROVIDERS, "gemini", mock_gemini)
        monkeypatch.setitem(LLM_PROVIDERS, "openai", mock_openai)

        class SharedEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": f"Context for {query}", "doc_id": "doc-test", "score": 0.8}]

        embedding = SharedEmbedding()

        def query_worker(i):
            biz = Business(
                id=uuid.uuid4(),
                llm_provider="openai" if i % 2 == 0 else "gemini",
                llm_api_key=f"key-{i}",
            )
            engine = RAGEngine(business=biz)
            engine.embedding_service = embedding
            return engine.query(f"Question number {i}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(query_worker, i) for i in range(30)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 30
        for r in results:
            assert r["confidence"] > 0.0
            assert "Answer for prompt hash" in r["answer"]


class TestAdversarialRouteIntegration:
    """End-to-end HTTP integration tests for routes relying on LLM resolution."""

    def test_chat_endpoint_graceful_fallback_when_no_llm_key_configured(
        self, client, db, test_business: Business, test_user, monkeypatch, mock_embedding_service
    ):
        """When documents exist but no LLM key is configured (tenant or platform),
        POST /api/chat/{public_key} must NOT 500 or crash; it must return 200 with
        confidence 0.0 and escalation triggered."""
        from app.models.document import Document, DocumentStatus
        from app.core.security import create_access_token

        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        test_business.llm_api_key = None
        db.commit()

        # Add a ready document so RAG branch is entered
        doc = Document(
            business_id=test_business.id,
            title="Adversarial Test Doc",
            file_type="txt",
            file_path="/mock/adv.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        payload = {"message": "What is the return policy?", "customer_name": "Test Customer"}
        res = client.post(f"/api/chat/{test_business.public_key}", json=payload)

        assert res.status_code == 200
        data = res.json()
        assert data["confidence_score"] == 0.0
        assert data["is_escalated"] is False
        assert "No API key configured" in data["message"]

    def test_chat_endpoint_strips_padded_byok_key(
        self, client, db, test_business: Business, test_user, clean_env, monkeypatch, mock_embedding_service
    ):
        """When tenant configured BYOK key with leading/trailing spaces,
        POST /api/chat/{public_key} invokes the LLM provider with stripped key."""
        from app.models.document import Document, DocumentStatus

        test_business.llm_provider = "openai"
        test_business.llm_api_key = "   sk-padded-byok-secret-key   \n"
        db.commit()

        doc = Document(
            business_id=test_business.id,
            title="Adversarial Test Doc 2",
            file_type="txt",
            file_path="/mock/adv2.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        recorded = []

        def mock_openai(api_key: str, prompt: str) -> str:
            recorded.append({"provider": "openai", "api_key": api_key})
            return "Stripped key OpenAI response."

        monkeypatch.setitem(LLM_PROVIDERS, "openai", mock_openai)

        payload = {"message": "What is the return policy?", "customer_name": "Test Customer"}
        res = client.post(f"/api/chat/{test_business.public_key}", json=payload)

        assert res.status_code == 200
        assert len(recorded) == 1
        assert recorded[0]["api_key"] == "sk-padded-byok-secret-key"
        assert res.json()["message"] == "Stripped key OpenAI response."

    def test_faq_generate_endpoint_raises_400_when_no_llm_key(
        self, client, db, test_business: Business, test_user, test_team_member, monkeypatch
    ):
        """POST /api/faq/{bid}/auto-generate returns HTTP 400 with detail 'No LLM API key configured.'
        when neither tenant nor platform has an API key."""
        from app.core.security import create_access_token
        from app.models.document import Document, DocumentChunk, DocumentStatus

        token = create_access_token({"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        test_business.llm_api_key = None
        db.commit()

        doc = Document(
            business_id=test_business.id,
            title="FAQ Source Doc",
            file_type="txt",
            file_path="/mock/faq.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.flush()

        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            content="Documentation content for generating FAQs about our products and return policies.",
        )
        db.add(chunk)
        db.commit()

        res = client.post(f"/api/faq/{test_business.id}/auto-generate", headers=headers)
        assert res.status_code == 400
        assert res.json()["detail"] == "No LLM API key configured."

    def test_knowledge_gaps_detect_endpoint_raises_400_when_no_llm_key(
        self, client, db, test_business: Business, test_user, test_team_member, monkeypatch
    ):
        """POST /api/knowledge-gaps/{bid}/analyze returns HTTP 400 with detail 'No LLM API key configured.'
        when neither tenant nor platform has an API key."""
        from app.core.security import create_access_token
        from app.models.conversation import Conversation, Message, MessageSender, ConversationStatus

        token = create_access_token({"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        test_business.llm_api_key = None
        db.commit()

        # Add an escalated conversation with customer message
        conv = Conversation(business_id=test_business.id, status=ConversationStatus.ESCALATED)
        db.add(conv)
        db.flush()
        msg = Message(conversation_id=conv.id, sender=MessageSender.CUSTOMER, content="Can I cancel anytime?")
        db.add(msg)
        db.commit()

        res = client.post(f"/api/knowledge-gaps/{test_business.id}/analyze", headers=headers)
        assert res.status_code == 400
        assert res.json()["detail"] == "No LLM API key configured."
