"""
Adversarial Stress-Testing and Fuzzing Suite for SupportAI Origin Guard Engine.
Empirically challenges:
1. URL Scheme variations (mixed case, missing schemes, dangerous pseudo-schemes, blob, file)
2. Hostname fuzzing & port injection (:80, :443, :8000, :65535, invalid ports :abc, :-1)
3. Userinfo injection & host spoofing (user:pass@host, attacker@allowed, allowed@attacker)
4. Domain spoofing attacks (prefix, suffix, multi-level subdomains, unicode homoglyphs, punycode)
5. IPv6 bracketed literals vs unbracketed vs mapped/link-local addresses
6. Bracketed userinfo host injection attacks (CVE-style parser evasion)
7. Null origin, empty headers, and whitespace permutations
8. Dev mode toggling (allow_localhost=True vs False) and dev host spoofing
9. Route-level HTTP 403 enforcement and database mutation prevention
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.origin_guard import extract_domain, validate_origin, clean_domain_entry
from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, Message


# ===========================================================================
# 1. URL Scheme Variations & Pseudo-Schemes
# ===========================================================================
class TestAdversarialSchemeVariations:
    """Stress-tests scheme variations, casing, and browser pseudo-schemes."""

    @pytest.mark.parametrize("scheme_prefix", [
        "http://",
        "https://",
        "HTTP://",
        "HTTPS://",
        "hTTp://",
        "hTTps://",
        "HtTpS://",
        "ws://",
        "wss://",
        "WS://",
        "WSS://",
    ])
    def test_case_insensitive_and_supported_schemes(self, scheme_prefix: str):
        origin = f"{scheme_prefix}example.com"
        assert extract_domain(origin, None) == "example.com"
        assert validate_origin(origin, None, ["example.com"], allow_localhost=False) is True

    @pytest.mark.parametrize("raw_input", [
        "example.com",
        "shop.example.com",
        "example.com:8080",
        "//example.com",
        "//shop.example.com:443",
    ])
    def test_missing_scheme_handling(self, raw_input: str):
        extracted = extract_domain(raw_input, None)
        assert extracted in ("example.com", "shop.example.com")
        assert validate_origin(raw_input, None, ["example.com"], allow_localhost=False) is True

    @pytest.mark.parametrize("blocked_scheme_uri", [
        "javascript:alert(1)",
        "JAVASCRIPT:alert(document.cookie)",
        "javascript:void(0)",
        "data:text/html,<script>alert(1)</script>",
        "DATA:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        "data:application/json,{\"foo\":\"bar\"}",
        "vbscript:msgbox(1)",
        "VBSCRIPT:msgbox(1)",
        "about:blank",
        "about:srcdoc",
        "ABOUT:BLANK",
    ])
    def test_dangerous_pseudo_schemes_strictly_rejected(self, blocked_scheme_uri: str):
        """Dangerous pseudo-schemes must return None from extract_domain and False from validate_origin."""
        assert extract_domain(blocked_scheme_uri, None) is None
        assert validate_origin(blocked_scheme_uri, None, ["example.com"], allow_localhost=True) is False
        assert validate_origin(blocked_scheme_uri, None, ["example.com"], allow_localhost=False) is False

    @pytest.mark.parametrize("blob_uri", [
        "blob:https://example.com/d3b07384-d113-4f4e-a1e4-984e7276589b",
        "blob:https://attacker.com/uuid-here",
        "blob:http://localhost:3000/some-guid",
    ])
    def test_blob_urls_rejected_or_unmatched(self, blob_uri: str):
        """Blob URLs are internal resource URIs and must not be granted origin access."""
        assert validate_origin(blob_uri, None, ["example.com"], allow_localhost=False) is False

    @pytest.mark.parametrize("file_uri", [
        "file:///home/user/app/index.html",
        "file:///C:/Users/test/index.html",
        "file://",
        "file:",
    ])
    def test_file_scheme_maps_to_null_origin(self, file_uri: str):
        """Local file URLs map to 'null' origin: allowed in dev mode, blocked in prod mode."""
        assert extract_domain(file_uri, None) == "null"
        assert validate_origin(file_uri, None, ["example.com"], allow_localhost=True) is True
        assert validate_origin(file_uri, None, ["example.com"], allow_localhost=False) is False


# ===========================================================================
# 2. Hostname Fuzzing, Port & Userinfo Injection
# ===========================================================================
class TestAdversarialHostnameFuzzing:
    """Fuzzes port numbers, userinfo credentials, and query/fragment payloads."""

    @pytest.mark.parametrize("port", [
        ":80",
        ":443",
        ":8000",
        ":8080",
        ":3000",
        ":5173",
        ":0",
        ":1",
        ":65535",
        ":abc",
        ":99999",
        ":-1",
    ])
    def test_port_injection_stripping(self, port: str):
        origin = f"https://example.com{port}"
        assert extract_domain(origin, None) == "example.com"
        assert validate_origin(origin, None, ["example.com"], allow_localhost=False) is True

    @pytest.mark.parametrize("userinfo_origin,expected_host,expected_valid", [
        ("https://user:pass@example.com", "example.com", True),
        ("https://admin@example.com", "example.com", True),
        ("https://user:pass@example.com:8443", "example.com", True),
        ("https://attacker.com:secret@example.com", "example.com", True),
        ("https://example.com@attacker.com", "attacker.com", False),
        ("https://example.com:password@attacker.com", "attacker.com", False),
        ("https://example.com:443@attacker.com", "attacker.com", False),
        ("https://user@attacker.com", "attacker.com", False),
    ])
    def test_userinfo_injection_resolution(self, userinfo_origin: str, expected_host: str, expected_valid: bool):
        """Userinfo must not deceive the parser into selecting the credential as the host."""
        extracted = extract_domain(userinfo_origin, None)
        assert extracted == expected_host
        assert validate_origin(userinfo_origin, None, ["example.com"], allow_localhost=False) is expected_valid

    @pytest.mark.parametrize("query_hash_origin", [
        "https://attacker.com/?allowed=example.com",
        "https://attacker.com/?redirect=https://example.com",
        "https://attacker.com/#example.com",
        "https://attacker.com/#/example.com",
        "https://attacker.com/example.com",
        "https://attacker.com/path/to/page?ref=example.com#token",
    ])
    def test_path_query_fragment_payloads_do_not_spoof_host(self, query_hash_origin: str):
        assert extract_domain(query_hash_origin, None) == "attacker.com"
        assert validate_origin(query_hash_origin, None, ["example.com"], allow_localhost=False) is False


# ===========================================================================
# 3. Domain Spoofing Attacks
# ===========================================================================
class TestAdversarialSpoofing:
    """Verifies immunity against prefix, suffix, and homoglyph domain spoofing."""

    @pytest.mark.parametrize("prefix_spoof", [
        "https://attacker-example.com",
        "https://evil-example.com",
        "https://fakeexample.com",
        "https://notexample.com",
        "https://myexample.com",
        "https://the-example.com",
        "https://subexample.com",
    ])
    def test_prefix_spoofing_blocked(self, prefix_spoof: str):
        assert validate_origin(prefix_spoof, None, ["example.com"], allow_localhost=False) is False

    @pytest.mark.parametrize("suffix_spoof", [
        "https://example.com.attacker.com",
        "https://example.com.evil.co",
        "https://example.com.org",
        "https://example.computer",
        "https://example.company",
        "https://example.com.fake.io",
        "https://shop.example.com.attacker.com",
    ])
    def test_suffix_spoofing_blocked(self, suffix_spoof: str):
        assert validate_origin(suffix_spoof, None, ["example.com"], allow_localhost=False) is False

    @pytest.mark.parametrize("valid_subdomain", [
        "https://shop.example.com",
        "https://checkout.example.com",
        "https://app.staging.example.com",
        "https://a.b.c.d.example.com",
    ])
    def test_valid_subdomains_allowed(self, valid_subdomain: str):
        assert validate_origin(valid_subdomain, None, ["example.com"], allow_localhost=False) is True
        assert validate_origin(valid_subdomain, None, ["*.example.com"], allow_localhost=False) is True

    @pytest.mark.parametrize("homoglyph_origin", [
        "https://exаmple.com",        # Cyrillic small letter a (U+0430)
        "https://exαmple.com",        # Greek small letter alpha (U+03B1)
        "https://xn--exmple-e1a.com", # Punycode encoded homoglyph
    ])
    def test_homoglyphs_and_punycode_do_not_match_ascii(self, homoglyph_origin: str):
        assert validate_origin(homoglyph_origin, None, ["example.com"], allow_localhost=False) is False


# ===========================================================================
# 4. IPv6 Formatting & Whitelist Parsing
# ===========================================================================
class TestAdversarialIPv6Formatting:
    """Verifies IPv6 bracketed vs unbracketed literals and whitelist cleaning."""

    @pytest.mark.parametrize("ipv6_loopback", [
        "http://[::1]",
        "http://[::1]:8080",
        "http://[::1]:3000",
        "[::1]",
        "::1",
    ])
    def test_ipv6_loopback_allowed_under_dev_mode(self, ipv6_loopback: str):
        assert validate_origin(ipv6_loopback, None, ["example.com"], allow_localhost=True) is True

    @pytest.mark.parametrize("non_loopback_ipv6", [
        "http://[2001:db8::1]",
        "http://[2001:db8::1]:8080",
        "http://[fe80::1]",
        "http://[fe80::1]:8000",
        "http://[::ffff:127.0.0.1]",
        "http://[::ffff:127.0.0.1]:8080",
    ])
    def test_non_loopback_ipv6_rejected_under_dev_mode(self, non_loopback_ipv6: str):
        """Non-loopback IPv6 addresses are not dev hosts and must be rejected."""
        assert validate_origin(non_loopback_ipv6, None, ["example.com"], allow_localhost=True) is False

    def test_explicit_bracketed_ipv6_whitelist(self):
        """When allow_localhost=False, bracketed [::1] in allowed_domains must permit [::1]."""
        assert validate_origin("http://[::1]:8080", None, ["[::1]"], allow_localhost=False) is True

    def test_explicit_unbracketed_ipv6_whitelist(self):
        """
        FINDING CHALLENGE:
        When an administrator configures allowed_domains = ["::1"], clean_domain_entry("::1")
        must NOT truncate the entry to None via colon splitting.
        """
        cleaned = clean_domain_entry("::1")
        assert cleaned is not None, "clean_domain_entry('::1') returned None; unbracketed IPv6 truncated by colon-split!"
        assert validate_origin("http://[::1]:8080", None, ["::1"], allow_localhost=False) is True


# ===========================================================================
# 5. Critical Vulnerability: Bracketed Userinfo Host Injection
# ===========================================================================
class TestBracketedUserinfoHostInjection:
    """
    CRITICAL EMPIRICAL CHALLENGE:
    Evaluates parser behavior when bracketed userinfo is injected into the URL:
    e.g. http://[example.com]@attacker.com or http://[::1]@attacker.com.

    A secure Origin Guard parser must identify 'attacker.com' as the host
    and REJECT the request. If the parser extracts 'example.com' or '::1',
    an attacker on attacker.com can completely bypass Origin Guard!
    """

    def test_bracketed_domain_userinfo_injection_blocked(self):
        """An attacker sending Origin: http://[example.com]@attacker.com must NOT bypass whitelist."""
        origin = "http://[example.com]@attacker.com"
        # The true host is attacker.com, NOT example.com!
        is_valid = validate_origin(origin, None, ["example.com"], allow_localhost=False)
        assert is_valid is False, (
            "CRITICAL VULNERABILITY: validate_origin allowed 'http://[example.com]@attacker.com' "
            "against whitelist ['example.com']! Fallback parser extracted bracketed userinfo as host."
        )

    def test_bracketed_loopback_userinfo_injection_blocked(self):
        """An attacker sending Origin: http://[::1]@attacker.com must NOT bypass dev mode."""
        origin = "http://[::1]@attacker.com"
        # The true host is attacker.com, NOT ::1!
        is_valid = validate_origin(origin, None, ["example.com"], allow_localhost=True)
        assert is_valid is False, (
            "CRITICAL VULNERABILITY: validate_origin allowed 'http://[::1]@attacker.com' "
            "under allow_localhost=True! Fallback parser extracted userinfo '[::1]' as dev host."
        )


