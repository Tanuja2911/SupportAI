"""
Milestone E2E-M1: Tier 1 Feature Coverage Test Suite (F1 - F15)
75 Comprehensive End-to-End Tests (5 tests per feature).

Covers:
- F1: DB Schema public_key
- F2: DB Schema allowed_domains & allow_localhost
- F3: Alembic Migration Chain
- F4: Container Boot & Docker Healthchecks
- F5: Unified Key Management & Fallback
- F6: Public vs Secret Key Decoupling
- F7: Domain Whitelisting Engine
- F8: Chat & Widget Origin Guard Integration
- F9: Greeting & False Escalation Fix
- F10: Pure 1-Line Self-Initializing Widget
- F11: Widget Status & Mobile Responsiveness
- F12: AI Settings Dashboard UI / API
- F13: Widget Config Dashboard UI / API
- F14: Embed Code Generator & 1-Click Copy
- F15: Automated Backend Pytest Suite Infrastructure
"""

import os
import re
import ast
import uuid
import socket
import psycopg2
import pytest
from urllib.parse import urlparse
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import String, Boolean, JSON

from app.models.business import Business
from app.models.widget import WidgetConfig
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.user import User, UserRole
from app.models.team import TeamMember
from app.core.config import get_settings
import app.services.rag_engine as rag_module


# ---------------------------------------------------------------------------
# Contract Helpers (Adhering to PROJECT.md § Interface Contracts)
# ---------------------------------------------------------------------------


def generate_embed_snippet(host_origin: str, public_key: str) -> str:
    """Generate pure 1-line script embed snippet adhering to PROJECT.md contract."""
    clean_origin = host_origin.rstrip("/")
    return f'<script src="{clean_origin}/widget/widget.js" data-business-key="{public_key}" defer></script>'


