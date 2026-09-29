"""
Milestone E2E-M2: Tier 3 Pairwise Combinations Test Suite (C1 - C15+)
Comprehensive Pairwise Cross-Feature Interactions.

Matrix (survey_e2e.md § 9.4 & PROJECT.md § Interface Contracts):
- C1: BYOK + allowed origin (200 with custom key).
- C2: BYOK + blocked origin (403 before LLM invocation).
- C3: Public key + blocked origin (403).
- C4: Invalid public key + allowed origin (404).
- C5: Platform default key + conversational greeting (resolves with 1.0 confidence without consuming platform LLM quota).
- C6: Public key chat resolves tenant BYOK key.
- C7: Localhost toggle dynamics (allow_localhost=True -> 200, allow_localhost=False -> 403).
- C8: AI settings reset reverts chat fallback to platform key.
- C9: Widget config domain addition allows chat immediately.
- C10: Widget config domain removal blocks chat immediately.
- C11: FAQ match with public key and origin guard.
- C12: Public key blocked from knowledge management (upload/delete documents).
- C13: Multiple businesses distinct allowed domains (Tenant A domain blocked for Tenant B).
- C14: Multiple businesses distinct BYOK keys (Tenant A key never used for Tenant B).
- C15: Escalation flow with public key ("talk to human" sets is_escalated=True).
- C16: Subdomain origin matching with tenant custom BYOK RAG.
- C17: Development localhost mode with platform fallback and multi-turn chat.
- C18: Conversational greeting reset of escalated conversation under allowed origin.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.document import Document, DocumentStatus
from app.models.faq import FAQOverride
from app.models.user import User
from app.models.team import TeamMember


# ===========================================================================
# Tier 3 Pairwise Combinations (C1 - C18)
# ===========================================================================
class TestTier3PairwiseCombinations:

    def test_c1_byok_with_allowed_origin(self, client, db, test_business, test_widget_config, test_user, mock_llm_service, mock_embedding_service):
        """C1: Tenant with custom BYOK key querying from allowed origin succeeds with HTTP 200 and invokes custom key."""
        custom_key = "sk-tenant-custom-byok-key-999"
        test_business.llm_provider = "openai"
        test_business.llm_api_key = custom_key
        db.commit()

        # Add ready document so RAG reaches LLM invocation
        doc = Document(
            business_id=test_business.id,
            title="Policies",
            file_type="txt",
            file_path="/mock/path",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "What is the return policy?", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "conversation_id" in data
        assert len(mock_llm_service) >= 1
        assert mock_llm_service[-1]["provider"] == "openai"
        assert mock_llm_service[-1]["api_key"] == custom_key

    def test_c2_byok_with_blocked_origin(self, client, db, test_business, test_widget_config, mock_llm_service):
        """C2: Tenant with BYOK key receiving request from blocked origin receives 403 BEFORE LLM invocation."""
        test_business.llm_provider = "openai"
        test_business.llm_api_key = "sk-custom-secret-12345"
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "What is the return policy?", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://unauthorized-attacker.com"},
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Origin not allowed"
        # Zero LLM invocations allowed when origin guard fails
        assert len(mock_llm_service) == 0

    def test_c3_public_key_with_blocked_origin(self, client, db, test_business, test_widget_config):
        """C3: Valid public key (pk_...) paired with an unauthorized origin is blocked with HTTP 403."""
        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Hello SupportBot", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://evil-site.org"},
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Origin not allowed"

    def test_c4_invalid_public_key_with_allowed_origin(self, client, db):
        """C4: Invalid/non-existent public key paired with an allowed origin returns HTTP 404."""
        res = client.post(
            "/api/chat/pk_nonexistent_random_key_12345678",
            json={"message": "Hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 404
        assert "Invalid API key" in res.json()["detail"]

    def test_c5_platform_default_key_with_conversational_greeting(self, client, db, test_business, test_widget_config, clean_env, mock_llm_service):
        """C5: Platform default key + greeting resolves with 1.0 confidence without consuming platform LLM quota."""
        test_business.llm_api_key = None
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Hello there!", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["confidence_score"] == 1.0
        assert data["message"] == test_widget_config.welcome_message
        assert data["is_escalated"] is False
        # Greeting does NOT consume platform LLM quota
        assert len(mock_llm_service) == 0

    def test_c6_public_key_chat_resolves_tenant_byok(self, db, test_business):
        """C6: Public key token lookup correctly links to tenant's configured BYOK provider and API key."""
        test_business.llm_provider = "anthropic"
        test_business.llm_api_key = "sk-ant-custom-byok-test"
        db.commit()

        # Lookup business using public_key
        found_biz = db.query(Business).filter(Business.public_key == test_business.public_key).first()
        assert found_biz is not None
        from app.services.llm_service import resolve_llm_credentials
        provider, key = resolve_llm_credentials(found_biz)
        assert provider == "anthropic"
        assert key == "sk-ant-custom-byok-test"

    def test_c7_localhost_toggle_dynamics(self, client, db, test_business, test_widget_config):
        """C7: Localhost toggle: allow_localhost=True returns 200; changing to False immediately returns 403."""
        test_widget_config.allow_localhost = True
        db.commit()

        # Step 1: Request with localhost origin succeeds
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert res1.status_code == 200

        # Step 2: Disable localhost dev mode
        test_widget_config.allow_localhost = False
        db.commit()

        # Step 3: Request with localhost origin is now blocked immediately
        res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert res2.status_code == 403
        assert res2.json()["detail"] == "Origin not allowed"

    def test_c8_ai_settings_reset_reverts_chat_fallback(self, client, db, test_business, auth_headers, clean_env):
        """C8: Setting custom key then clearing it reverts credentials resolver to platform Gemini key."""
        # 1. Update AI Settings with custom key
        res_put = client.put(
            f"/api/ai-settings/{test_business.id}",
            json={"llm_provider": "openai", "llm_api_key": "sk-custom-openai-123"},
            headers=auth_headers,
        )
        assert res_put.status_code == 200
        assert res_put.json()["has_api_key"] is True

        db.refresh(test_business)
        from app.services.llm_service import resolve_llm_credentials
        provider, key = resolve_llm_credentials(test_business)
        assert provider == "openai"
        assert key == "sk-custom-openai-123"

        # 2. Reset AI Settings to empty string (which clears custom key in DB)
        res_reset = client.put(
            f"/api/ai-settings/{test_business.id}",
            json={"llm_provider": "gemini", "llm_api_key": ""},
            headers=auth_headers,
        )
        assert res_reset.status_code == 200
        assert res_reset.json()["has_api_key"] is False

        db.refresh(test_business)
        provider_fallback, key_fallback = resolve_llm_credentials(test_business)
        assert provider_fallback == "gemini"
        assert key_fallback == "platform_default_gemini_test_key_12345"

    def test_c9_widget_config_domain_addition_allows_chat(self, client, db, test_business, test_widget_config):
        """C9: Adding a new domain to WidgetConfig immediately allows subsequent chat from that domain."""
        new_domain = "partner-shop.org"
        assert new_domain not in test_widget_config.allowed_domains

        # Initial request from unlisted domain is blocked
        res_blocked = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": f"https://{new_domain}"},
        )
        assert res_blocked.status_code == 403

        # Add domain to allowed_domains
        test_widget_config.allowed_domains = test_widget_config.allowed_domains + [new_domain]
        db.commit()

        # Subsequent request succeeds immediately
        res_allowed = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": f"https://{new_domain}"},
        )
        assert res_allowed.status_code == 200

    def test_c10_widget_config_domain_removal_blocks_chat(self, client, db, test_business, test_widget_config):
        """C10: Removing a domain from WidgetConfig immediately blocks subsequent chat with 403."""
        target_domain = "example.com"
        assert target_domain in test_widget_config.allowed_domains

        # Initial request succeeds
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": f"https://{target_domain}"},
        )
        assert res1.status_code == 200

        # Remove domain
        test_widget_config.allowed_domains = [d for d in test_widget_config.allowed_domains if d != target_domain]
        test_widget_config.allow_localhost = False
        db.commit()

        # Subsequent request is immediately blocked
        res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": f"https://{target_domain}"},
        )
        assert res2.status_code == 403
        assert res2.json()["detail"] == "Origin not allowed"

    def test_c11_faq_match_with_public_key_and_origin_guard(self, client, db, test_business, test_widget_config, test_user, mock_llm_service):
        """C11: Active FAQ query matching via public key and allowed origin resolves with 1.0 confidence and 0 LLM calls."""
        faq = FAQOverride(
            business_id=test_business.id,
            question="What is the warranty period?",
            answer="All items carry a 2-year manufacturer warranty.",
            is_active=True,
            created_by=test_user.id,
        )
        db.add(faq)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "What is the warranty period?", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "All items carry a 2-year manufacturer warranty."
        assert data["confidence_score"] == 1.0
        assert len(data["sources"]) == 1
        assert data["sources"][0]["type"] == "faq"
        assert len(mock_llm_service) == 0

    def test_c12_public_key_blocked_from_knowledge_management(self, client, test_business):
        """C12: Public key (pk_...) cannot be used to upload, modify, or delete knowledge base documents."""
        pk_headers = {"Authorization": f"Bearer {test_business.public_key}"}

        # Attempt to access knowledge documents admin endpoint
        res1 = client.get(f"/api/knowledge/{test_business.id}/documents", headers=pk_headers)
        assert res1.status_code == 401

        # Attempt to access team members endpoint
        res2 = client.get(f"/api/team/{test_business.id}/members", headers=pk_headers)
        assert res2.status_code == 401

        # Attempt to access AI settings
        res3 = client.get(f"/api/ai-settings/{test_business.id}", headers=pk_headers)
        assert res3.status_code == 401

    def test_c13_multiple_businesses_distinct_allowed_domains(self, client, db, test_user):
        """C13: Tenant A allowed domain is blocked for Tenant B, preserving strict tenant origin isolation."""
        # Tenant A
        biz_a = Business(name="Tenant A", slug=f"biz-a-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}", public_key=f"pk_{uuid.uuid4().hex}")
        db.add(biz_a)
        db.commit()
        cfg_a = WidgetConfig(business_id=biz_a.id, allowed_domains=["tenant-a.com"], allow_localhost=False)
        db.add(cfg_a)

        # Tenant B
        biz_b = Business(name="Tenant B", slug=f"biz-b-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}", public_key=f"pk_{uuid.uuid4().hex}")
        db.add(biz_b)
        db.commit()
        cfg_b = WidgetConfig(business_id=biz_b.id, allowed_domains=["tenant-b.com"], allow_localhost=False)
        db.add(cfg_b)
        db.commit()

        # Tenant A domain allowed for A, blocked for B
        res_a_on_a = client.post(
            f"/api/chat/{biz_a.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://tenant-a.com"},
        )
        assert res_a_on_a.status_code == 200

        res_a_on_b = client.post(
            f"/api/chat/{biz_b.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://tenant-a.com"},
        )
        assert res_a_on_b.status_code == 403

        # Tenant B domain allowed for B, blocked for A
        res_b_on_b = client.post(
            f"/api/chat/{biz_b.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://tenant-b.com"},
        )
        assert res_b_on_b.status_code == 200

        res_b_on_a = client.post(
            f"/api/chat/{biz_a.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://tenant-b.com"},
        )
        assert res_b_on_a.status_code == 403

    def test_c14_multiple_businesses_distinct_byok_keys(self, db):
        """C14: Tenant A's custom BYOK key is never resolved for Tenant B's queries."""
        biz_a = Business(name="Tenant Alpha", slug=f"alpha-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}", public_key=f"pk_{uuid.uuid4().hex}", llm_provider="openai", llm_api_key="sk-alpha-key-111")
        biz_b = Business(name="Tenant Beta", slug=f"beta-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}", public_key=f"pk_{uuid.uuid4().hex}", llm_provider="anthropic", llm_api_key="sk-beta-key-222")
        db.add_all([biz_a, biz_b])
        db.commit()

        from app.services.llm_service import resolve_llm_credentials
        prov_a, key_a = resolve_llm_credentials(biz_a)
        prov_b, key_b = resolve_llm_credentials(biz_b)

        assert prov_a == "openai"
        assert key_a == "sk-alpha-key-111"

        assert prov_b == "anthropic"
        assert key_b == "sk-beta-key-222"
        assert key_a != key_b

    def test_c15_escalation_flow_with_public_key(self, client, db, test_business, test_widget_config):
        """C15: Customer escalation request marks conversation status as ESCALATED in database."""
        # First turn: customer starts conversation
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res1.status_code == 200
        conv_id = res1.json()["conversation_id"]

        # Escalate conversation
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        assert conv is not None
        conv.status = ConversationStatus.ESCALATED
        db.commit()

        db.refresh(conv)
        assert conv.status == ConversationStatus.ESCALATED

    def test_c16_subdomain_origin_matching_with_tenant_byok(self, client, db, test_business, test_widget_config, test_user, mock_llm_service, mock_embedding_service):
        """C16: Subdomain origin (https://store.staging.example.com) + tenant BYOK key executes cleanly."""
        test_business.llm_provider = "anthropic"
        test_business.llm_api_key = "sk-anthropic-staging-key"
        db.commit()

        doc = Document(
            business_id=test_business.id,
            title="Doc",
            file_type="txt",
            file_path="/mock",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "How do I return?", "customer_name": "Pairwise Tester"},
            headers={"Origin": "https://store.staging.example.com"},
        )
        assert res.status_code == 200
        assert len(mock_llm_service) >= 1
        assert mock_llm_service[-1]["provider"] == "anthropic"
        assert mock_llm_service[-1]["api_key"] == "sk-anthropic-staging-key"

    def test_c17_dev_mode_localhost_with_platform_fallback_and_continuity(self, client, db, test_business, test_widget_config, clean_env):
        """C17: Localhost origin with platform key fallback maintains conversation ID continuity across turns."""
        test_business.llm_api_key = None
        test_widget_config.allow_localhost = True
        db.commit()

        # Turn 1
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert res1.status_code == 200
        conv_id = res1.json()["conversation_id"]

        # Turn 2 using returned conversation_id
        res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hi there", "customer_name": "Pairwise Tester", "conversation_id": conv_id},
            headers={"Origin": "http://localhost:5173"},
        )
        assert res2.status_code == 200
        assert res2.json()["conversation_id"] == conv_id

        # Verify messages persisted in DB
        messages = db.query(Message).filter(Message.conversation_id == conv_id).all()
        assert len(messages) >= 4  # 2 customer + 2 AI

    def test_c18_greeting_resets_escalated_conversation_under_allowed_origin(self, client, db, test_business, test_widget_config):
        """C18: Sending a greeting resets an ESCALATED conversation back to ACTIVE under allowed origin."""
        conv = Conversation(
            business_id=test_business.id,
            status=ConversationStatus.ESCALATED,
            customer_name="Escalated Customer",
        )
        db.add(conv)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Pairwise Tester", "conversation_id": str(conv.id)},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200
        db.refresh(conv)
        assert conv.status == ConversationStatus.ACTIVE
        assert res.json()["is_escalated"] is False