# ===========================================================================
# 6. Null Origin, Whitespace & Header Precedence
# ===========================================================================
class TestNullAndWhitespacePermutations:
    """Tests null origins, whitespace padding, and Origin vs Referer precedence."""

    @pytest.mark.parametrize("null_origin", [
        "null",
        "NULL",
        "  null  ",
        "\tnull\n",
    ])
    def test_null_origin_handling(self, null_origin: str):
        assert extract_domain(null_origin, None) == "null"
        assert validate_origin(null_origin, None, ["example.com"], allow_localhost=True) is True
        assert validate_origin(null_origin, None, ["example.com"], allow_localhost=False) is False

    @pytest.mark.parametrize("empty_val", [None, "", "   ", "\t\r\n"])
    def test_both_headers_empty_handling(self, empty_val: str | None):
        assert extract_domain(empty_val, empty_val) is None
        assert validate_origin(empty_val, empty_val, ["example.com"], allow_localhost=True) is True
        assert validate_origin(empty_val, empty_val, ["example.com"], allow_localhost=False) is False

    def test_origin_precedence_over_referer_when_origin_valid(self):
        """When Origin is allowed, it succeeds even if Referer is an attacker domain."""
        assert validate_origin(
            origin="https://example.com",
            referer="https://attacker.com/page",
            allowed_domains=["example.com"],
            allow_localhost=False,
        ) is True

    def test_origin_precedence_over_referer_when_origin_invalid(self):
        """When Origin is attacker.com, it must be BLOCKED even if Referer is example.com."""
        assert validate_origin(
            origin="https://attacker.com",
            referer="https://example.com/checkout",
            allowed_domains=["example.com"],
            allow_localhost=False,
        ) is False

    def test_referer_fallback_when_origin_absent(self):
        """When Origin is absent, valid Referer succeeds."""
        assert validate_origin(
            origin=None,
            referer="https://example.com/checkout",
            allowed_domains=["example.com"],
            allow_localhost=False,
        ) is True

    def test_referer_fallback_blocked_when_unauthorized(self):
        """When Origin is absent, invalid Referer fails."""
        assert validate_origin(
            origin=None,
            referer="https://attacker.com/checkout",
            allowed_domains=["example.com"],
            allow_localhost=False,
        ) is False


