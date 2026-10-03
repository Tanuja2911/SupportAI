"""
Adversarial test suite for Greeting Resolution, Conversational Intent Detection,
and False Escalation Elimination in backend/app/api/routes/chat.py.
"""

import pytest
import json
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.document import Document, DocumentStatus


class TestAdversarialGreetingAndEscalation:
    """Adversarial stress-testing suite challenging greeting vs substantive discrimination,
    false escalation elimination, human escalation containment, and escalation recovery."""

    # -------------------------------------------------------------------------
    # 1. Greeting vs Substantive Discrimination
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("query,expected_keyword", [
        ("Hello, where is my order?", "order"),
        ("Good morning, how do I reset my password?", "password"),
        ("Hi, do you ship to Canada?", "ship"),
        ("Hey there! What is your refund policy?", "refund"),
        ("Good afternoon, can someone help me track my package?", "package"),
    ])
    def test_substantive_inquiries_with_greetings_route_to_rag(
        self, client, db, test_business, test_user, test_widget_config, mock_embedding_service, mock_llm_service, query, expected_keyword
    ):
        """Messages starting with greetings but containing substantive inquiries must NOT
        be intercepted as pure greetings. They must route to FAQ/RAG."""
        doc = Document(
            business_id=test_business.id,
            title="General Store Policies",
            file_type="txt",
            file_path="/mock/store_policies.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": query},
        )
        assert res.status_code == 200
        data = res.json()
        # Must not be the generic welcome greeting
        assert data["message"] != test_widget_config.welcome_message
        assert data["is_escalated"] is False

    # -------------------------------------------------------------------------
    # 2. Conversational Intent & Greetings
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("phrase", [
        "Good morning! Can you help me?",
        "Hello there, how are you?",
        "Thanks a million!",
        "See you later alligator",
    ])
    def test_natural_conversational_greetings_must_be_answered_conversationally(
        self, client, db, test_business, test_user, test_widget_config, phrase
    ):
        """Natural conversational greetings, gratitude, and closings must be answered
        conversationally with confidence 1.0, is_escalated=False, without falling through
        to low-confidence knowledge base fallbacks."""
        doc = Document(
            business_id=test_business.id,
            title="General Knowledge",
            file_type="txt",
            file_path="/mock/general.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": phrase},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_escalated"] is False
        assert data["confidence_score"] == 1.0
        # Must not receive the low-confidence fallback message
        assert "don't have enough information in my knowledge base" not in data["message"].lower()

    # -------------------------------------------------------------------------
    # 3. Strict Human Escalation Containment
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("phrase", [
        "I need to speak to a human",
        "representative please",
        "human support",
        "speak to human",
        "speak with a human",
        "Can I talk to a live agent?",
        "Please connect me with a representative",
    ])
    def test_explicit_human_escalation_containment(
        self, client, db, test_business, phrase
    ):
        """Explicit requests for human assistance must transition conversation status
        to ESCALATED and return is_escalated=True with confidence 1.0."""
        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": phrase},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_escalated"] is True
        assert data["confidence_score"] == 1.0
        assert "escalated" in data["message"].lower() or "representative" in data["message"].lower()

        conv = db.query(Conversation).filter(Conversation.id == data["conversation_id"]).first()
        assert conv.status == ConversationStatus.ESCALATED

    # -------------------------------------------------------------------------
    # 4. Mixed Greeting and Explicit Escalation
    # -------------------------------------------------------------------------
    def test_compound_greeting_with_escalation_prioritizes_escalation(
        self, client, db, test_business
    ):
        """When a message contains both a greeting and an explicit request for human support,
        escalation must take precedence over conversational greeting resolution."""
        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Good morning! Can I please speak with a human?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_escalated"] is True
        conv = db.query(Conversation).filter(Conversation.id == data["conversation_id"]).first()
        assert conv.status == ConversationStatus.ESCALATED

    # -------------------------------------------------------------------------
    # 5. False Escalation Elimination
    # -------------------------------------------------------------------------
    def test_low_confidence_unanswered_query_does_not_escalate(
        self, client, db, test_business, test_user, mock_embedding_service, mock_llm_service
    ):
        """Out-of-domain / low-confidence queries must return a polite fallback message
        and must NOT set conversation status to ESCALATED or return is_escalated=True."""
        doc = Document(
            business_id=test_business.id,
            title="Catalog",
            file_type="txt",
            file_path="/mock/catalog.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "What is the meaning of quantum chromodynamics?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_escalated"] is False
        assert "don't have enough information" in data["message"].lower()

        conv = db.query(Conversation).filter(Conversation.id == data["conversation_id"]).first()
        assert conv.status == ConversationStatus.ACTIVE

    # -------------------------------------------------------------------------
    # 6. Escalation Recovery
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("greeting", [
        "Good morning!",
        "hello",
        "hi there",
        "Thanks a million!",
    ])
    def test_greeting_restores_escalated_conversation_to_active(
        self, client, db, test_business, greeting
    ):
        """Sending a greeting or conversational phrase to an already-ESCALATED conversation
        must restore its status to ACTIVE and return is_escalated=False."""
        conv = Conversation(
            business_id=test_business.id,
            status=ConversationStatus.ESCALATED,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": greeting, "conversation_id": str(conv.id)},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_escalated"] is False

        db.refresh(conv)
        assert conv.status == ConversationStatus.ACTIVE
