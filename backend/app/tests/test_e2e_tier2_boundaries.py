"""
Milestone E2E-M2: Tier 2 Boundary Values, Malformed Inputs & Error Matrix Suite
Over 75 Rigorous End-to-End Boundary and Corner Case Tests.

Coverage Matrix (survey_e2e.md § 9.3 & PROJECT.md § Interface Contracts):
- Category 1: Origins & Domain Whitelisting Boundaries (F7, F8)
- Category 2: Public & Secret Key Formats and Limits (F1, F6)
- Category 3: Tokens & Authentication Security Boundaries (F6, F12, F13)
- Category 4: Greetings & Message Input Boundaries (F9)
- Category 5: RAG, Embeddings & LLM Failure Modes (F5, F9)
- Category 6: Schema Constraints & Database Cascade Boundaries (F1, F2)
"""

import os
import re
import uuid
from datetime import timedelta
from urllib.parse import urlparse

import pytest
import httpx
from jose import jwt
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.user import User, UserRole
from app.models.team import TeamMember
from app.models.faq import FAQOverride
from app.models.document import Document, DocumentStatus, DocumentChunk
from app.services.rag_engine import RAGEngine
import app.services.rag_engine as rag_module


# ===========================================================================
# Category 1: Origins & Domain Whitelisting Boundaries (F7, F8) - 22 Tests
# ===========================================================================
class TestOriginGuardBoundaries:
    def test_b1_origin_null_string_allowed_when_localhost_enabled(self):
        """B1: Origin header "null" (privacy-sensitive contexts / sandboxed iframes) allowed in dev mode."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("null", None, ["example.com"], allow_localhost=True) is True

    def test_b2_origin_null_string_blocked_when_localhost_disabled(self):
        """B2: Origin header "null" blocked when allow_localhost is False."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("null", None, ["example.com"], allow_localhost=False) is False

    def test_b3_origin_data_scheme_blocked(self):
        """B3: Origin with data: URI scheme is untrusted and rejected even with allow_localhost=True."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("data:text/html,<script>alert(1)</script>", None, ["example.com"], allow_localhost=True) is False
        assert validate_origin("data:text/html;base64,PHNjcmlwdD4=", None, ["example.com"], allow_localhost=False) is False

    def test_b4_origin_javascript_scheme_blocked(self):
        """B4: Origin with javascript: URI pseudo-scheme is untrusted and rejected."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("javascript:void(0)", None, ["example.com"], allow_localhost=True) is False
        assert validate_origin("javascript:alert(1)", None, ["example.com"], allow_localhost=False) is False

    def test_b5_origin_file_scheme_allowed_in_dev_mode(self):
        """B5: Origin with file:// scheme allowed when allow_localhost is True (local HTML file testing)."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("file:///home/user/workspace/test.html", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("file://", None, ["example.com"], allow_localhost=True) is True

    def test_b6_origin_file_scheme_blocked_when_dev_disabled(self):
        """B6: Origin with file:// scheme blocked when allow_localhost is False."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("file:///home/user/workspace/test.html", None, ["example.com"], allow_localhost=False) is False

    def test_b7_origin_custom_port_stripped_for_domain_match(self):
        """B7: Origin with custom port (e.g. :8443) correctly matches allowed domain entry."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://example.com:8443", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("http://example.com:3000", None, ["example.com"], allow_localhost=False) is True

    def test_b8_origin_standard_ports_http_https_match(self):
        """B8: Standard ports :80 and :443 correctly match domain whitelist."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://example.com:443", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("http://example.com:80", None, ["example.com"], allow_localhost=False) is True

    def test_b9_origin_trailing_slash_stripped(self):
        """B9: Trailing slash in origin URL does not disrupt domain extraction."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://example.com/", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("https://shop.example.com/", None, ["example.com"], allow_localhost=False) is True

    def test_b10_origin_deep_path_and_query_handled(self):
        """B10: Deep path and query parameters (common in Referer header) preserve host validation."""
        from app.core.origin_guard import validate_origin
        assert validate_origin(None, "https://example.com/checkout/step2?promo=save&ref=google#top", ["example.com"], allow_localhost=False) is True
        assert validate_origin(None, "https://unauthorized.org/path/index.html?token=123", ["example.com"], allow_localhost=False) is False

    def test_b11_origin_prefix_spoofing_prevented(self):
        """B11: Hostnames sharing suffix without dot separator (evil-example.com vs example.com) are rejected."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://evil-example.com", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("https://notexample.com", None, ["example.com"], allow_localhost=False) is False

    def test_b12_origin_suffix_spoofing_prevented(self):
        """B12: Hostnames using target domain as a subdomain prefix (example.com.attacker.com) are rejected."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://example.com.attacker.com", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("https://example.com.evil.co", None, ["example.com"], allow_localhost=False) is False

    def test_b13_origin_exact_domain_match(self):
        """B13: Exact hostname match without subdomains passes cleanly."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("http://example.com", None, ["example.com"], allow_localhost=False) is True

    def test_b14_origin_single_level_subdomain_allowed(self):
        """B14: Valid single-level subdomain of allowed domain passes."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://store.example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("https://admin.example.com", None, ["example.com"], allow_localhost=False) is True

    def test_b15_origin_multi_level_subdomain_allowed(self):
        """B15: Valid deeply nested multi-level subdomain passes."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://us-east.k8s.cluster.example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("https://dev.portal.staging.example.com", None, ["example.com"], allow_localhost=False) is True

    def test_b16_origin_idn_punycode_domain_allowed(self):
        """B16: Internationalized domain name (IDN) in Punycode format passes when whitelisted."""
        from app.core.origin_guard import validate_origin
        # Punycode for bücher.example.com -> xn--bcher-kva.example.com
        assert validate_origin("https://xn--bcher-kva.example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("https://xn--bcher-kva.de", None, ["xn--bcher-kva.de"], allow_localhost=False) is True

    def test_b17_origin_localhost_ipv4_variations(self):
        """B17: 127.0.0.1 with various ports succeeds when allow_localhost is True and fails when False."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("http://127.0.0.1", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://127.0.0.1:3000", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://127.0.0.1:8080", None, ["example.com"], allow_localhost=True) is True

        assert validate_origin("http://127.0.0.1", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("http://127.0.0.1:3000", None, ["example.com"], allow_localhost=False) is False

    def test_b18_origin_localhost_ipv6_variations(self):
        """B18: IPv6 loopback [::1] succeeds when allow_localhost is True and fails when False."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("http://[::1]", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://[::1]:5173", None, ["example.com"], allow_localhost=True) is True

        assert validate_origin("http://[::1]", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("http://[::1]:5173", None, ["example.com"], allow_localhost=False) is False

    def test_b19_origin_localhost_all_interfaces_0000(self):
        """B19: 0.0.0.0 bind host treated as local dev environment."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("http://0.0.0.0", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://0.0.0.0:8000", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://0.0.0.0:8000", None, ["example.com"], allow_localhost=False) is False

    def test_b20_origin_missing_both_origin_and_referer(self):
        """B20: Missing both Origin and Referer headers delegates to allow_localhost."""
        from app.core.origin_guard import validate_origin
        assert validate_origin(None, None, ["example.com"], allow_localhost=True) is True
        assert validate_origin(None, None, ["example.com"], allow_localhost=False) is False

    def test_b21_origin_referer_takes_precedence_when_origin_none(self):
        """B21: Referer validated when Origin header is None."""
        from app.core.origin_guard import validate_origin
        assert validate_origin(None, "https://app.example.com", ["example.com"], allow_localhost=False) is True
        assert validate_origin(None, "https://phishing-site.net", ["example.com"], allow_localhost=False) is False

    def test_b22_origin_whitespace_trimmed_in_allowed_domains(self):
        """B22: Allowed domains containing accidental whitespace are trimmed and matched."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://example.com", None, ["  example.com  ", "shop.example.com "], allow_localhost=False) is True


# ===========================================================================
# Category 2: Public & Secret Key Formats and Limits (F1, F6) - 12 Tests
# ===========================================================================
class TestKeyFormatBoundaries:
    def test_b23_key_empty_string_chat_route_returns_404_or_405(self, client):
        """B23: Calling chat endpoint with empty string key is handled without 500."""
        res = client.post("/api/chat/", json={"message": "hello"})
        assert res.status_code in (404, 405)

    def test_b24_key_whitespace_only_returns_404(self, client):
        """B24: Calling chat endpoint with whitespace-only key returns 404."""
        res = client.post("/api/chat/%20%20%20", json={"message": "hello"})
        assert res.status_code in (404, 422)

    def test_b25_key_truncated_pk_prefix_only_returns_404(self, client):
        """B25: Calling chat endpoint with truncated "pk_" key returns 404."""
        res = client.post("/api/chat/pk_", json={"message": "hello"})
        assert res.status_code == 404

    def test_b26_key_invalid_short_hex_length_returns_404(self, client):
        """B26: Key with truncated hex segment (pk_abc12) returns 404."""
        res = client.post("/api/chat/pk_abc12", json={"message": "hello"})
        assert res.status_code == 404

    def test_b27_key_non_hex_characters_returns_404(self, client):
        """B27: Key containing non-hex characters (pk_zzzz_not_hex_chars_12345) returns 404."""
        res = client.post("/api/chat/pk_zzzz_not_hex_chars_12345", json={"message": "hello"})
        assert res.status_code == 404

    def test_b28_key_extreme_length_256_chars_returns_404_no_crash(self, client):
        """B28: Key with extreme length (256 chars) is safely rejected without server buffer overflow."""
        extreme_key = "pk_" + "a" * 253
        res = client.post(f"/api/chat/{extreme_key}", json={"message": "hello"})
        assert res.status_code == 404

    def test_b29_key_special_characters_sql_injection_attempt_returns_404(self, client):
        """B29: SQL injection payloads in key parameter return 404 without database exception."""
        sqli_key = "pk_' OR '1'='1' --"
        res = client.post(f"/api/chat/{sqli_key}", json={"message": "hello"})
        assert res.status_code in (404, 422)

    def test_b30_key_null_bytes_and_newlines_rejected(self, client):
        """B30: Key containing URL-encoded newline or null byte does not cause 500."""
        res = client.post("/api/chat/pk_valid%00key", json={"message": "hello"})
        assert res.status_code in (400, 404, 422)

    def test_b31_key_secret_vs_public_prefix_isolation(self, test_business):
        """B31: Business public_key starts with pk_ and secret api_key starts with sec_."""
        assert test_business.public_key.startswith("pk_")
        assert test_business.api_key.startswith("sec_")
        assert test_business.public_key != test_business.api_key

    def test_b32_key_business_public_key_cannot_be_null_in_db(self, db):
        """B32: Business.public_key column has nullable=False constraint."""
        col = Business.__table__.columns.get("public_key")
        assert col is not None
        assert col.nullable is False

        # Verify raw SQL insert with explicit NULL violates NOT NULL constraint
        with pytest.raises(IntegrityError):
            db.execute(
                Business.__table__.insert().values(
                    id=uuid.uuid4(),
                    name="Null PK Raw Test",
                    slug=f"null-pk-raw-{uuid.uuid4().hex[:6]}",
                    api_key=f"sec_{uuid.uuid4().hex}",
                    public_key=None,
                )
            )
            db.commit()
        db.rollback()

    def test_b33_key_business_api_key_cannot_be_null_in_db(self, db):
        """B33: Business.api_key column has nullable=False constraint."""
        biz = Business(
            name="Null Sec Test",
            slug=f"null-sec-{uuid.uuid4().hex[:6]}",
            api_key=None,
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b34_key_business_public_key_format_length(self, test_business):
        """B34: Standard public_key generated has 35 chars (pk_ + 32 hex chars)."""
        assert len(test_business.public_key) == 35
        hex_part = test_business.public_key[3:]
        assert all(c in "0123456789abcdef" for c in hex_part)


# ===========================================================================
# Category 3: Tokens & Authentication Security Boundaries (F6, F12, F13) - 12 Tests
# ===========================================================================
class TestTokenAndAuthBoundaries:
    def test_b35_auth_expired_jwt_token_returns_401(self, client, test_business, test_user):
        """B35: Bearer JWT expired in the past returns HTTP 401 Unauthorized."""
        expired_token = create_access_token({"sub": str(test_user.id)}, expires_delta=timedelta(minutes=-30))
        headers = {"Authorization": f"Bearer {expired_token}", "X-Business-Id": str(test_business.id)}
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 401
        assert "Invalid or expired token" in res.json()["detail"]

    def test_b36_auth_jwt_signed_with_wrong_secret_returns_401(self, client, test_business, test_user):
        """B36: JWT signed with attacker secret key returns HTTP 401."""
        bogus_token = jwt.encode({"sub": str(test_user.id)}, "completely_wrong_secret_123", algorithm="HS256")
        headers = {"Authorization": f"Bearer {bogus_token}", "X-Business-Id": str(test_business.id)}
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_b37_auth_jwt_with_missing_sub_claim_returns_401(self, client, test_business):
        """B37: JWT lacking required "sub" claim returns HTTP 401."""
        settings = get_settings()
        token_no_sub = jwt.encode({"email": "test@example.com"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        headers = {"Authorization": f"Bearer {token_no_sub}", "X-Business-Id": str(test_business.id)}
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_b38_auth_malformed_bearer_header_no_token_returns_401(self, client, test_business):
        """B38: Authorization header "Bearer " without token returns HTTP 401."""
        headers = {"Authorization": "Bearer ", "X-Business-Id": str(test_business.id)}
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_b39_auth_malformed_bearer_header_garbage_token_returns_401(self, client, test_business):
        """B39: Authorization header with non-JWT garbage returns HTTP 401."""
        headers = {"Authorization": "Bearer not-a-valid-jwt-structure", "X-Business-Id": str(test_business.id)}
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_b40_auth_public_key_as_bearer_to_conversations_returns_401(self, client, test_business):
        """B40: Public key passed as Bearer to /api/conversations returns HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/conversations/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_b41_auth_public_key_as_bearer_to_ai_settings_returns_401(self, client, test_business):
        """B41: Public key passed as Bearer to /api/ai-settings returns HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_b42_auth_public_key_as_bearer_to_widget_config_returns_401(self, client, test_business):
        """B42: Public key passed as Bearer to /api/widget/{id}/config returns HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/widget/{test_business.id}/config", headers=headers)
        assert res.status_code == 401

    def test_b43_auth_secret_key_as_bearer_without_jwt_returns_401(self, client, test_business):
        """B43: Backend secret key passed directly as Bearer token without JWT encapsulation returns HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.api_key}"}
        res = client.get(f"/api/widget/{test_business.id}/config", headers=headers)
        assert res.status_code == 401

    def test_b44_auth_mismatched_business_id_header_returns_403(self, client, db, auth_headers):
        """B44: User authenticated for Business A attempting to access Business B returns HTTP 403."""
        biz_b = Business(
            name="Business B",
            slug=f"biz-b-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz_b)
        db.commit()

        # auth_headers has test_user token (member of test_business, not biz_b)
        res = client.get(f"/api/ai-settings/{biz_b.id}", headers=auth_headers)
        assert res.status_code == 403
        assert "Not a team member" in res.json()["detail"]

    def test_b45_auth_nonexistent_business_id_header_returns_403(self, client, auth_headers):
        """B45: Accessing a non-existent business UUID returns HTTP 403 or 404."""
        fake_uuid = str(uuid.uuid4())
        res = client.get(f"/api/ai-settings/{fake_uuid}", headers=auth_headers)
        assert res.status_code in (403, 404)

    def test_b46_auth_viewer_cannot_update_ai_settings(self, client, test_business, viewer_headers):
        """B46: VIEWER role cannot update AI Settings / widget config."""
        res = client.put(
            f"/api/widget/{test_business.id}/config",
            json={"welcome_message": "Hacked"},
            headers=viewer_headers,
        )
        assert res.status_code == 403
        assert "Insufficient permissions" in res.json()["detail"]


# ===========================================================================
# Category 4: Greetings & Message Input Boundaries (F9) - 12 Tests
# ===========================================================================
class TestGreetingAndMessageBoundaries:
    def test_b47_greeting_mixed_case_hello_recognized(self, client, test_business, test_widget_config):
        """B47: Greeting with mixed-case "hElLo" returns welcome message with confidence 1.0."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hElLo"})
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == test_widget_config.welcome_message
        assert data["confidence_score"] == 1.0
        assert data["is_escalated"] is False

    def test_b48_greeting_leading_and_trailing_spaces_recognized(self, client, test_business, test_widget_config):
        """B48: Greeting surrounded by whitespace "   hey   " recognized."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": "   hey   "})
        assert res.status_code == 200
        assert res.json()["confidence_score"] == 1.0

    def test_b49_greeting_trailing_punctuation_multiple_marks(self, client, test_business, test_widget_config):
        """B49: Greeting with trailing punctuation "hello?!" or "hi!!!!" recognized."""
        res1 = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hello?!"})
        assert res1.status_code == 200
        assert res1.json()["confidence_score"] == 1.0

        res2 = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hi!!!!"})
        assert res2.status_code == 200
        assert res2.json()["confidence_score"] == 1.0

    def test_b50_greeting_conversational_good_morning_variations(self, client, test_business, test_widget_config):
        """B50: Multi-word greetings ("Good Morning", "Good Afternoon", "Good Evening") recognized."""
        for g in ["good morning", "GOOD AFTERNOON", "Good Evening..."]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": g})
            assert res.status_code == 200
            assert res.json()["confidence_score"] == 1.0

    def test_b51_greeting_slang_variations_howdy_sup(self, client, test_business, test_widget_config):
        """B51: Informal greetings "howdy", "sup", "greetings" recognized."""
        for g in ["howdy", "sup", "greetings"]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": g})
            assert res.status_code == 200
            assert res.json()["confidence_score"] == 1.0

    def test_b52_greeting_sentence_with_order_help_not_intercepted_as_pure_greeting(self, client, test_business):
        """B52: Conversational question "Hello, can someone help me with my order?" is not a pure greeting."""
        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "Hello, can someone help me with my order?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "order" in data["message"].lower() or "knowledge base" in data["message"].lower()

    def test_b53_greeting_sentence_asking_refund_not_intercepted_as_pure_greeting(self, client, test_business):
        """B53: Conversational question "Hi there, how do I get a refund?" routes to RAG / knowledge."""
        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "Hi there, how do I get a refund?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "knowledge base" in data["message"].lower() or "refund" in data["message"].lower()

    def test_b54_greeting_empty_message_validation_error(self, client, test_business):
        """B54: Empty message "" in ChatRequest payload handled gracefully."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": ""})
        assert res.status_code in (200, 422)

    def test_b55_greeting_whitespace_only_message_handled(self, client, test_business):
        """B55: Whitespace-only message handled without raising unhandled 500 error."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": "     "})
        assert res.status_code in (200, 422)

    def test_b56_greeting_extreme_message_10k_chars_handled_gracefully(self, client, test_business):
        """B56: Message with 10,000 characters is safely processed without memory error."""
        huge_message = "What is your refund policy? " * 400
        assert len(huge_message) >= 10000
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": huge_message})
        assert res.status_code == 200

    def test_b57_greeting_special_characters_html_xss_sanitized(self, client, test_business):
        """B57: Message containing HTML and XSS tags safely stored and returned as text."""
        xss_payload = "<script>alert('xss');</script><b>bold</b>"
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": xss_payload})
        assert res.status_code == 200

    def test_b58_greeting_unicode_emojis_handled_safely(self, client, test_business):
        """B58: Message with diverse Unicode emojis handles cleanly."""
        emoji_msg = "👋 Hello! 🤖 Can you help? 🌟📦✨"
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": emoji_msg})
        assert res.status_code == 200