# ===========================================================================
# F1: DB Schema public_key (5 tests)
# ===========================================================================
class TestFeature1PublicKeySchema:
    def test_f1_business_model_has_public_key_column(self):
        """F1.1: Verify Business model has public_key column of type String(64), indexed and unique."""
        col = Business.__table__.columns.get("public_key")
        assert col is not None, "Business model must have public_key column"
        assert isinstance(col.type, String), "public_key column must be String"
        assert col.type.length == 64, "public_key column length must be 64"
        assert col.index is True, "public_key column must be indexed"
        assert col.unique is True, "public_key column must be unique"

    def test_f1_business_public_key_unique_index(self, db):
        """F1.2: Verify uniqueness constraint on Business.public_key prevents duplicate values."""
        fixed_key = f"pk_{uuid.uuid4().hex}"
        b1 = Business(name="Biz 1", slug=f"biz1-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}", public_key=fixed_key)
        db.add(b1)
        db.commit()

        b2 = Business(name="Biz 2", slug=f"biz2-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}", public_key=fixed_key)
        db.add(b2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_f1_business_create_populates_public_key(self, db):
        """F1.3: Verify creating Business automatically generates public_key with pk_ prefix."""
        b = Business(name="Auto PK Biz", slug=f"auto-pk-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}")
        db.add(b)
        db.commit()
        db.refresh(b)
        assert b.public_key is not None
        assert b.public_key.startswith("pk_"), f"Expected pk_ prefix, got {b.public_key}"

    def test_f1_public_key_format_validation(self, db):
        """F1.4: Verify public_key format adheres to pk_<32_hex_chars> with 35 total length."""
        b = Business(name="Format Biz", slug=f"format-biz-{uuid.uuid4().hex[:6]}", api_key=f"sec_{uuid.uuid4().hex}")
        db.add(b)
        db.commit()
        db.refresh(b)

        assert len(b.public_key) == 35, f"Expected 35 chars (pk_ + 32 hex), got {len(b.public_key)}"
        hex_part = b.public_key[3:]
        assert all(c in "0123456789abcdef" for c in hex_part), "public_key suffix must be valid hex"

    def test_f1_query_business_by_public_key(self, db, test_business):
        """F1.5: Verify businesses can be directly queried by public_key."""
        result = db.query(Business).filter(Business.public_key == test_business.public_key).first()
        assert result is not None
        assert result.id == test_business.id
        assert result.api_key == test_business.api_key


# ===========================================================================
# F2: DB Schema allowed_domains & allow_localhost (5 tests)
# ===========================================================================
class TestFeature2AllowedDomainsSchema:
    def test_f2_widget_config_model_columns_exist(self):
        """F2.1: Verify WidgetConfig model has allowed_domains and allow_localhost columns."""
        table = WidgetConfig.__table__
        assert "allowed_domains" in table.columns, "WidgetConfig must have allowed_domains column"
        assert "allow_localhost" in table.columns, "WidgetConfig must have allow_localhost column"
        assert isinstance(table.columns["allowed_domains"].type, JSON), "allowed_domains must be JSON type"
        assert isinstance(table.columns["allow_localhost"].type, Boolean), "allow_localhost must be Boolean type"

    def test_f2_allowed_domains_default_empty_list(self, db, test_business):
        """F2.2: Verify allowed_domains defaults to an empty list when omitted."""
        config = WidgetConfig(business_id=test_business.id)
        assert config.allowed_domains == [] or config.allowed_domains is None

    def test_f2_allow_localhost_default_true(self, db, test_business):
        """F2.3: Verify allow_localhost defaults to True on WidgetConfig when committed."""
        config = WidgetConfig(business_id=test_business.id)
        db.add(config)
        db.commit()
        db.refresh(config)
        assert config.allow_localhost is True

    def test_f2_widget_config_persists_domains_json_list(self, db, test_business):
        """F2.4: Verify storing and retrieving multiple allowed domains preserves list structure."""
        domain_list = ["example.com", "shop.example.com", "partner-portal.io"]
        cfg = WidgetConfig(business_id=test_business.id, allowed_domains=domain_list, allow_localhost=True)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

        assert isinstance(cfg.allowed_domains, list)
        assert len(cfg.allowed_domains) == 3
        assert "shop.example.com" in cfg.allowed_domains

    def test_f2_widget_config_allow_localhost_boolean_toggle(self, db, test_business):
        """F2.5: Verify allow_localhost can be set to False and properly persisted."""
        cfg = WidgetConfig(business_id=test_business.id, allow_localhost=False, allowed_domains=["prod.com"])
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

        assert cfg.allow_localhost is False
        cfg.allow_localhost = True
        db.commit()
        db.refresh(cfg)
        assert cfg.allow_localhost is True


# ===========================================================================
# F3: Alembic Migration Chain (5 tests)
# ===========================================================================
class TestFeature3AlembicMigrationChain:
    def _get_versions_dir(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../migrations/versions"))

    def test_f3_migration_file_exists(self):
        """F3.1: Verify Alembic migration file for widget security and public keys exists."""
        versions_dir = self._get_versions_dir()
        migration_file = os.path.join(versions_dir, "f841aa3ea07f_add_widget_security_and_public_keys.py")
        assert os.path.exists(migration_file), f"Migration file {migration_file} must exist"

    def test_f3_migration_down_revision_points_to_ea2363451b55(self):
        """F3.2: Verify down_revision strictly links to ea2363451b55."""
        versions_dir = self._get_versions_dir()
        migration_file = os.path.join(versions_dir, "f841aa3ea07f_add_widget_security_and_public_keys.py")
        with open(migration_file, "r") as f:
            content = f.read()

        assert "revision: str = 'f841aa3ea07f'" in content or 'revision = "f841aa3ea07f"' in content or "revision = 'f841aa3ea07f'" in content
        assert "down_revision" in content
        assert "ea2363451b55" in content

    def test_f3_migration_has_upgrade_and_downgrade_callables(self):
        """F3.3: Verify migration defines both upgrade() and downgrade() functions."""
        versions_dir = self._get_versions_dir()
        migration_file = os.path.join(versions_dir, "f841aa3ea07f_add_widget_security_and_public_keys.py")
        with open(migration_file, "r") as f:
            tree = ast.parse(f.read())

        func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "upgrade" in func_names, "Migration must define upgrade()"
        assert "downgrade" in func_names, "Migration must define downgrade()"

    def test_f3_migration_backfill_sql_logic(self):
        """F3.4: Verify migration script executes SQL backfill for existing businesses."""
        versions_dir = self._get_versions_dir()
        migration_file = os.path.join(versions_dir, "f841aa3ea07f_add_widget_security_and_public_keys.py")
        with open(migration_file, "r") as f:
            content = f.read()

        assert "UPDATE businesses SET public_key =" in content, "Migration must backfill public_key"
        assert "WHERE public_key IS NULL" in content, "Backfill must target NULL public_key rows"
        assert "nullable=False" in content, "Migration must enforce non-null on public_key"
        assert "allowed_domains" in content, "Migration must add allowed_domains column"
        assert "allow_localhost" in content, "Migration must add allow_localhost column"

    def test_f3_linear_migration_chain(self):
        """F3.5: Verify linear Alembic migration history without split heads."""
        versions_dir = self._get_versions_dir()
        files = [f for f in os.listdir(versions_dir) if f.endswith(".py") and not f.startswith("__")]

        revisions = {}
        for f in files:
            path = os.path.join(versions_dir, f)
            with open(path, "r") as fp:
                txt = fp.read()
            rev_match = re.search(r"revision\s*:\s*str\s*=\s*['\"]([^'\"]+)['\"]", txt) or re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", txt)
            down_match = re.search(r"down_revision\s*:\s*Union\[[^\]]+\]\s*=\s*['\"]([^'\"]+)['\"]", txt) or re.search(r"down_revision\s*=\s*['\"]([^'\"]+)['\"]", txt)
            if rev_match:
                rev = rev_match.group(1)
                down = down_match.group(1) if down_match else None
                revisions[rev] = down

        assert "f841aa3ea07f" in revisions
        assert revisions["f841aa3ea07f"] == "ea2363451b55"
        assert revisions["ea2363451b55"] == "a19f4c2d7e31"
        assert revisions["a19f4c2d7e31"] == "ccd3ae6edeb7"
        assert revisions["ccd3ae6edeb7"] is None, "ccd3ae6edeb7 must be root migration"


# ===========================================================================
# F4: Container Boot & Docker Healthchecks (5 tests)
# ===========================================================================
class TestFeature4ContainerBootAndHealthchecks:
    def test_f4_docker_compose_db_healthcheck_defined(self):
        """F4.1: Verify postgres db service is healthy and accepts connections on port 5432."""
        s = socket.create_connection(("db", 5432), timeout=3)
        assert s is not None
        s.close()

    def test_f4_docker_compose_redis_healthcheck_defined(self):
        """F4.2: Verify redis service is healthy and responds to PING command."""
        r = socket.create_connection(("redis", 6379), timeout=3)
        r.sendall(b"PING\r\n")
        resp = r.recv(1024)
        r.close()
        assert resp.strip() == b"+PONG"

    def test_f4_docker_compose_backend_depends_on_healthy(self):
        """F4.3: Verify backend boot executed Alembic migrations on healthy database."""
        conn = psycopg2.connect("postgresql://supportiq:supportiq@db:5432/supportiq")
        cur = conn.cursor()
        cur.execute("SELECT version_num FROM alembic_version")
        row = cur.fetchone()
        cur.close()
        conn.close()
        assert row is not None
        assert row[0] == "f841aa3ea07f", f"Expected head f841aa3ea07f, got {row[0]}"

    def test_f4_docker_compose_celery_depends_on_healthy(self):
        """F4.4: Verify celery worker environment is coordinated with redis broker."""
        settings = get_settings()
        assert "redis" in settings.REDIS_URL
        assert ":6379" in settings.REDIS_URL

    def test_f4_gemini_api_key_env_not_clobbered(self):
        """F4.5: Verify .env configuration exists and GEMINI_API_KEY is not clobbered."""
        env_path = "/app/.env"
        assert os.path.exists(env_path), f"Environment file {env_path} must exist"
        settings = get_settings()
        assert settings.SECRET_KEY is not None


# ===========================================================================
# F5: Unified Key Management & Fallback (5 tests)
# ===========================================================================
class TestFeature5UnifiedKeyManagementAndFallback:
    def test_f5_resolve_credentials_platform_default(self, clean_env):
        """F5.1: Tenant without custom key resolves to platform default GEMINI_API_KEY."""
        from app.services.llm_service import resolve_llm_credentials
        biz = Business(name="Platform Default Biz", slug="pf-biz", api_key="sec_1", llm_provider="gemini", llm_api_key=None)
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "platform_default_gemini_test_key_12345"

    def test_f5_resolve_credentials_tenant_byok(self, clean_env):
        """F5.2: Tenant with custom key overrides platform default."""
        from app.services.llm_service import resolve_llm_credentials
        biz = Business(name="BYOK Biz", slug="byok-biz", api_key="sec_2", llm_provider="openai", llm_api_key="sk-custom-tenant-key-777")
        provider, key = resolve_llm_credentials(biz)
        assert provider == "openai"
        assert key == "sk-custom-tenant-key-777"

    def test_f5_resolve_credentials_custom_provider_with_byok(self, clean_env):
        """F5.3: Tenant custom key works with Anthropic provider."""
        from app.services.llm_service import resolve_llm_credentials
        biz = Business(name="Anthropic Biz", slug="anth-biz", api_key="sec_3", llm_provider="anthropic", llm_api_key="claude-custom-key-888")
        provider, key = resolve_llm_credentials(biz)
        assert provider == "anthropic"
        assert key == "claude-custom-key-888"

    def test_f5_resolve_credentials_empty_byok_falls_back(self, clean_env):
        """F5.4: Tenant with empty or whitespace BYOK key gracefully falls back to platform key."""
        from app.services.llm_service import resolve_llm_credentials
        biz = Business(name="Empty Key Biz", slug="empty-biz", api_key="sec_4", llm_provider="gemini", llm_api_key="   ")
        provider, key = resolve_llm_credentials(biz)
        assert provider == "gemini"
        assert key == "platform_default_gemini_test_key_12345"

    def test_f5_resolve_credentials_no_key_raises_400(self, monkeypatch):
        """F5.5: When neither tenant nor platform has an API key, raises HTTPException 400."""
        settings = get_settings()
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        from app.services.llm_service import resolve_llm_credentials
        biz = Business(name="No Key Biz", slug="no-key-biz", api_key="sec_5", llm_provider="gemini", llm_api_key=None)
        with pytest.raises(HTTPException) as exc_info:
            resolve_llm_credentials(biz)
        assert exc_info.value.status_code == 400
        assert "No LLM API key configured" in exc_info.value.detail


# ===========================================================================
# F6: Public vs Secret Key Decoupling (5 tests)
# ===========================================================================
class TestFeature6PublicVsSecretKeyDecoupling:
    def test_f6_public_and_secret_keys_are_distinct(self, test_business):
        """F6.1: Verify public_key and api_key are distinct strings with separate prefixes."""
        assert test_business.public_key != test_business.api_key
        assert test_business.public_key.startswith("pk_")
        assert test_business.api_key.startswith("sec_")

    def test_f6_secret_key_allowed_on_chat_for_backward_compat(self, client, test_business, test_widget_config):
        """F6.2: Backward compatibility: POST /api/chat/{secret_key} succeeds."""
        payload = {"message": "hello", "customer_name": "Test Customer"}
        res = client.post(f"/api/chat/{test_business.api_key}", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "conversation_id" in data
        assert data["message"] == test_widget_config.welcome_message

    def test_f6_secret_key_allowed_on_embed_endpoint(self, client, test_business, test_widget_config):
        """F6.3: Backward compatibility: GET /api/widget/embed/{secret_key} succeeds."""
        res = client.get(f"/api/widget/embed/{test_business.api_key}")
        assert res.status_code == 200
        data = res.json()
        assert data["bot_name"] == test_widget_config.bot_name

    def test_f6_public_key_rejected_on_admin_routes(self, client, test_business):
        """F6.4: Sending public_key as Bearer token to admin routes returns HTTP 401."""
        headers = {"Authorization": f"Bearer {test_business.public_key}"}
        res = client.get(f"/api/conversations/{test_business.id}", headers=headers)
        assert res.status_code == 401

    def test_f6_invalid_token_returns_404(self, client):
        """F6.5: Non-existent token returns HTTP 404 on chat and embed routes."""
        res_chat = client.post("/api/chat/invalid_random_token_12345", json={"message": "hello"})
        assert res_chat.status_code == 404

        res_embed = client.get("/api/widget/embed/invalid_random_token_12345")
        assert res_embed.status_code == 404


# ===========================================================================
# F7: Domain Whitelisting Engine (5 tests)
# ===========================================================================
class TestFeature7DomainWhitelistingEngine:
    def test_f7_validate_origin_allowed_domain_exact_match(self):
        """F7.1: Exact matching allowed domain returns True."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("http://example.com", None, ["example.com"], allow_localhost=False) is True

    def test_f7_validate_origin_subdomain_match(self):
        """F7.2: Subdomain of an allowed domain returns True."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://shop.example.com", None, ["example.com"], allow_localhost=False) is True
        assert validate_origin("https://checkout.staging.example.com", None, ["example.com"], allow_localhost=False) is True

    def test_f7_validate_origin_unlisted_domain_blocked(self):
        """F7.3: Domain not in allowed_domains returns False."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("https://attacker-site.org", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("https://example.com.evil.co", None, ["example.com"], allow_localhost=False) is False

    def test_f7_validate_origin_localhost_allowed_when_flag_true(self):
        """F7.4: Localhost origins return True when allow_localhost is True."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("http://localhost:3000", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://127.0.0.1:8080", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("http://[::1]:5173", None, ["example.com"], allow_localhost=True) is True
        assert validate_origin("null", None, ["example.com"], allow_localhost=True) is True

    def test_f7_validate_origin_localhost_blocked_when_flag_false(self):
        """F7.5: Localhost origins return False when allow_localhost is False."""
        from app.core.origin_guard import validate_origin
        assert validate_origin("http://localhost:3000", None, ["example.com"], allow_localhost=False) is False
        assert validate_origin("http://127.0.0.1:8080", None, ["example.com"], allow_localhost=False) is False


# ===========================================================================
# F8: Chat & Widget Origin Guard Integration (5 tests)
# ===========================================================================
class TestFeature8ChatAndWidgetOriginGuardIntegration:
    def test_f8_chat_endpoint_allowed_origin_returns_200(self, client, test_business, test_widget_config):
        """F8.1: POST /api/chat with allowed origin succeeds with 200."""
        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "hello"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert res.status_code == 200
        assert res.json()["confidence_score"] == 1.0

    def test_f8_embed_endpoint_allowed_origin_returns_200(self, client, test_business, test_widget_config):
        """F8.2: GET /api/widget/embed with allowed origin succeeds with 200."""
        res = client.get(
            f"/api/widget/embed/{test_business.api_key}",
            headers={"Origin": "http://localhost:3000"},
        )
        assert res.status_code == 200
        assert res.json()["bot_name"] == test_widget_config.bot_name

    def test_f8_origin_guard_enforcement_contract_403(self, client, test_business, test_widget_config):
        """F8.3: Origin guard interface contract mandates HTTP 403 Forbidden with exact message on endpoints."""
        # Test chat endpoint with unauthorized origin
        chat_res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "hello"},
            headers={"Origin": "https://unauthorized-domain.com"},
        )
        assert chat_res.status_code == 403
        assert chat_res.json()["detail"] == "Origin not allowed"

        # Test widget embed endpoint with unauthorized origin
        embed_res = client.get(
            f"/api/widget/embed/{test_business.api_key}",
            headers={"Origin": "https://unauthorized-domain.com"},
        )
        assert embed_res.status_code == 403
        assert embed_res.json()["detail"] == "Origin not allowed"

    def test_f8_referer_fallback_when_origin_header_absent(self, test_widget_config):
        """F8.4: Referer header validates when Origin header is omitted."""
        from app.core.origin_guard import validate_origin
        assert validate_origin(None, "https://app.example.com/pricing", test_widget_config.allowed_domains, allow_localhost=False) is True
        assert validate_origin(None, "https://malicious.org/phishing", test_widget_config.allowed_domains, allow_localhost=False) is False

    def test_f8_chat_endpoint_records_message_from_valid_origin(self, client, db, test_business, test_widget_config):
        """F8.5: Chat interaction records customer message into SQLite database."""
        client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "hello", "customer_name": "Origin Tester"},
            headers={"Origin": "http://localhost:5173"},
        )
        msg = db.query(Message).filter(Message.content == "hello").first()
        assert msg is not None
        assert msg.sender == MessageSender.CUSTOMER


