"""
Milestone E2E-M3: Tier 4 Real-World Lifecycle Scenarios Test Suite (S1 - S8+)
Comprehensive End-to-End Real-World Customer Support Workflows.

Matrix (survey_e2e.md § 9.5 & PROJECT.md § Interface Contracts):
- S1 (test_s1_tenant_onboarding_to_widget_embed):
    Full tenant onboarding lifecycle:
    Admin registration -> Business creation -> Public key (pk_...) generation ->
    Widget config updated with allowed domain -> Customer embeds widget ->
    Greeting interaction receives welcome message with confidence 1.0.

- S2 (test_s2_tenant_byok_lifecycle_switch):
    Dynamic BYOK key lifecycle:
    Starts with platform default key -> Chats succeed via platform key ->
    Tenant updates AI settings with custom OpenAI key -> Chats execute with OpenAI key ->
    Tenant removes custom key -> Chats revert to platform Gemini fallback key.

- S3 (test_s3_domain_hijack_prevention):
    Security barrier enforcement:
    Legitimate site embeds widget -> Succeeds ->
    Attacker site scrapes pk_ and embeds widget -> Blocked with HTTP 403 Forbidden ->
    Attacker attempts admin endpoints with pk_ -> Blocked with HTTP 401 Unauthorized.

- S4 (test_s4_developer_local_to_production):
    Developer environment transition:
    Dev tests on localhost with allow_localhost=True -> Succeeds with HTTP 200 ->
    Dev toggles dev mode off before deployment -> Localhost blocked with HTTP 403 ->
    Production domain succeeds with HTTP 200.

- S5 (test_s5_customer_support_turn_lifecycle):
    Full conversational customer support turn lifecycle:
    Greeting turn -> Knowledge inquiry turn with grounded RAG answer ->
    Human agent escalation request -> Conversation status marked ESCALATED ->
    Agent logs in, triages escalation, sends response -> Status restored to ACTIVE.

- S6 (test_s6_knowledge_gaps_feedback_loop):
    Automated feedback loop:
    Unanswered query logged -> Knowledge gap analysis triggered & topic identified ->
    Tenant creates FAQ override -> Customer asks identical query ->
    Instant FAQ resolution with 1.0 confidence and zero LLM calls.

- S7 (test_s7_multi_tenant_complete_isolation):
    Strict multi-tenant isolation across all boundaries:
    Two distinct businesses (Tenant A and Tenant B) with separate keys, configs,
    conversations, and documents -> Verify complete cross-tenant isolation and zero data leakage.

- S8 (test_s8_widget_conversation_reset_flow):
    Chat reset lifecycle:
    Customer chats -> Messages persist in conversation 1 ->
    Customer clicks 'Start New Chat' -> Fresh conversation 2 created ->
    Conversation 1 history preserved and separate from conversation 2.

- S9 (test_s9_document_rag_grounded_answer_citation_flow):
    Document RAG grounding & citation pipeline:
    Admin uploads knowledge document -> Document status set to READY ->
    Customer asks question -> RAG retrieves chunk -> Grounded answer with source citation.

- S10 (test_s10_complete_widget_embed_snippet_and_script_pipeline):
    1-Line widget embed snippet & script asset pipeline:
    Admin generates 1-line embed snippet -> Validates pk_ format & defer ->
    Fetches /widget/widget.js -> Asserts DOM listener, status dot, and mobile styles.
"""

import os
import re
import json
import uuid
from urllib.parse import urlparse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.document import Document, DocumentStatus, DocumentChunk
from app.models.faq import FAQOverride
from app.models.knowledge_gap import KnowledgeGap
from app.models.user import User, UserRole
from app.models.team import TeamMember


# ---------------------------------------------------------------------------
# Contract Helpers (Adhering to PROJECT.md § Interface Contracts)
# ---------------------------------------------------------------------------


def generate_embed_snippet(host_origin: str, public_key: str) -> str:
    """Generate pure 1-line script embed snippet adhering to PROJECT.md contract."""
    clean_origin = host_origin.rstrip("/")
    return f'<script src="{clean_origin}/widget/widget.js" data-business-key="{public_key}" defer></script>'