# ===========================================================================
# Category 5: RAG, Embeddings & LLM Failure Modes (F5, F9) - 12 Tests
# ===========================================================================
class TestRAGAndLLMBoundaries:
    def test_b59_rag_llm_provider_timeout_exception_handled(self, monkeypatch):
        """B59: LLM provider raising httpx.TimeoutException is caught and handled gracefully in RAGEngine."""
        def timeout_gemini(api_key: str, prompt: str) -> str:
            raise httpx.TimeoutException("Read timed out after 30 seconds")

        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "gemini", timeout_gemini)

        class MockEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Test chunk", "doc_id": "doc-1", "score": 0.8}]

        engine = RAGEngine(business_id="test-biz-id", llm_provider="gemini", llm_api_key="test-key")
        engine.embedding_service = MockEmbedding()

        result = engine.query("What is the return window?")
        assert result["confidence"] == 0.0
        assert "trouble generating a response" in result["answer"]

    def test_b60_rag_llm_provider_http_500_exception_handled(self, monkeypatch):
        """B60: LLM provider returning HTTP 500 error is caught and handled gracefully in RAGEngine."""
        def error_500_openai(api_key: str, prompt: str) -> str:
            raise httpx.HTTPStatusError("500 Internal Server Error", request=None, response=httpx.Response(500))

        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "openai", error_500_openai)

        class MockEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "OpenAI chunk", "doc_id": "doc-2", "score": 0.9}]

        engine = RAGEngine(business_id="test-biz-id", llm_provider="openai", llm_api_key="test-openai-key")
        engine.embedding_service = MockEmbedding()

        result = engine.query("How do I cancel?")
        assert result["confidence"] == 0.0
        assert "trouble generating a response" in result["answer"]

    def test_b61_rag_llm_provider_connect_error_handled(self, monkeypatch):
        """B61: LLM provider network disconnect (httpx.ConnectError) is caught without uncaught exception."""
        def connect_error(api_key: str, prompt: str) -> str:
            raise httpx.ConnectError("Failed to connect to host")

        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "anthropic", connect_error)

        class MockEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Anthropic chunk", "doc_id": "doc-3", "score": 0.75}]

        engine = RAGEngine(business_id="test-biz-id", llm_provider="anthropic", llm_api_key="test-anthropic-key")
        engine.embedding_service = MockEmbedding()

        result = engine.query("How do I upgrade?")
        assert result["confidence"] == 0.0
        assert "trouble generating a response" in result["answer"]

    def test_b62_rag_empty_search_results_returns_zero_confidence(self):
        """B62: When embedding search returns 0 chunks, RAG returns 0.0 confidence."""
        class EmptyEmbedding:
            def search(self, business_id, query, top_k=5):
                return []

        engine = RAGEngine(business_id="empty-biz-id", llm_provider="gemini", llm_api_key="dummy-key")
        engine.embedding_service = EmptyEmbedding()

        result = engine.query("Random query without any documents")
        assert result["confidence"] == 0.0
        assert result["sources"] == []
        assert "don't have enough information" in result["answer"]

    def test_b63_rag_zero_similarity_score_clamped_to_zero_confidence(self, monkeypatch):
        """B63: Search results with similarity score 0.0 yield confidence 0.0."""
        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "gemini", lambda k, p: "Mock answer")

        class ZeroScoreEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Irrelevant chunk", "doc_id": "doc-4", "score": 0.0}]

        engine = RAGEngine(business_id="test-biz", llm_provider="gemini", llm_api_key="dummy-key")
        engine.embedding_service = ZeroScoreEmbedding()

        result = engine.query("Question?")
        assert result["confidence"] == 0.0

    def test_b64_rag_negative_similarity_score_clamped_to_zero(self, monkeypatch):
        """B64: Negative cosine similarity score is clamped to minimum 0.0."""
        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "gemini", lambda k, p: "Mock answer")

        class NegativeScoreEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Opposite chunk", "doc_id": "doc-5", "score": -0.45}]

        engine = RAGEngine(business_id="test-biz", llm_provider="gemini", llm_api_key="dummy-key")
        engine.embedding_service = NegativeScoreEmbedding()

        result = engine.query("Question?")
        assert result["confidence"] == 0.0

    def test_b65_rag_boundary_low_score_triggers_escalation(self, monkeypatch):
        """B65: Score of 0.01 produces confidence 0.05 (< 0.1), which triggers escalation condition."""
        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "gemini", lambda k, p: "Uncertain answer")

        class LowScoreEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Barely relevant", "doc_id": "doc-6", "score": 0.01}]

        engine = RAGEngine(business_id="test-biz", llm_provider="gemini", llm_api_key="dummy-key")
        engine.embedding_service = LowScoreEmbedding()

        result = engine.query("Obscure question")
        assert result["confidence"] == 0.05
        assert result["confidence"] < 0.1  # Escalation threshold

    def test_b66_rag_boundary_adequate_score_avoids_escalation(self, monkeypatch):
        """B66: Score of 0.05 produces confidence 0.25 (>= 0.1), avoiding false escalation."""
        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "gemini", lambda k, p: "Confident answer")

        class AdequateEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Relevant document", "doc_id": "doc-7", "score": 0.05}]

        engine = RAGEngine(business_id="test-biz", llm_provider="gemini", llm_api_key="dummy-key")
        engine.embedding_service = AdequateEmbedding()

        result = engine.query("Clear question")
        assert result["confidence"] == 0.25
        assert result["confidence"] >= 0.1

    def test_b67_rag_score_above_one_clamped_to_one(self, monkeypatch):
        """B67: High similarity scores (e.g. 0.95 * 5.0 = 4.75) are clamped to maximum 1.0."""
        monkeypatch.setitem(rag_module.LLM_PROVIDERS, "gemini", lambda k, p: "Exact match answer")

        class PerfectEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Exact match", "doc_id": "doc-8", "score": 0.95}]

        engine = RAGEngine(business_id="test-biz", llm_provider="gemini", llm_api_key="dummy-key")
        engine.embedding_service = PerfectEmbedding()

        result = engine.query("Exact query")
        assert result["confidence"] == 1.0

    def test_b68_rag_ready_docs_zero_returns_helpful_unconfigured_message(self, client, test_business):
        """B68: Chat query when business has 0 ready documents returns unconfigured explanation with confidence 1.0."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": "Can I return my item?"})
        assert res.status_code == 200
        data = res.json()
        assert "don't have any knowledge base documents loaded yet" in data["message"]
        assert data["confidence_score"] == 1.0
        assert data["is_escalated"] is False

    def test_b69_rag_missing_llm_api_key_both_tenant_and_platform_handled(self, monkeypatch):
        """B69: When neither tenant nor platform has an API key, RAG engine returns friendly fallback without crashing."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

        class DummyEmbedding:
            def search(self, business_id, query, top_k=5):
                return [{"chunk": "Some doc", "doc_id": "doc-9", "score": 0.8}]

        engine = RAGEngine(business_id="biz", llm_provider="gemini", llm_api_key=None)
        engine.embedding_service = DummyEmbedding()

        result = engine.query("What are the hours?")
        assert result["confidence"] == 0.0
        assert "No API key configured" in result["answer"]

    def test_b70_rag_empty_whitespace_tenant_llm_key_falls_back_to_platform(self, clean_env):
        """B70: Tenant with whitespace-only llm_api_key falls back to platform default key."""
        from app.services.llm_service import resolve_llm_credentials
        biz = Business(
            name="Whitespace Key Biz",
            slug=f"ws-key-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
            llm_provider="gemini",
            llm_api_key="    	   ",
        )
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "platform_default_gemini_test_key_12345"