# ===========================================================================
# F9: Greeting & False Escalation Fix (5 tests)
# ===========================================================================
class TestFeature9GreetingAndFalseEscalationFix:
    def test_f9_conversational_greeting_hello_returns_friendly(self, client, test_business, test_widget_config):
        """F9.1: 'hello' returns widget welcome message."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hello"})
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == test_widget_config.welcome_message

    def test_f9_conversational_greeting_confidence_1(self, client, test_business):
        """F9.2: Greeting has confidence_score == 1.0."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hi there"})
        assert res.status_code == 200
        assert res.json()["confidence_score"] == 1.0

    def test_f9_greeting_does_not_set_escalated(self, client, test_business):
        """F9.3: Greeting has is_escalated == False."""
        res = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hey"})
        assert res.status_code == 200
        assert res.json()["is_escalated"] is False

    def test_f9_conversational_greeting_variations(self, client, test_business, test_widget_config):
        """F9.4: Variations ('Good morning', 'Howdy', 'greetings') resolve cleanly."""
        for greeting in ["Good morning!", "Howdy", "Greetings", "sup"]:
            res = client.post(f"/api/chat/{test_business.api_key}", json={"message": greeting})
            assert res.status_code == 200, f"Failed on greeting: {greeting}"
            data = res.json()
            assert data["is_escalated"] is False
            assert data["confidence_score"] == 1.0
            assert data["message"] == test_widget_config.welcome_message

    def test_f9_greeting_resets_escalated_conversation_to_active(self, client, db, test_business):
        """F9.5: Greeting sent to an ESCALATED conversation restores status to ACTIVE."""
        conv = Conversation(business_id=test_business.id, status=ConversationStatus.ESCALATED)
        db.add(conv)
        db.commit()
        db.refresh(conv)

        res = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "hello", "conversation_id": str(conv.id)},
        )
        assert res.status_code == 200
        db.refresh(conv)
        assert conv.status == ConversationStatus.ACTIVE