# ===========================================================================
# 7. Dev Mode Toggling & Dev Host Spoofing
# ===========================================================================
class TestAdversarialDevModeToggling:
    """Tests dev mode toggling and attacks designed to mimic dev hosts."""

    @pytest.mark.parametrize("dev_origin", [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:8080",
        "http://0.0.0.0",
        "http://0.0.0.0:8000",
        "http://[::1]",
        "http://[::1]:5173",
        "null",
        "file:///app/index.html",
    ])
    def test_dev_hosts_allowed_only_when_flag_true(self, dev_origin: str):
        assert validate_origin(dev_origin, None, ["example.com"], allow_localhost=True) is True
        assert validate_origin(dev_origin, None, ["example.com"], allow_localhost=False) is False

    @pytest.mark.parametrize("dev_spoof_origin", [
        "http://localhost.attacker.com",
        "http://attacker.com/localhost",
        "http://attacker-localhost.com",
        "http://localhost-evil.com",
        "http://evil.com?localhost",
        "http://evil.com#localhost",
        "http://127.0.0.1.attacker.com",
        "http://attacker.com:127001",
        "http://null.attacker.com",
        "http://attacker.com/null",
        "http://localhost:password@attacker.com",
        "http://127.0.0.1@attacker.com",
        "http://192.168.1.1:8000",
        "http://10.0.0.1:3000",
    ])
    def test_dev_spoofing_attempts_blocked_even_with_dev_mode_true(self, dev_spoof_origin: str):
        """Attacker hosts mimicking localhost must be blocked even when allow_localhost=True."""
        assert validate_origin(dev_spoof_origin, None, ["example.com"], allow_localhost=True) is False