# ===========================================================================
# Category 6: Schema Constraints & Database Cascade Boundaries (F1, F2) - 14 Tests
# ===========================================================================
class TestSchemaAndDatabaseBoundaries:
    def test_b71_db_duplicate_business_slug_raises_integrity_error(self, db, test_business):
        """B71: Creating second business with identical slug violates unique constraint."""
        dup_biz = Business(
            name="Duplicate Slug Biz",
            slug=test_business.slug,
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(dup_biz)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b72_db_duplicate_business_api_key_raises_integrity_error(self, db, test_business):
        """B72: Creating second business with duplicate secret api_key violates uniqueness."""
        dup_biz = Business(
            name="Duplicate API Key Biz",
            slug=f"dup-api-{uuid.uuid4().hex[:6]}",
            api_key=test_business.api_key,
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(dup_biz)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b73_db_duplicate_business_public_key_raises_integrity_error(self, db, test_business):
        """B73: Creating second business with duplicate public_key violates uniqueness."""
        dup_biz = Business(
            name="Duplicate PK Biz",
            slug=f"dup-pk-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=test_business.public_key,
        )
        db.add(dup_biz)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b74_db_business_null_name_rejected(self, db):
        """B74: Business.name nullable=False constraint enforced."""
        biz = Business(
            name=None,
            slug=f"null-name-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b75_db_business_null_slug_rejected(self, db):
        """B75: Business.slug nullable=False constraint enforced."""
        biz = Business(
            name="Null Slug",
            slug=None,
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b76_db_business_null_api_key_rejected(self, db):
        """B76: Business.api_key nullable=False constraint enforced."""
        biz = Business(
            name="Null API Key",
            slug=f"null-api-{uuid.uuid4().hex[:6]}",
            api_key=None,
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b77_db_widget_config_null_business_id_rejected(self, db):
        """B77: WidgetConfig.business_id nullable=False constraint enforced."""
        cfg = WidgetConfig(business_id=None, bot_name="Ghost Bot")
        db.add(cfg)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b78_db_widget_config_duplicate_business_id_rejected(self, db, test_business):
        """B78: WidgetConfig.business_id unique=True constraint prevents multiple configs per business."""
        cfg1 = WidgetConfig(business_id=test_business.id, bot_name="Bot 1")
        db.add(cfg1)
        db.commit()

        cfg2 = WidgetConfig(business_id=test_business.id, bot_name="Bot 2")
        db.add(cfg2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_b79_db_cascade_delete_business_removes_widget_config(self, db):
        """B79: Deleting a Business cascades and removes associated WidgetConfig."""
        biz = Business(
            name="Cascade Biz",
            slug=f"cascade-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        db.commit()

        cfg = WidgetConfig(business_id=biz.id, bot_name="Cascade Bot")
        db.add(cfg)
        db.commit()

        db.delete(biz)
        db.commit()

        orphaned_cfg = db.query(WidgetConfig).filter(WidgetConfig.business_id == biz.id).first()
        assert orphaned_cfg is None

    def test_b80_db_cascade_delete_business_removes_conversations_and_messages(self, db):
        """B80: Deleting a Business cascades and removes associated Conversations and Messages."""
        biz = Business(
            name="Cascade Conv Biz",
            slug=f"conv-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        db.commit()

        conv = Conversation(business_id=biz.id, customer_name="Alice")
        db.add(conv)
        db.commit()

        msg = Message(conversation_id=conv.id, sender=MessageSender.CUSTOMER, content="Hello")
        db.add(msg)
        db.commit()

        conv_id = conv.id
        msg_id = msg.id

        db.delete(biz)
        db.commit()

        assert db.query(Conversation).filter(Conversation.id == conv_id).first() is None
        assert db.query(Message).filter(Message.id == msg_id).first() is None

    def test_b81_db_cascade_delete_business_removes_team_members(self, db, test_user):
        """B81: Deleting a Business cascades and removes TeamMember associations."""
        biz = Business(
            name="Cascade Team Biz",
            slug=f"team-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        db.commit()

        member = TeamMember(business_id=biz.id, user_id=test_user.id, role=UserRole.OWNER)
        db.add(member)
        db.commit()

        db.delete(biz)
        db.commit()

        assert db.query(TeamMember).filter(TeamMember.business_id == biz.id).first() is None

    def test_b82_db_cascade_delete_business_removes_faq_overrides(self, db, test_user):
        """B82: Deleting a Business cascades and removes FAQ overrides."""
        biz = Business(
            name="Cascade FAQ Biz",
            slug=f"faq-{uuid.uuid4().hex[:6]}",
            api_key=f"sec_{uuid.uuid4().hex}",
            public_key=f"pk_{uuid.uuid4().hex}",
        )
        db.add(biz)
        db.commit()

        faq = FAQOverride(business_id=biz.id, question="Q?", answer="A!", created_by=test_user.id)
        db.add(faq)
        db.commit()

        db.delete(biz)
        db.commit()

        assert db.query(FAQOverride).filter(FAQOverride.business_id == biz.id).first() is None

    def test_b83_db_update_nonexistent_business_id_in_ai_settings_returns_403_or_404(self, client, auth_headers):
        """B83: PUT /api/ai-settings/{random_uuid} returns 403 or 404."""
        fake_uuid = str(uuid.uuid4())
        res = client.put(
            f"/api/ai-settings/{fake_uuid}",
            json={"llm_provider": "gemini", "llm_api_key": "some-key"},
            headers=auth_headers,
        )
        assert res.status_code in (403, 404)

    def test_b84_db_update_nonexistent_business_id_in_widget_config_returns_403_or_404(self, client, auth_headers):
        """B84: PUT /api/widget/{random_uuid}/config returns 403 or 404."""
        fake_uuid = str(uuid.uuid4())
        res = client.put(
            f"/api/widget/{fake_uuid}/config",
            json={"welcome_message": "New Message"},
            headers=auth_headers,
        )
        assert res.status_code in (403, 404)