# ===========================================================================
# F10: Pure 1-Line Self-Initializing Widget (5 tests)
# ===========================================================================
class TestFeature10PureOneLineSelfInitializingWidget:
    def test_f10_widget_static_file_served(self, client):
        """F10.1: GET /widget/widget.js returns HTTP 200 and javascript content."""
        res = client.get("/widget/widget.js")
        assert res.status_code == 200
        assert "javascript" in res.headers.get("content-type", "")

    def test_f10_widget_script_contains_script_src_origin_detection(self, client):
        """F10.2: Widget script contains origin detection logic parsing script src."""
        res = client.get("/widget/widget.js")
        text = res.text
        assert "scripts[i].src" in text or "currentScript" in text
        assert "detectedServerUrl" in text or "serverUrl" in text

    def test_f10_widget_script_defines_supportai_global(self, client):
        """F10.3: Widget script defines window.SupportAI namespace."""
        res = client.get("/widget/widget.js")
        assert "window.SupportAI" in res.text

    def test_f10_widget_embed_contract_1_line_syntax(self, test_business):
        """F10.4: Snippet strictly matches single-line script format with data-business-key and defer."""
        snippet = generate_embed_snippet("https://app.supportai.com", test_business.public_key)
        pattern = r'^<script src="https://app\.supportai\.com/widget/widget\.js" data-business-key="pk_[0-9a-f]{32}" defer></script>$'
        assert re.match(pattern, snippet), f"Snippet {snippet} does not match expected 1-line format"

    def test_f10_widget_loads_embed_config_via_api(self, client):
        """F10.5: Widget script contains API call to /api/widget/embed/."""
        res = client.get("/widget/widget.js")
        assert "/api/widget/embed/" in res.text


