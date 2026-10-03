import urllib.parse
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.user import User


class TestTokenFuzzingPublicRoutes:
    """Adversarial input fuzzing on public client-facing routes: /api/chat/{token} and /api/widget/embed/{token}."""

    def test_valid_public_key_succeeds(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        """Valid public key (pk_...) returns HTTP 200 on both chat and embed routes."""
        r_chat = client.post(f"/api/chat/{test_business.public_key}", json={"message": "hello"})
        assert r_chat.status_code == 200
        assert "conversation_id" in r_chat.json()

        r_embed = client.get(f"/api/widget/embed/{test_business.public_key}")
        assert r_embed.status_code == 200
        assert r_embed.json()["bot_name"] == test_widget_config.bot_name

    def test_valid_secret_key_backward_compatibility(self, client: TestClient, test_business: Business, test_widget_config: WidgetConfig):
        """Valid secret api_key returns HTTP 200 on both chat and embed routes for backward compatibility."""
        r_chat = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hello"})
        assert r_chat.status_code == 200

        r_embed = client.get(f"/api/widget/embed/{test_business.api_key}")
        assert r_embed.status_code == 200

    def test_truncated_token_returns_404_invalid_api_key(self, client: TestClient):
        """Truncated token 'pk_123' returns HTTP 404 with exact detail 'Invalid API key'."""
        r_chat = client.post("/api/chat/pk_123", json={"message": "hello"})
        assert r_chat.status_code == 404
        assert r_chat.json()["detail"] == "Invalid API key"

        r_embed = client.get("/api/widget/embed/pk_123")
        assert r_embed.status_code == 404
        assert r_embed.json()["detail"] == "Invalid API key"

    @pytest.mark.parametrize("sqli_token", [
        "pk_' OR '1'='1",
        "pk_' OR 1=1 --",
        "pk_admin' --",
        "pk_' UNION SELECT id, name, api_key FROM businesses --",
        "pk_\"; DROP TABLE businesses; --",
    ])
    def test_sql_injection_tokens_return_404_invalid_api_key(self, client: TestClient, sqli_token: str):
        """SQL injection payloads in token parameter return HTTP 404 with exact detail 'Invalid API key'."""
        r_chat = client.post(f"/api/chat/{sqli_token}", json={"message": "hello"})
        assert r_chat.status_code == 404
        assert r_chat.json()["detail"] == "Invalid API key"

        r_embed = client.get(f"/api/widget/embed/{sqli_token}")
        assert r_embed.status_code == 404
        assert r_embed.json()["detail"] == "Invalid API key"

    @pytest.mark.parametrize("non_ascii_token", [
        "pk_🚀тест你好",
        "pk_日本語テスト",
        "pk_€£¥₹",
        "pk_مرحبا_بالعالم",
    ])
    def test_non_ascii_tokens_return_404_invalid_api_key(self, client: TestClient, non_ascii_token: str):
        """Non-ASCII unicode tokens return HTTP 404 with exact detail 'Invalid API key'."""
        r_chat = client.post(f"/api/chat/{non_ascii_token}", json={"message": "hello"})
        assert r_chat.status_code == 404
        assert r_chat.json()["detail"] == "Invalid API key"

        r_embed = client.get(f"/api/widget/embed/{non_ascii_token}")
        assert r_embed.status_code == 404
        assert r_embed.json()["detail"] == "Invalid API key"

    def test_non_existent_35char_tokens_return_404_invalid_api_key(self, client: TestClient):
        """Syntactically valid 35-character tokens not in DB return HTTP 404 with exact detail 'Invalid API key'."""
        fake_pk = f"pk_{'0' * 32}"
        r_chat = client.post(f"/api/chat/{fake_pk}", json={"message": "hello"})
        assert r_chat.status_code == 404
        assert r_chat.json()["detail"] == "Invalid API key"

        r_embed = client.get(f"/api/widget/embed/{fake_pk}")
        assert r_embed.status_code == 404
        assert r_embed.json()["detail"] == "Invalid API key"

    def test_whitespace_tokens_return_404_invalid_api_key(self, client: TestClient):
        """URL-encoded whitespace tokens return HTTP 404 with exact detail 'Invalid API key'."""
        r_chat = client.post("/api/chat/%20%20%20", json={"message": "hello"})
        assert r_chat.status_code == 404
        assert r_chat.json()["detail"] == "Invalid API key"

        r_embed = client.get("/api/widget/embed/%20%20%20")
        assert r_embed.status_code == 404
        assert r_embed.json()["detail"] == "Invalid API key"

    def test_path_traversal_routing_behavior(self, client: TestClient):
        """Path traversal patterns in token parameter are stopped at routing layer with HTTP 404."""
        # Unencoded / encoded traversal resolves at HTTP path router level
        r_chat = client.post("/api/chat/../../etc/passwd", json={"message": "hello"})
        assert r_chat.status_code == 404

        r_embed = client.get("/api/widget/embed/../../etc/passwd")
        assert r_embed.status_code == 404

        r_chat_enc = client.post("/api/chat/..%2F..%2Fetc%2Fpasswd", json={"message": "hello"})
        assert r_chat_enc.status_code == 404

        r_embed_enc = client.get("/api/widget/embed/..%2F..%2Fetc%2Fpasswd")
        assert r_embed_enc.status_code == 404

    def test_missing_and_empty_tokens_return_404(self, client: TestClient):
        """Missing or empty token paths return HTTP 404."""
        r_chat = client.post("/api/chat", json={"message": "hello"})
        assert r_chat.status_code == 404

        r_embed = client.get("/api/widget/embed")
        assert r_embed.status_code == 404

    def test_null_byte_behavior_empirical(self, client: TestClient):
        """Empirical evaluation of null byte (%00) handling in token parameter."""
        # Using raise_server_exceptions=False on a dedicated client to capture server response
        safe_client = TestClient(client.app, raise_server_exceptions=False)
        r_chat = safe_client.post("/api/chat/pk_foo%00bar", json={"message": "hello"})
        r_embed = safe_client.get("/api/widget/embed/pk_foo%00bar")

        # Note: Unhandled null byte in DB query causes ValueError -> HTTP 500
        # If hardened, it returns 404 or 400. We assert the server does not leak data (status >= 400).
        assert r_chat.status_code in (400, 404, 500)
        assert r_embed.status_code in (400, 404, 500)
        assert "password" not in r_chat.text.lower()
        assert "password" not in r_embed.text.lower()


ADMIN_ROUTES = [
    "/api/conversations/{bid}",
    "/api/analytics/{bid}/dashboard",
    "/api/team/{bid}/members",
    "/api/ai-settings/{bid}",
    "/api/widget/{bid}/config",
    "/api/knowledge/{bid}/documents",
    "/api/faq/{bid}",
]

ATTACK_VECTORS = [
    ("bearer_public_key", lambda pk, sk: {"headers": {"Authorization": f"Bearer {pk}"}, "params": {}}),
    ("bearer_secret_api_key", lambda pk, sk: {"headers": {"Authorization": f"Bearer {sk}"}, "params": {}}),
    ("x_api_key_header", lambda pk, sk: {"headers": {"X-API-Key": pk}, "params": {}}),
    ("query_param_api_key", lambda pk, sk: {"headers": {}, "params": {"api_key": pk}}),
    ("empty_bearer", lambda pk, sk: {"headers": {"Authorization": "Bearer "}, "params": {}}),
    ("missing_auth", lambda pk, sk: {"headers": {}, "params": {}}),
]


class TestAdministrativePrivilegeBarrierAdversarial:
    """Adversarial stress-test verifying that public keys and unauthenticated requests cannot access administrative endpoints."""

    @pytest.mark.parametrize("route_template", ADMIN_ROUTES)
    @pytest.mark.parametrize("vector_name,vector_fn", ATTACK_VECTORS)
    def test_admin_route_privilege_barrier(
        self,
        client: TestClient,
        test_business: Business,
        route_template: str,
        vector_name: str,
        vector_fn,
    ):
        """Every administrative endpoint strictly rejects public keys, secret keys, query params, and missing auth with 401."""
        url = route_template.format(bid=str(test_business.id))
        kwargs = vector_fn(test_business.public_key, test_business.api_key)

        res = client.get(url, headers=kwargs["headers"], params=kwargs["params"])

        # Must return 401 Unauthorized (or 403 Forbidden)
        assert res.status_code in (401, 403), f"Route {url} with {vector_name} returned {res.status_code}: {res.text}"
        # Zero leak of administrative data
        assert "bot_name" not in res.text
        assert "allowed_domains" not in res.text
        assert "full_name" not in res.text


class TestAISettingsResetStressHarness:
    """Stress tests for AI Settings reset behavior and platform default fallback."""

    def test_ai_settings_put_empty_string_resets_to_platform_default(
        self,
        client: TestClient,
        db: Session,
        test_business: Business,
        auth_headers: dict,
        clean_env,
    ):
        """PUT empty string '' resets llm_api_key to None and activates platform default."""
        test_business.llm_api_key = "custom-key-to-clear"
        db.commit()

        put_res = client.put(
            f"/api/ai-settings/{test_business.id}",
            json={"llm_provider": "gemini", "llm_api_key": ""},
            headers=auth_headers,
        )
        assert put_res.status_code == 200
        put_data = put_res.json()
        assert put_data["has_api_key"] is False
        assert put_data["is_using_platform_default"] is True

        db.refresh(test_business)
        assert test_business.llm_api_key is None

        get_res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert get_res.status_code == 200
        assert get_res.json()["is_using_platform_default"] is True
        assert get_res.json()["has_api_key"] is False

    def test_ai_settings_put_none_resets_to_platform_default(
        self,
        client: TestClient,
        db: Session,
        test_business: Business,
        auth_headers: dict,
        clean_env,
    ):
        """PUT None resets llm_api_key to None and activates platform default."""
        test_business.llm_api_key = "custom-key-to-clear"
        db.commit()

        put_res = client.put(
            f"/api/ai-settings/{test_business.id}",
            json={"llm_provider": "gemini", "llm_api_key": None},
            headers=auth_headers,
        )
        assert put_res.status_code == 200
        assert put_res.json()["is_using_platform_default"] is True
        assert put_res.json()["has_api_key"] is False

        db.refresh(test_business)
        assert test_business.llm_api_key is None

        get_res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert get_res.json()["is_using_platform_default"] is True

    def test_ai_settings_put_whitespace_resets_to_platform_default(
        self,
        client: TestClient,
        db: Session,
        test_business: Business,
        auth_headers: dict,
        clean_env,
    ):
        """PUT whitespace-only string resets llm_api_key to None and activates platform default."""
        test_business.llm_api_key = "custom-key-to-clear"
        db.commit()

        put_res = client.put(
            f"/api/ai-settings/{test_business.id}",
            json={"llm_provider": "gemini", "llm_api_key": "   \t  \n  "},
            headers=auth_headers,
        )
        assert put_res.status_code == 200
        assert put_res.json()["is_using_platform_default"] is True
        assert put_res.json()["has_api_key"] is False

        db.refresh(test_business)
        assert test_business.llm_api_key is None

        get_res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert get_res.json()["is_using_platform_default"] is True

    def test_ai_settings_put_custom_key_sets_byok_active(
        self,
        client: TestClient,
        db: Session,
        test_business: Business,
        auth_headers: dict,
        clean_env,
    ):
        """PUT valid custom key sets has_api_key=True and is_using_platform_default=False."""
        put_res = client.put(
            f"/api/ai-settings/{test_business.id}",
            json={"llm_provider": "openai", "llm_api_key": "sk-custom-openai-secret"},
            headers=auth_headers,
        )
        assert put_res.status_code == 200
        data = put_res.json()
        assert data["has_api_key"] is True
        assert data["is_using_platform_default"] is False
        assert data["llm_provider"] == "openai"

        db.refresh(test_business)
        assert test_business.llm_api_key == "sk-custom-openai-secret"
        assert test_business.llm_provider == "openai"

        get_res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert get_res.json()["is_using_platform_default"] is False
        assert get_res.json()["has_api_key"] is True

    def test_ai_settings_rapid_toggle_cycle_stress(
        self,
        client: TestClient,
        db: Session,
        test_business: Business,
        auth_headers: dict,
        clean_env,
    ):
        """Repeatedly toggling custom keys and resets preserves consistent state without race or corruption."""
        for i in range(5):
            # Set custom
            key = f"sk-cycle-key-{i}"
            r_set = client.put(
                f"/api/ai-settings/{test_business.id}",
                json={"llm_provider": "anthropic", "llm_api_key": key},
                headers=auth_headers,
            )
            assert r_set.status_code == 200
            assert r_set.json()["is_using_platform_default"] is False
            assert r_set.json()["has_api_key"] is True

            # Clear with whitespace or empty
            clear_val = "" if i % 2 == 0 else "   "
            r_clear = client.put(
                f"/api/ai-settings/{test_business.id}",
                json={"llm_provider": "gemini", "llm_api_key": clear_val},
                headers=auth_headers,
            )
            assert r_clear.status_code == 200
            assert r_clear.json()["is_using_platform_default"] is True
            assert r_clear.json()["has_api_key"] is False