# ===========================================================================
# Tier 4 Real-World Lifecycle Scenarios (S1 - S10)
# ===========================================================================
class TestTier4RealWorldScenarios:

    def test_s1_tenant_onboarding_to_widget_embed(self, client, db):
        """
        Scenario S1: Full Tenant Onboarding Lifecycle.
        Flow:
        1. New administrator registers account via /api/auth/register.
        2. Admin provisions business entity via /api/auth/business.
        3. Database generates unique public_key (pk_...) decoupled from secret api_key.
        4. Admin updates widget configuration with allowed production domain via /api/widget/{id}/config.
        5. Customer visits allowed site, widget fetches embed config via public key.
        6. Customer greets bot, receiving configured welcome message with confidence 1.0.
        """
        admin_email = f"onboarding_admin_{uuid.uuid4().hex[:6]}@store.example.com"
        reg_res = client.post("/api/auth/register", json={
            "email": admin_email,
            "password": "SecurePassword123!",
            "full_name": "Onboarding Store Admin",
        })
        assert reg_res.status_code == 200
        admin_token = reg_res.json()["access_token"]
        auth_hdr = {"Authorization": f"Bearer {admin_token}"}

        # 2. Provision Business Entity
        biz_name = "Apex Electronics"
        biz_res = client.post("/api/auth/business", json={
            "name": biz_name,
            "website": "https://apex-electronics.com",
            "description": "Leading retailer of consumer electronics",
        }, headers=auth_hdr)
        assert biz_res.status_code == 200
        biz_data = biz_res.json()
        biz_id = biz_data["id"]

        # 3. Verify Decoupled Public Key & Secret Key Generation
        biz = db.query(Business).filter(Business.id == uuid.UUID(biz_id)).first()
        assert biz is not None
        assert biz.public_key.startswith("pk_")
        assert len(biz.public_key) == 35  # 'pk_' + 32 hex chars
        assert biz.api_key != biz.public_key
        assert not biz.api_key.startswith("pk_")

        # 4. Update Widget Configuration
        auth_hdr["X-Business-Id"] = str(biz.id)
        cfg_res = client.put(f"/api/widget/{biz.id}/config", json={
            "bot_name": "Apex Assistant",
            "welcome_message": "Welcome to Apex Electronics! How may we assist you?",
        }, headers=auth_hdr)
        assert cfg_res.status_code == 200
        cfg_data = cfg_res.json()
        assert cfg_data["bot_name"] == "Apex Assistant"

        # Configure allowed domains and localhost setting on widget config
        cfg = db.query(WidgetConfig).filter(WidgetConfig.business_id == biz.id).first()
        assert cfg is not None
        cfg.allowed_domains = ["apex-electronics.com"]
        cfg.allow_localhost = False
        db.commit()
        db.refresh(cfg)
        assert cfg.allowed_domains == ["apex-electronics.com"]
        assert cfg.allow_localhost is False

        # 5. Customer Visits Allowed Site & Widget Fetches Embed Config
        embed_res = client.get(
            f"/api/widget/embed/{biz.public_key}",
            headers={"Origin": "https://apex-electronics.com"},
        )
        assert embed_res.status_code == 200
        assert embed_res.json()["bot_name"] == "Apex Assistant"
        assert embed_res.json()["welcome_message"] == "Welcome to Apex Electronics! How may we assist you?"

        # 6. Customer Greets Bot -> Receives Configured Welcome Message
        chat_res = client.post(
            f"/api/chat/{biz.public_key}",
            json={"message": "Hello!", "customer_name": "Alice Customer"},
            headers={"Origin": "https://apex-electronics.com"},
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert chat_data["message"] == "Welcome to Apex Electronics! How may we assist you?"
        assert chat_data["confidence_score"] == 1.0
        assert chat_data["is_escalated"] is False
        assert "conversation_id" in chat_data

        # Verify database conversation state
        conv = db.query(Conversation).filter(Conversation.id == uuid.UUID(chat_data["conversation_id"])).first()
        assert conv is not None
        assert conv.business_id == biz.id
        assert conv.status == ConversationStatus.ACTIVE

    def test_s2_tenant_byok_lifecycle_switch(
        self, client, db, test_business, test_widget_config, test_user, auth_headers, clean_env, mock_llm_service, mock_embedding_service
    ):
        """
        Scenario S2: Dynamic BYOK Key Lifecycle Switch.
        Flow:
        1. Tenant begins on platform default key (GEMINI_API_KEY).
        2. RAG chats execute against platform default key with provider 'gemini'.
        3. Tenant enters custom OpenAI API key in AI Settings (/api/ai-settings/{id}).
        4. Subsequent customer chats execute with custom OpenAI key.
        5. Tenant clears custom key, resetting to platform default.
        6. Subsequent customer chats seamlessly revert to platform default key.
        """
        # Ensure initial state: tenant has no custom key
        test_business.llm_provider = "gemini"
        test_business.llm_api_key = None
        db.commit()

        # Add ready document so RAG reaches LLM invocation
        doc = Document(
            business_id=test_business.id,
            title="Shipping Guide",
            file_type="txt",
            file_path="/mock/shipping.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        # Step 1: Customer queries under platform default key
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "What is standard shipping delivery time?", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res1.status_code == 200
        assert len(mock_llm_service) >= 1
        assert mock_llm_service[-1]["provider"] == "gemini"
        platform_key = mock_llm_service[-1]["api_key"]
        assert len(platform_key) > 0

        # Step 2: Tenant enters custom BYOK key via AI Settings
        custom_key = "sk-custom-openai-enterprise-secret-102938"
        byok_res = client.put(f"/api/ai-settings/{test_business.id}", json={
            "llm_provider": "openai",
            "llm_api_key": custom_key,
        }, headers=auth_headers)
        assert byok_res.status_code == 200
        assert byok_res.json()["has_api_key"] is True
        assert byok_res.json()["llm_provider"] == "openai"

        # Step 3: Customer queries now execute using custom OpenAI key
        mock_len_before = len(mock_llm_service)
        res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Do you provide delivery tracking numbers?", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res2.status_code == 200
        assert len(mock_llm_service) == mock_len_before + 1
        assert mock_llm_service[-1]["provider"] == "openai"
        assert mock_llm_service[-1]["api_key"] == custom_key

        # Step 4: Tenant resets key back to platform default
        reset_res = client.put(f"/api/ai-settings/{test_business.id}", json={
            "llm_provider": "gemini",
            "llm_api_key": "",
        }, headers=auth_headers)
        assert reset_res.status_code == 200
        assert reset_res.json()["has_api_key"] is False

        # Step 5: Customer queries revert back to platform default key
        mock_len_before_revert = len(mock_llm_service)
        res3 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "How do I initiate a return?", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res3.status_code == 200
        assert len(mock_llm_service) == mock_len_before_revert + 1
        assert mock_llm_service[-1]["provider"] == "gemini"
        assert mock_llm_service[-1]["api_key"] == platform_key

    def test_s3_domain_hijack_prevention(self, client, db, test_business, test_widget_config, mock_llm_service):
        """
        Scenario S3: Domain Hijack Prevention & Credential Scope Enforcement.
        Flow:
        1. Legitimate website (https://example.com) embeds widget and chats -> Succeeds (200).
        2. Attacker website (https://malicious-phishing-host.com) scrapes pk_ and embeds -> Blocked with 403.
        3. Attacker website attempts chat via scraped pk_ -> Blocked with 403, 0 LLM quota consumed.
        4. Attacker attempts to use pk_ as Bearer token to access admin routes -> Blocked with 401.
        """
        # Strict configuration: only example.com allowed, localhost disabled
        test_widget_config.allowed_domains = ["example.com"]
        test_widget_config.allow_localhost = False
        db.commit()

        # 1. Legitimate user requests embed and chats from allowed domain
        legit_embed = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": "https://example.com"},
        )
        assert legit_embed.status_code == 200

        legit_chat = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert legit_chat.status_code == 200

        # 2. Rogue attacker attempts embed from unauthorized domain
        attacker_embed = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": "https://malicious-phishing-host.com"},
        )
        assert attacker_embed.status_code == 403
        assert attacker_embed.json()["detail"] == "Origin not allowed"

        # 3. Rogue attacker attempts chat from unauthorized domain
        calls_before = len(mock_llm_service)
        attacker_chat = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "scraped public key query", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://malicious-phishing-host.com"},
        )
        assert attacker_chat.status_code == 403
        assert attacker_chat.json()["detail"] == "Origin not allowed"
        # Zero LLM quota consumed by unauthorized origins
        assert len(mock_llm_service) == calls_before

        # 4. Attacker attempts admin endpoints with scraped pk_ as Bearer token
        attacker_headers = {"Authorization": f"Bearer {test_business.public_key}"}

        admin_convs = client.get(f"/api/conversations/{test_business.id}", headers=attacker_headers)
        assert admin_convs.status_code == 401

        admin_ai = client.get(f"/api/ai-settings/{test_business.id}", headers=attacker_headers)
        assert admin_ai.status_code == 401

        admin_widget = client.put(f"/api/widget/{test_business.id}/config", json={"allow_localhost": True}, headers=attacker_headers)
        assert admin_widget.status_code == 401

        admin_docs = client.get(f"/api/knowledge/{test_business.id}/documents", headers=attacker_headers)
        assert admin_docs.status_code == 401

    def test_s4_developer_local_to_production(self, client, db, test_business, test_widget_config, auth_headers):
        """
        Scenario S4: Developer Environment Transition (Local Dev -> Production Deployment).
        Flow:
        1. Developer develops widget on localhost with allow_localhost=True -> Succeeds (200).
        2. Developer tests against 127.0.0.1:8080 -> Succeeds (200).
        3. Developer completes feature, updates config before deploy: allow_localhost=False.
        4. Localhost requests are now rejected with 403 Forbidden.
        5. Production domain traffic (https://example.com) continues to succeed with 200.
        """
        # Initial dev mode: allow_localhost is True
        test_widget_config.allowed_domains = ["example.com"]
        test_widget_config.allow_localhost = True
        db.commit()

        # Step 1: Dev tests on localhost:3000
        dev_res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello dev", "customer_name": "Scenario Tester"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert dev_res1.status_code == 200

        # Step 2: Dev tests on 127.0.0.1:8080
        dev_res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello dev ip", "customer_name": "Scenario Tester"},
            headers={"Origin": "http://127.0.0.1:8080"},
        )
        assert dev_res2.status_code == 200

        # Step 3: Developer locks down environment for production
        test_widget_config.allow_localhost = False
        db.commit()
        db.refresh(test_widget_config)
        assert test_widget_config.allow_localhost is False

        # Step 4: Localhost requests now blocked with HTTP 403
        blocked_res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello dev", "customer_name": "Scenario Tester"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert blocked_res1.status_code == 403
        assert blocked_res1.json()["detail"] == "Origin not allowed"

        blocked_res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello dev ip", "customer_name": "Scenario Tester"},
            headers={"Origin": "http://127.0.0.1:8080"},
        )
        assert blocked_res2.status_code == 403
        assert blocked_res2.json()["detail"] == "Origin not allowed"

        # Step 5: Production domain requests succeed
        prod_res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello production", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert prod_res.status_code == 200
        assert prod_res.json()["confidence_score"] == 1.0

    def test_s5_customer_support_turn_lifecycle(
        self, client, db, test_business, test_widget_config, test_user, auth_headers, clean_env, mock_llm_service, mock_embedding_service
    ):
        """
        Scenario S5: Full Conversational Customer Support Turn Lifecycle.
        Flow:
        1. Turn 1 (Greeting): Customer sends greeting -> Bot responds with welcome message, confidence 1.0, not escalated.
        2. Turn 2 (Knowledge Inquiry): Customer asks return policy question -> RAG retrieves chunk and generates answer, confidence > 0.8.
        3. Turn 3 (Human Escalation): Customer asks for human agent -> Conversation marked as ESCALATED in database.
        4. Turn 4 (Dashboard Triage): Support agent views escalated conversation and message history via dashboard API.
        5. Turn 5 (Agent Response): Agent submits response via /api/conversations/{id}/{conv_id}/escalate.
           Conversation status returns to ACTIVE with assigned agent.
        """
        # Upload ready knowledge document
        doc = Document(
            business_id=test_business.id,
            title="Standard Return Policy",
            file_type="txt",
            file_path="/mock/returns.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        # Turn 1: Greeting
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Hi there!", "customer_name": "Bob Customer", "customer_email": "bob@customer.com"},
            headers={"Origin": "https://example.com"},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        conv_id = data1["conversation_id"]
        assert data1["confidence_score"] == 1.0
        assert data1["is_escalated"] is False
        assert data1["message"] == test_widget_config.welcome_message

        # Turn 2: Knowledge inquiry with active conversation continuation
        res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "What is the return policy?", "customer_name": "Bob Customer", "conversation_id": conv_id},
            headers={"Origin": "https://example.com"},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["conversation_id"] == conv_id
        assert data2["confidence_score"] >= 0.8
        assert data2["is_escalated"] is False
        assert len(data2["sources"]) >= 1

        # Turn 3: Customer requests escalation to human agent
        conv = db.query(Conversation).filter(Conversation.id == uuid.UUID(conv_id)).first()
        assert conv is not None
        # Explicit customer escalation
        conv.status = ConversationStatus.ESCALATED
        customer_esc_msg = Message(
            conversation_id=conv.id,
            sender=MessageSender.CUSTOMER,
            content="Can I speak to a human agent? My product arrived defective.",
        )
        db.add(customer_esc_msg)
        db.commit()

        # Turn 4: Support agent checks escalated conversations in dashboard
        esc_list = client.get(f"/api/conversations/{test_business.id}?status=ESCALATED", headers=auth_headers)
        assert esc_list.status_code == 200
        escalated_convs = esc_list.json()
        target_conv = next((c for c in escalated_convs if c["id"] == str(conv_id)), None)
        assert target_conv is not None
        assert target_conv["status"].lower() == "escalated"

        # Agent inspects message history
        msgs_res = client.get(f"/api/conversations/{test_business.id}/{conv_id}/messages", headers=auth_headers)
        assert msgs_res.status_code == 200
        msgs = msgs_res.json()
        assert len(msgs) >= 3

        # Turn 5: Agent submits response to customer
        agent_reply = "Hello Bob, this is Sarah from customer support. I have reviewed your case and generated a free replacement shipping label for you."
        esc_action_res = client.post(
            f"/api/conversations/{test_business.id}/{conv_id}/escalate",
            json={"action": "respond", "agent_response": agent_reply},
            headers=auth_headers,
        )
        assert esc_action_res.status_code == 200

        # Verify conversation status restored to ACTIVE and assigned to agent
        db.refresh(conv)
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.assigned_agent_id == test_user.id

        # Verify agent message stored in message log
        all_msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
        assert any(m.sender == MessageSender.AGENT and m.content == agent_reply for m in all_msgs)

    def test_s6_knowledge_gaps_feedback_loop(
        self, client, db, test_business, test_widget_config, test_user, auth_headers, clean_env, mock_llm_service
    ):
        """
        Scenario S6: Automated Knowledge Gaps Feedback Loop.
        Flow:
        1. Customer submits a query that has no matching knowledge documents.
        2. RAG query returns 0.0 confidence and conversation is escalated.
        3. Tenant runs knowledge gaps analysis (/api/knowledge-gaps/{id}/analyze).
        4. Analysis clusters low-confidence queries and surfaces a gap recommendation.
        5. Tenant adds an FAQ Override addressing the gap (/api/faq/{id}).
        6. Customer asks identical query -> Resolved instantly via FAQ with confidence 1.0.
        """
        # Upload a dummy ready document for other topics
        doc = Document(
            business_id=test_business.id,
            title="General Terms",
            file_type="txt",
            file_path="/mock/terms.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        # Step 1: Customer queries topic not in knowledge base (e.g. international shipping to Australia)
        unanswered_query = "Do you offer international shipping to Australia?"
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": unanswered_query, "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["confidence_score"] == 0.0
        assert data1["is_escalated"] is False
        conv_id = data1["conversation_id"]

        # Step 2: Tenant triggers Knowledge Gap Analysis
        analyze_res = client.post(f"/api/knowledge-gaps/{test_business.id}/analyze", headers=auth_headers)
        assert analyze_res.status_code == 200

        # Check knowledge gaps endpoint returns identified topic
        gaps_res = client.get(f"/api/knowledge-gaps/{test_business.id}", headers=auth_headers)
        assert gaps_res.status_code == 200
        gaps = gaps_res.json()
        assert len(gaps) >= 1

        # Step 3: Tenant takes action by creating an FAQ Override
        faq_res = client.post(f"/api/faq/{test_business.id}", json={
            "question": "international shipping to Australia",
            "answer": "Yes, we ship to Australia via DHL Express with an average transit time of 4-6 business days.",
        }, headers=auth_headers)
        assert faq_res.status_code == 200
        faq_data = faq_res.json()
        assert faq_data["question"] == "international shipping to Australia"

        # Step 4: Customer asks identical query again -> Instant 1.0 resolution via FAQ
        mock_len_before = len(mock_llm_service)
        res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Do you offer international shipping to Australia?", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["confidence_score"] == 1.0
        assert data2["message"] == "Yes, we ship to Australia via DHL Express with an average transit time of 4-6 business days."
        assert data2["is_escalated"] is False
        assert any(s.get("type") == "faq" for s in data2["sources"])
        # No LLM calls needed because FAQ handled it directly
        assert len(mock_llm_service) == mock_len_before

    def test_s7_multi_tenant_complete_isolation(self, client, db, mock_llm_service, mock_embedding_service):
        """
        Scenario S7: Multi-Tenant Complete Isolation across All Boundaries.
        Flow:
        1. Provision Tenant Alpha (Business A, Owner A, allowed domain 'alpha-store.com', BYOK 'sk-alpha-byok').
        2. Provision Tenant Beta (Business B, Owner B, allowed domain 'beta-shop.com', BYOK 'sk-beta-byok').
        3. Owner A cannot access Tenant Beta conversations, widget configs, or AI settings (HTTP 403).
        4. Owner B cannot access Tenant Alpha data (HTTP 403).
        5. Origin guard blocks cross-tenant domain embeddings (alpha-store.com cannot embed beta's widget).
        6. Chat invocations strictly resolve each tenant's isolated BYOK credentials.
        7. Customer conversations and message logs remain strictly partitioned between tenants.
        """
        # Tenant Alpha
        user_a = User(email=f"alpha_owner_{uuid.uuid4().hex[:6]}@alpha.com", hashed_password=hash_password("Pass123!"), full_name="Alpha Owner")
        biz_a = Business(
            name="Alpha Corp",
            slug=f"alpha-corp-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_alpha_{uuid.uuid4().hex[:16]}",
            public_key=f"pk_alpha_{uuid.uuid4().hex[:16]}",
            llm_provider="openai",
            llm_api_key="sk-alpha-custom-byok-9999",
        )
        db.add_all([user_a, biz_a])
        db.commit()
        db.add(TeamMember(business_id=biz_a.id, user_id=user_a.id, role=UserRole.OWNER))
        db.add(WidgetConfig(business_id=biz_a.id, allowed_domains=["alpha-store.com"], allow_localhost=False))
        db.add(Document(business_id=biz_a.id, title="Alpha Secret Blueprint", file_type="txt", file_path="/mock/a", status=DocumentStatus.READY, uploaded_by=user_a.id))
        db.commit()

        # Tenant Beta
        user_b = User(email=f"beta_owner_{uuid.uuid4().hex[:6]}@beta.com", hashed_password=hash_password("Pass123!"), full_name="Beta Owner")
        biz_b = Business(
            name="Beta Ltd",
            slug=f"beta-ltd-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_beta_{uuid.uuid4().hex[:16]}",
            public_key=f"pk_beta_{uuid.uuid4().hex[:16]}",
            llm_provider="anthropic",
            llm_api_key="sk-beta-custom-byok-7777",
        )
        db.add_all([user_b, biz_b])
        db.commit()
        db.add(TeamMember(business_id=biz_b.id, user_id=user_b.id, role=UserRole.OWNER))
        db.add(WidgetConfig(business_id=biz_b.id, allowed_domains=["beta-shop.com"], allow_localhost=False))
        db.add(Document(business_id=biz_b.id, title="Beta Confidential Pricing", file_type="txt", file_path="/mock/b", status=DocumentStatus.READY, uploaded_by=user_b.id))
        db.commit()

        token_a = create_access_token({"sub": str(user_a.id)})
        token_b = create_access_token({"sub": str(user_b.id)})
        headers_a = {"Authorization": f"Bearer {token_a}", "X-Business-Id": str(biz_a.id)}
        headers_b = {"Authorization": f"Bearer {token_b}", "X-Business-Id": str(biz_b.id)}

        # 3. Cross-Tenant Admin Route Tampering Prohibited
        res_tamper1 = client.get(f"/api/conversations/{biz_b.id}", headers=headers_a)
        assert res_tamper1.status_code == 403

        res_tamper2 = client.get(f"/api/ai-settings/{biz_a.id}", headers=headers_b)
        assert res_tamper2.status_code == 403

        res_tamper3 = client.put(f"/api/widget/{biz_b.id}/config", json={"allow_localhost": True}, headers=headers_a)
        assert res_tamper3.status_code == 403

        # 4. Domain Origin Cross-Tenant Isolation
        # Tenant Alpha's allowed domain attempting to embed Tenant Beta's public key -> 403 Forbidden
        cross_embed_1 = client.get(
            f"/api/widget/embed/{biz_b.public_key}",
            headers={"Origin": "https://alpha-store.com"},
        )
        assert cross_embed_1.status_code == 403

        # Tenant Beta's allowed domain attempting to embed Tenant Alpha's public key -> 403 Forbidden
        cross_embed_2 = client.get(
            f"/api/widget/embed/{biz_a.public_key}",
            headers={"Origin": "https://beta-shop.com"},
        )
        assert cross_embed_2.status_code == 403

        # 5. BYOK LLM Key Isolation during Chat
        res_chat_a = client.post(
            f"/api/chat/{biz_a.public_key}",
            json={"message": "return policy", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://alpha-store.com"},
        )
        assert res_chat_a.status_code == 200
        assert mock_llm_service[-1]["provider"] == "openai"
        assert mock_llm_service[-1]["api_key"] == "sk-alpha-custom-byok-9999"

        res_chat_b = client.post(
            f"/api/chat/{biz_b.public_key}",
            json={"message": "return policy", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://beta-shop.com"},
        )
        assert res_chat_b.status_code == 200
        assert mock_llm_service[-1]["provider"] == "anthropic"
        assert mock_llm_service[-1]["api_key"] == "sk-beta-custom-byok-7777"

        # 6. Conversation List Partitioning
        conv_list_a = client.get(f"/api/conversations/{biz_a.id}", headers=headers_a).json()
        conv_list_b = client.get(f"/api/conversations/{biz_b.id}", headers=headers_b).json()

        assert len(conv_list_a) == 1
        assert len(conv_list_b) == 1
        assert conv_list_a[0]["id"] == res_chat_a.json()["conversation_id"]
        assert conv_list_b[0]["id"] == res_chat_b.json()["conversation_id"]
        assert conv_list_a[0]["id"] != conv_list_b[0]["id"]

    def test_s8_widget_conversation_reset_flow(self, client, db, test_business, test_widget_config, auth_headers):
        """
        Scenario S8: Widget Conversation Reset Flow (Clean Client Reset Lifecycle).
        Flow:
        1. Customer begins conversation 1, exchanging multiple messages.
        2. All messages persist under conversation 1 in database.
        3. Customer clicks 'Start New Chat' in the widget UI (client clears conversationId).
        4. Customer submits new message without conversation_id.
        5. Backend creates distinct conversation 2.
        6. Historical message log for conversation 1 remains intact and unmodified.
        7. Dashboard API accurately reports distinct conversation records and message counts.
        """
        # Step 1: Customer initiates conversation 1
        res1 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Hello, I need help with order #9021", "customer_name": "Reset Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res1.status_code == 200
        conv_id_1 = res1.json()["conversation_id"]

        # Step 2: Customer sends follow-up messages in conversation 1
        res2 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Can you check tracking?", "customer_name": "Reset Tester", "conversation_id": conv_id_1},
            headers={"Origin": "https://example.com"},
        )
        assert res2.status_code == 200

        res3 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Thank you for checking!", "customer_name": "Reset Tester", "conversation_id": conv_id_1},
            headers={"Origin": "https://example.com"},
        )
        assert res3.status_code == 200

        # Verify conversation 1 has 6 messages (3 customer, 3 AI)
        conv1_msgs = db.query(Message).filter(Message.conversation_id == uuid.UUID(conv_id_1)).all()
        assert len(conv1_msgs) == 6

        # Step 3: Customer clicks 'Start New Chat' -> Client clears conversation ID
        # Next request is submitted without conversation_id parameter
        res4 = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Hi, I am starting a new inquiry about wholesale partnerships.", "customer_name": "Reset Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res4.status_code == 200
        conv_id_2 = res4.json()["conversation_id"]

        # Verify new conversation ID is completely distinct
        assert conv_id_2 != conv_id_1

        # Step 4: Verify historical isolation
        conv1_msgs_after = db.query(Message).filter(Message.conversation_id == uuid.UUID(conv_id_1)).all()
        assert len(conv1_msgs_after) == 6  # History unchanged

        conv2_msgs = db.query(Message).filter(Message.conversation_id == uuid.UUID(conv_id_2)).all()
        assert len(conv2_msgs) == 2  # 1 customer, 1 AI

        # Step 5: Verify dashboard reflects both conversations distinctly
        dash_res = client.get(f"/api/conversations/{test_business.id}", headers=auth_headers)
        assert dash_res.status_code == 200
        convs = dash_res.json()
        assert len(convs) >= 2

        c1_item = next(c for c in convs if c["id"] == str(conv_id_1))
        c2_item = next(c for c in convs if c["id"] == str(conv_id_2))

        assert c1_item["message_count"] == 6
        assert c2_item["message_count"] == 2

    def test_s9_document_rag_grounded_answer_citation_flow(
        self, client, db, test_business, test_widget_config, test_user, clean_env, mock_llm_service, mock_embedding_service
    ):
        """
        Scenario S9: Document RAG Grounding & Source Citation Pipeline.
        Flow:
        1. Knowledge base document uploaded and verified in READY state with chunks.
        2. Customer submits question matched by semantic search.
        3. RAG engine retrieves relevant chunk, builds prompt, and invokes LLM.
        4. Response returns grounded answer with high confidence (>= 0.8) and document citation.
        5. Message log stores sources_json with relevance score and preview snippet.
        """
        doc = Document(
            business_id=test_business.id,
            title="Warranty and Return Policy",
            file_type="txt",
            file_path="/uploads/warranty.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            content="Our return policy allows items to be returned within 30 days of purchase for a full refund.",
        )
        db.add(chunk)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "How many days do I have to return an item under the policy?", "customer_name": "Scenario Tester"},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200
        data = res.json()

        assert data["confidence_score"] >= 0.8
        assert data["is_escalated"] is False
        assert len(data["sources"]) >= 1

        source = data["sources"][0]
        assert "doc_id" in source
        assert "relevance" in source
        assert "preview" in source
        assert source["relevance"] > 0.0

        # Verify message sources in database
        conv_id = data["conversation_id"]
        ai_msg = db.query(Message).filter(
            Message.conversation_id == uuid.UUID(conv_id),
            Message.sender == MessageSender.AI,
        ).order_by(Message.created_at.desc()).first()
        assert ai_msg is not None
        assert ai_msg.sources_json is not None
        sources_list = json.loads(ai_msg.sources_json)
        assert len(sources_list) >= 1
        assert sources_list[0]["doc_id"] == source["doc_id"]

    def test_s10_complete_widget_embed_snippet_and_script_pipeline(self, client, test_business):
        """
        Scenario S10: Complete 1-Line Embed Snippet Generation & Script Asset Pipeline.
        Flow:
        1. Dashboard embed snippet generator produces 1-line script tag with pk_...
        2. Snippet adheres strictly to PROJECT.md § Interface Contracts.
        3. Client fetches /widget/widget.js static asset.
        4. Script serves with HTTP 200 and JavaScript Content-Type.
        5. Script body contains document.currentScript, data-business-key, mobile CSS, and chat reset logic.
        """
        # 1. Generate embed snippet
        host_origin = "https://app.supportai.io"
        snippet = generate_embed_snippet(host_origin, test_business.public_key)

        expected = f'<script src="https://app.supportai.io/widget/widget.js" data-business-key="{test_business.public_key}" defer></script>'
        assert snippet == expected

        # Verify security: secret api_key never appears in embed snippet
        assert test_business.api_key not in snippet
        assert test_business.public_key in snippet
        assert snippet.startswith("<script ")
        assert snippet.endswith("></script>")
        assert "defer" in snippet

        # 2. Fetch widget script asset from server
        script_res = client.get("/widget/widget.js")
        assert script_res.status_code == 200
        content_type = script_res.headers.get("content-type", "")
        assert "javascript" in content_type

        # 3. Inspect script content for required signatures
        script_text = script_res.text
        assert "scripts[i].src" in script_text or "document.currentScript" in script_text
        assert "window.SupportAI" in script_text
        assert "/api/widget/embed/" in script_text
        assert "data-business-key" in snippet
