"""
Unit and integration tests for Conversational Intent Detection,
Human Escalation Containment, and Un-escalated Low-Confidence RAG Misses.
"""

import pytest
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.document import Document, DocumentStatus


class TestFeature9ConversationalIntents:
    """F9: Conversational intent resolution across greetings, gratitude, closings, identity, and escalation."""

    def test_greetings_pure_tokens(self, client, test_business, test_widget_config):
        """Pure single-token greetings resolve with welcome message, confidence 1.0, is_escalated False."""
        for g in ["hi", "hello", "hey", "howdy", "sup", "greetings"]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": g})
            assert res.status_code == 200
            data = res.json()
            assert data["message"] == test_widget_config.welcome_message
            assert data["confidence_score"] == 1.0
            assert data["is_escalated"] is False

    def test_greetings_time_of_day_variations(self, client, test_business, test_widget_config):
        """Multi-word greetings (Good morning/afternoon/evening/day) resolve cleanly."""
        for g in ["Good morning", "good afternoon", "Good Evening", "good day!"]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": g})
            assert res.status_code == 200
            data = res.json()
            assert data["message"] == test_widget_config.welcome_message
            assert data["confidence_score"] == 1.0
            assert data["is_escalated"] is False

    def test_compound_greeting_can_you_help_me(self, client, test_business, test_widget_config):
        """Natural compound greeting 'Good morning, can you help me?' resolves as greeting without RAG/escalation."""
        for phrase in [
            "Good morning, can you help me?",
            "Hello! Can you help me?",
            "Hey there, how are you?",
            "Hi, I need some help",
        ]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": phrase})
            assert res.status_code == 200
            data = res.json()
            assert data["message"] == test_widget_config.welcome_message
            assert data["confidence_score"] == 1.0
            assert data["is_escalated"] is False

    def test_conversational_gratitude(self, client, test_business):
        """Gratitude phrases return polite thank-you response with confidence 1.0."""
        for thanks in ["Thanks!", "thank you", "thank you so much", "much appreciated", "appreciate it!"]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": thanks})
            assert res.status_code == 200
            data = res.json()
            assert "welcome" in data["message"].lower()
            assert data["confidence_score"] == 1.0
            assert data["is_escalated"] is False

    def test_conversational_closings(self, client, test_business):
        """Closing phrases return polite farewell with confidence 1.0."""
        for closing in ["bye", "goodbye", "Have a nice day!", "see you later", "take care"]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": closing})
            assert res.status_code == 200
            data = res.json()
            assert any(word in data["message"].lower() for word in ["goodbye", "day", "reach out"])
            assert data["confidence_score"] == 1.0
            assert data["is_escalated"] is False

    def test_conversational_identity_and_capabilities(self, client, test_business):
        """Identity questions return assistant capability summary with confidence 1.0."""
        for query in ["who are you?", "what can you do", "what do you do", "help"]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": query})
            assert res.status_code == 200
            data = res.json()
            assert "assistant" in data["message"].lower() or "help" in data["message"].lower()
            assert data["confidence_score"] == 1.0
            assert data["is_escalated"] is False

    def test_substantive_query_with_greeting_routes_to_knowledge_base(self, client, db, test_business, test_user, mock_embedding_service, mock_llm_service):
        """Sentences starting with greetings but containing substantive inquiries route to knowledge base."""
        doc = Document(
            business_id=test_business.id,
            title="Return Policy",
            file_type="txt",
            file_path="/mock/returns.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "Hello, can someone help me with my order?"},
        )
        assert res.status_code == 200
        data = res.json()
        # Not intercepted as pure greeting
        assert "order" in data["message"].lower() or "knowledge base" in data["message"].lower()

    def test_strict_human_escalation_explicit_requests(self, client, db, test_business):
        """Explicit human requests mark conversation status as ESCALATED in DB and set is_escalated = True."""
        for phrase in [
            "I want to talk to a human",
            "Can I speak with an agent?",
            "Please connect me to a representative",
            "I need real person support",
            "human support please",
        ]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": phrase})
            assert res.status_code == 200
            data = res.json()
            assert data["is_escalated"] is True
            assert "human support team" in data["message"].lower() or "representative" in data["message"].lower()

            conv = db.query(Conversation).filter(Conversation.id == data["conversation_id"]).first()
            assert conv.status == ConversationStatus.ESCALATED

    def test_low_confidence_rag_miss_does_not_lock_escalation(self, client, db, test_business, test_user, mock_embedding_service, mock_llm_service):
        """Out-of-domain knowledge queries return polite fallback without locking conversation into ESCALATED."""
        doc = Document(
            business_id=test_business.id,
            title="General Store Info",
            file_type="txt",
            file_path="/mock/info.txt",
            status=DocumentStatus.READY,
            uploaded_by=test_user.id,
        )
        db.add(doc)
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "What is quantum gravity theory in physics?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_escalated"] is False
        assert "don't have enough information" in data["message"].lower()

        conv = db.query(Conversation).filter(Conversation.id == data["conversation_id"]).first()
        assert conv.status == ConversationStatus.ACTIVE

    def test_greeting_restores_escalated_conversation_to_active(self, client, db, test_business):
        """Greeting sent to an ESCALATED conversation restores DB status to ACTIVE."""
        conv = Conversation(business_id=test_business.id, status=ConversationStatus.ESCALATED)
        db.add(conv)
        db.commit()
        db.refresh(conv)

        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "hello", "conversation_id": str(conv.id)},
        )
        assert res.status_code == 200
        assert res.json()["is_escalated"] is False
        db.refresh(conv)
        assert conv.status == ConversationStatus.ACTIVE