# ===========================================================================
# 8. Route-Level Integration & Zero Side-Effect Verification
# ===========================================================================
class TestAdversarialRouteIntegration:
    """Verifies route-level 403 enforcement, payload schema, and side-effect immunity."""

    def test_embed_route_returns_403_on_unauthorized_origin(
        self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig
    ):
        res = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": "https://malicious-website.com"},
        )
        assert res.status_code == 403
        assert res.json() == {"detail": "Origin not allowed"}

    def test_chat_route_returns_403_on_unauthorized_origin(
        self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig
    ):
        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello"},
            headers={"Origin": "https://malicious-website.com"},
        )
        assert res.status_code == 403
        assert res.json() == {"detail": "Origin not allowed"}

    def test_token_auth_precedes_origin_guard_404_over_403(self, client: TestClient):
        """An invalid public key must return 404 Invalid API key even from an unauthorized origin."""
        res = client.get(
            "/api/widget/embed/pk_nonexistent_invalid_key",
            headers={"Origin": "https://malicious-website.com"},
        )
        assert res.status_code == 404
        assert res.json() == {"detail": "Invalid API key"}

    def test_blocked_chat_request_creates_no_conversations_or_messages(
        self, client: TestClient, db: Session, test_business: Business, test_widget_config: WidgetConfig
    ):
        """Security: rejected requests must cause zero database mutations (conversations or messages)."""
        conv_count_before = db.query(Conversation).filter(Conversation.business_id == test_business.id).count()
        msg_count_before = db.query(Message).count()

        res = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "Attacker payload trying to flood the DB"},
            headers={"Origin": "https://attacker.org"},
        )
        assert res.status_code == 403

        conv_count_after = db.query(Conversation).filter(Conversation.business_id == test_business.id).count()
        msg_count_after = db.query(Message).count()
        assert conv_count_after == conv_count_before
        assert msg_count_after == msg_count_before

    def test_route_bracketed_userinfo_exploit_must_be_403(
        self, client: TestClient, db: Session, test_business: Business, test_widget_config: WidgetConfig
    ):
        """
        CRITICAL ROUTE-LEVEL VULNERABILITY CHALLENGE:
        An attacker targeting the embed or chat endpoint using bracketed userinfo spoofing
        (Origin: http://[example.com]@attacker.com) MUST receive HTTP 403 Forbidden, NOT 200 OK.
        """
        test_widget_config.allowed_domains = ["example.com"]
        test_widget_config.allow_localhost = False
        db.commit()

        exploit_origin = "http://[example.com]@attacker.com"

        res_embed = client.get(
            f"/api/widget/embed/{test_business.public_key}",
            headers={"Origin": exploit_origin},
        )
        assert res_embed.status_code == 403, (
            f"ROUTE VULNERABILITY: /api/widget/embed returned {res_embed.status_code} "
            f"instead of 403 for exploit origin '{exploit_origin}'!"
        )

        res_chat = client.post(
            f"/api/chat/{test_business.public_key}",
            json={"message": "hello"},
            headers={"Origin": exploit_origin},
        )
        assert res_chat.status_code == 403, (
            f"ROUTE VULNERABILITY: /api/chat returned {res_chat.status_code} "
            f"instead of 403 for exploit origin '{exploit_origin}'!"
        )