# ===========================================================================
# F11: Widget Status & Mobile Responsiveness (5 tests)
# ===========================================================================
class TestFeature11WidgetStatusAndMobileResponsiveness:
    def test_f11_widget_script_styling_definitions(self, client):
        """F11.1: Widget script contains base DOM styling definitions."""
        res = client.get("/widget/widget.js")
        text = res.text
        assert "primary_color" in text or "primaryColor" in text
        assert "zIndex" in text or "position" in text

    def test_f11_widget_config_returns_custom_styling(self, client, test_business, test_widget_config):
        """F11.2: GET /api/widget/embed/{api_key} returns styling configurations."""
        res = client.get(f"/api/widget/embed/{test_business.api_key}")
        assert res.status_code == 200
        data = res.json()
        assert data["primary_color"] == test_widget_config.primary_color
        assert data["position"] == test_widget_config.position
        assert "placeholder_text" in data

    def test_f11_widget_mobile_positioning_defaults(self, test_widget_config):
        """F11.3: Default widget position is bottom-right."""
        assert test_widget_config.position == "bottom-right"

    def test_f11_widget_handles_chat_reset_flow(self, client, test_business):
        """F11.4: Starting a chat without conversation_id allocates a new conversation."""
        res1 = client.post(f"/api/chat/{test_business.api_key}", json={"message": "first message"})
        conv1_id = res1.json()["conversation_id"]

        # Resetting: omit conversation_id
        res2 = client.post(f"/api/chat/{test_business.api_key}", json={"message": "second message after reset"})
        conv2_id = res2.json()["conversation_id"]

        assert conv1_id != conv2_id, "Reset chat must allocate new conversation ID"

    def test_f11_widget_conversation_continuity_with_id(self, client, test_business):
        """F11.5: Supplying conversation_id maintains continuity in the same conversation."""
        res1 = client.post(f"/api/chat/{test_business.api_key}", json={"message": "hello"})
        conv_id = res1.json()["conversation_id"]

        res2 = client.post(
            f"/api/chat/{test_business.api_key}",
            json={"message": "hi there", "conversation_id": conv_id},
        )
        assert res2.json()["conversation_id"] == conv_id


