"""
Unit and integration tests for Origin Guard Engine and Domain Whitelisting.
Covers extract_domain, validate_origin, and route-level HTTP 403 enforcement.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.origin_guard import extract_domain, validate_origin, clean_domain_entry
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.user import User


# ===========================================================================
# 1. Unit Tests: clean_domain_entry
# ===========================================================================
class TestCleanDomainEntry:
    def test_clean_standard_domains(self):
        assert clean_domain_entry("example.com") == "example.com"
        assert clean_domain_entry("shop.example.com") == "shop.example.com"

    def test_strip_schemes(self):
        assert clean_domain_entry("https://example.com") == "example.com"
        assert clean_domain_entry("http://shop.example.com") == "shop.example.com"

    def test_strip_ports_paths_and_queries(self):
        assert clean_domain_entry("https://example.com:8443/checkout?ref=1#top") == "example.com"
        assert clean_domain_entry("http://localhost:3000/") == "localhost"

    def test_strip_wildcards(self):
        assert clean_domain_entry("*.example.com") == "example.com"
        assert clean_domain_entry(".example.com") == "example.com"
        assert clean_domain_entry("*.staging.app.io") == "staging.app.io"

    def test_whitespace_and_invalid_inputs(self):
        assert clean_domain_entry("  example.com  ") == "example.com"
        assert clean_domain_entry("") is None
        assert clean_domain_entry("   ") is None
        assert clean_domain_entry("*") is None
        assert clean_domain_entry(None) is None


# ===========================================================================
# 2. Unit Tests: extract_domain
# ===========================================================================
class TestExtractDomain:
    def test_extract_from_origin(self):
        assert extract_domain("https://example.com", None) == "example.com"
        assert extract_domain("http://example.com:8080/path?q=1#hash", None) == "example.com"
        assert extract_domain("HTTPS://SHOP.EXAMPLE.COM", None) == "shop.example.com"

    def test_extract_origin_precedence_over_referer(self):
        assert extract_domain("https://origin.example.com", "https://referer.example.com") == "origin.example.com"

    def test_fallback_to_referer(self):
        assert extract_domain(None, "https://shop.example.com/checkout") == "shop.example.com"
        assert extract_domain("", "https://app.example.com/pricing") == "app.example.com"
        assert extract_domain("   ", "http://docs.example.com:3000") == "docs.example.com"

    def test_null_and_file_origins(self):
        assert extract_domain("null", None) == "null"
        assert extract_domain("NULL", None) == "null"
        assert extract_domain("file:///home/user/index.html", None) == "null"
        assert extract_domain("file://", None) == "null"

    def test_untrusted_schemes_return_none(self):
        assert extract_domain("data:text/html,<script>alert(1)</script>", None) is None
        assert extract_domain("data:text/html;base64,PHNjcmlwdD4=", None) is None
        assert extract_domain("javascript:alert(1)", None) is None
        assert extract_domain("vbscript:msgbox(1)", None) is None

    def test_localhost_and_loopback(self):
        assert extract_domain("http://localhost:3000", None) == "localhost"
        assert extract_domain("http://127.0.0.1:8080", None) == "127.0.0.1"
        assert extract_domain("http://[::1]:5173", None) == "::1"
        assert extract_domain("http://0.0.0.0:8000", None) == "0.0.0.0"

    def test_punycode_idn(self):
        assert extract_domain("https://xn--bcher-kva.example.com", None) == "xn--bcher-kva.example.com"

    def test_missing_both_headers_returns_none(self):
        assert extract_domain(None, None) is None
        assert extract_domain("", "") is None
        assert extract_domain("  ", "   ") is None


# ===========================================================================
# 3. Unit Tests: validate_origin
# ===========================================================================
class TestValidateOrigin:
    def test_exact_domain_match(self):
        assert validate_origin("https://example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("http://example.com", None, ["example.com"], allow_localhost=False) is True

    def test_subdomain_matching(self):
        assert validate_origin("https://shop.example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("https://checkout.staging.example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("https://deep.sub.dom.example.com", None, ["*.example.com"], allow_localhost=False) is True

    def test_spoofing_attempts_blocked(self):
        # Prefix spoofing
        assert validate_origin("https://evil-example.com", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("https://notexample.com", None, ["example.com"], allow_localhost=False) is False
        # Suffix spoofing
        assert validate_origin("https://example.com.evil.co", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("https://example.com.attacker.com", None, ["example.com"], allow_localhost=False) is False

    def test_localhost_enabled(self):
        assert validate_origin("http://localhost:3000", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://127.0.0.1:8080", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://[::1]:5173", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://0.0.0.0:8000", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("null", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("file:///app/index.html", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin(None, None, ["example.com"], allow_localhost=True) is True

    def test_localhost_disabled(self):
        assert validate_origin("http://localhost:3000", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("http://127.0.0.1:8080", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("http://[::1]:5173", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("null", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("file:///app/index.html", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin(None, None, ["example.com"], allow_localhost=False) is False

    def test_explicitly_whitelisted_localhost_when_flag_false(self):
        assert validate_origin("http://localhost:3000", None, ["localhost"], allow_localhost=False) is True
        assert validate_origin("http://127.0.0.1:8080", None, ["127.0.0.1"], allow_localhost=False) is True

    def test_untrusted_schemes_blocked_regardless_of_localhost(self):
        assert validate_origin("data:text/html,<script>", None, ["example.com"], allow_localhost=True) is False
        assert validate_origin("javascript:void(0)", None, ["example.com"], allow_localhost=True) is False

    def test_allowed_domains_cleaning_tolerance(self):
        whitelist = ["  example.com  ", "*.shop.com", "https://app.co:8443/"]
        assert validate_origin("https://example.com", None, whitelist, allow_localhost=False) is True
        assert validate_origin("https://sub.shop.com", None, whitelist, allow_localhost=False) is True
        assert validate_origin("https://app.co", None, whitelist, allow_localhost=False) is True


# ===========================================================================
# 4. Route Integration Tests: Widget Embed & Chat Endpoints
# ===========================================================================
class TestRouteOriginGuardIntegration:
    def test_embed_allowed_origin_returns_200(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        res = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200
        assert res.json()["bot_name"] == test_widget_config.bot_name

    def test_embed_unauthorized_origin_returns_403(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        res = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": "https://attacker.com"},
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Origin not allowed"

    def test_embed_referer_fallback_succeeds(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        res = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Referer": "https://app.example.com/checkout"},
        )
        assert res.status_code == 200

    def test_embed_referer_fallback_unauthorized_403(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        res = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Referer": "https://phishing.site/page"},
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Origin not allowed"

    def test_chat_allowed_origin_returns_200(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello"},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200
        assert res.json()["message"] == test_widget_config.welcome_message

    def test_chat_unauthorized_origin_returns_403(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello"},
            headers={"Origin": "https://attacker-domain.org"},
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Origin not allowed"

    def test_chat_localhost_blocked_when_allow_localhost_false(
        self, client: TestClient, db: Session, test_business: Business, test_widget_config: WidgetConfig
    ):
        test_widget_config.allow_localhost = False
        db.commit()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Origin not allowed"

    def test_chat_backward_compatibility_with_api_key(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "hello"},
            headers={"Origin": "https://example.com"},
        )
        assert res.status_code == 200

    def test_widget_config_update_dynamically_updates_allowed_domains(
        self, client: TestClient, db: Session, test_business: Business, test_widget_config: WidgetConfig, auth_headers: dict
    ):
        update_payload = {
            "allowed_domains": ["newstore.org"],
            "allow_localhost": False,
        }
        put_res = client.put(
            f"/api/widget/{test_business.id}/config",
            json=update_payload,
            headers=auth_headers,
        )
        assert put_res.status_code == 200
        assert put_res.json()["allowed_domains"] == ["newstore.org"]
        assert put_res.json()["allow_localhost"] is False

        # Old domain now receives 403
        old_res = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": "https://example.com"},
        )
        assert old_res.status_code == 403

        # New domain succeeds with 200
        new_res = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": "https://newstore.org"},
        )
        assert new_res.status_code == 200