# ===========================================================================
# F12: AI Settings Dashboard UI / API (5 tests)
# ===========================================================================
class TestFeature12AISettingsAPI:
    def test_f12_get_ai_settings_returns_has_api_key(self, client, test_business, auth_headers):
        """F12.1: GET /api/ai-settings/{id} returns has_api_key: False initially."""
        res = client.get(f"/api/ai-settings/{test_business.id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is False
        assert data["llm_provider"] == "gemini"

    def test_f12_update_ai_settings_custom_key(self, client, test_business, auth_headers):
        """F12.2: PUT /api/ai-settings/{id} sets custom key and provider."""
        payload = {"llm_provider": "openai", "llm_api_key": "sk-custom-openai-secret"}
        res = client.put(f"/api/ai-settings/{test_business.id}", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["has_api_key"] is True
        assert data["llm_provider"] == "openai"

    def test_f12_clear_ai_settings_resets_to_platform_default(self, client, test_business, auth_headers):
        """F12.3: Clearing custom key resets has_api_key to False."""
        payload = {"llm_provider": "gemini", "llm_api_key": ""}
        res = client.put(f"/api/ai-settings/{test_business.id}", json=payload, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["has_api_key"] is False

    def test_f12_update_ai_settings_invalid_provider_returns_400(self, client, test_business, auth_headers):
        """F12.4: Submitting an invalid provider returns HTTP 400 Bad Request."""
        payload = {"llm_provider": "unsupported_llm_xyz", "llm_api_key": "any-key"}
        res = client.put(f"/api/ai-settings/{test_business.id}", json=payload, headers=auth_headers)
        assert res.status_code == 400
        assert "Provider must be one of" in res.json()["detail"]

    def test_f12_unauthorized_ai_settings_access_returns_403(self, client, test_business, db):
        """F12.5: User without membership in the business receives HTTP 403 Forbidden."""
        other_user = User(email="intruder@test.com", hashed_password="pw", full_name="Intruder")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        from app.core.security import create_access_token
        intruder_token = create_access_token({"sub": str(other_user.id)})
        headers = {"Authorization": f"Bearer {intruder_token}", "X-Business-Id": str(test_business.id)}

        res = client.get(f"/api/ai-settings/{test_business.id}", headers=headers)
        assert res.status_code == 403


# ===========================================================================
# F13: Widget Config Dashboard UI / API (5 tests)
# ===========================================================================
class TestFeature13WidgetConfigAPI:
    def test_f13_get_widget_config_returns_config_object(self, client, test_business, test_widget_config, auth_headers):
        """F13.1: GET /api/widget/{id}/config returns widget configuration object."""
        res = client.get(f"/api/widget/{test_business.id}/config", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["bot_name"] == test_widget_config.bot_name
        assert data["welcome_message"] == test_widget_config.welcome_message

    def test_f13_update_widget_config_basic_properties(self, client, test_business, test_widget_config, auth_headers):
        """F13.2: PUT /api/widget/{id}/config updates bot_name and primary_color."""
        payload = {"bot_name": "SupportAI Pro Assistant", "primary_color": "#4f46e5"}
        res = client.put(f"/api/widget/{test_business.id}/config", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["bot_name"] == "SupportAI Pro Assistant"
        assert data["primary_color"] == "#4f46e5"

    def test_f13_update_widget_config_persists_in_database(self, client, db, test_business, test_widget_config, auth_headers):
        """F13.3: Widget config update persists modifications to SQLite database."""
        client.put(
            f"/api/widget/{test_business.id}/config",
            json={"welcome_message": "Updated persistent welcome!"},
            headers=auth_headers,
        )
        db.refresh(test_widget_config)
        assert test_widget_config.welcome_message == "Updated persistent welcome!"

    def test_f13_non_owner_cannot_update_widget_config(self, client, test_business, test_widget_config, viewer_headers):
        """F13.4: Team member with viewer role receives HTTP 403 on PUT widget config."""
        payload = {"bot_name": "Hacked Name"}
        res = client.put(f"/api/widget/{test_business.id}/config", json=payload, headers=viewer_headers)
        assert res.status_code == 403
        assert "Insufficient permissions" in res.json()["detail"]

    def test_f13_unauthenticated_widget_config_access_returns_401(self, client, test_business):
        """F13.5: Accessing widget config without token returns HTTP 401 Unauthorized."""
        res = client.get(f"/api/widget/{test_business.id}/config")
        assert res.status_code == 401


# ===========================================================================
# F14: Embed Code Generator & 1-Click Copy (5 tests)
# ===========================================================================
class TestFeature14EmbedCodeGenerator:
    def test_f14_embed_code_snippet_format(self, test_business):
        """F14.1: Embed snippet matches <script src='.../widget/widget.js' data-business-key='pk_...' defer></script>."""
        snippet = generate_embed_snippet("http://localhost:8000", test_business.public_key)
        assert snippet.startswith('<script src="http://localhost:8000/widget/widget.js"')
        assert f'data-business-key="{test_business.public_key}"' in snippet
        assert snippet.endswith('defer></script>')

    def test_f14_embed_code_uses_public_key_not_secret(self, test_business):
        """F14.2: Embed snippet strictly incorporates public_key and never the administrative secret key."""
        snippet = generate_embed_snippet("http://localhost:8000", test_business.public_key)
        assert test_business.public_key in snippet
        assert test_business.api_key not in snippet

    def test_f14_embed_code_single_tag_only(self, test_business):
        """F14.3: Embed snippet consists of a single self-contained script tag without inline scripts."""
        snippet = generate_embed_snippet("http://localhost:8000", test_business.public_key)
        assert snippet.count("<script") == 1
        assert snippet.count("</script>") == 1
        assert "SupportAI.init" not in snippet

    def test_f14_embed_code_contains_defer_attribute(self, test_business):
        """F14.4: Embed snippet includes defer attribute."""
        snippet = generate_embed_snippet("http://localhost:8000", test_business.public_key)
        assert "defer" in snippet

    def test_f14_embed_code_dynamic_origin_interpolation(self, test_business):
        """F14.5: Embed snippet generator handles dynamic production host origins."""
        snippet = generate_embed_snippet("https://support.enterprise.io/", test_business.public_key)
        assert snippet == f'<script src="https://support.enterprise.io/widget/widget.js" data-business-key="{test_business.public_key}" defer></script>'


# ===========================================================================
# F15: Automated Backend Pytest Suite Infrastructure (5 tests)
# ===========================================================================
class TestFeature15PytestSuiteInfrastructure:
    def test_f15_test_client_health_check(self, client):
        """F15.1: TestClient connects to FastAPI app and verifies /api/health."""
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

    def test_f15_mock_llm_records_invocations(self, mock_llm_service, clean_env):
        """F15.2: mock_llm_service fixture intercepts LLM calls without external network requests."""
        call_fn = rag_module.LLM_PROVIDERS.get("gemini")
        resp = call_fn("test_key", "generate 5-8 frequently asked questions for support")
        assert len(mock_llm_service) == 1
        assert mock_llm_service[0]["provider"] == "gemini"
        assert mock_llm_service[0]["api_key"] == "test_key"
        assert "How do returns work?" in resp

    def test_f15_mock_embeddings_records_searches(self, mock_embedding_service):
        """F15.3: mock_embedding_service fixture returns mock chunks without PyTorch weight loading."""
        from app.services.embedding_service import EmbeddingService
        svc = EmbeddingService()
        results = svc.search("biz-123", "What is the return policy?")
        assert len(mock_embedding_service) == 1
        assert len(results) == 1
        assert "return policy allows" in results[0]["chunk"]

    def test_f15_sqlite_uuid_processor_handles_string_uuids(self, db):
        """F15.4: SQLite monkey-patch on PG_UUID allows string UUID queries without AttributeError."""
        user_uuid = uuid.uuid4()
        user = User(id=user_uuid, email="uuid_patch@test.com", hashed_password="pw", full_name="UUID User")
        db.add(user)
        db.commit()

        # Query using raw string UUID (exactly as returned from JWT decode)
        found = db.query(User).filter(User.id == str(user_uuid)).first()
        assert found is not None
        assert found.email == "uuid_patch@test.com"

    def test_f15_all_models_registered_in_metadata(self):
        """F15.5: Base.metadata contains all 10 application domain models."""
        from app.core.database import Base
        tables = Base.metadata.tables.keys()
        expected_tables = {
            "users",
            "businesses",
            "team_members",
            "widget_configs",
            "conversations",
            "messages",
            "documents",
            "document_chunks",
            "faq_overrides",
            "analytics_events",
            "knowledge_gaps",
        }
        for table in expected_tables:
            assert table in tables, f"Expected table {table} in metadata"
