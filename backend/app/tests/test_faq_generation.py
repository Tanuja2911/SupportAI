import json

from app.core.security import create_access_token
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.rag_engine import LLM_PROVIDERS


def _add_ready_content(db, business, user):
    document = Document(
        business_id=business.id,
        title="FAQ source",
        file_type="txt",
        file_path="/mock/faq-source.txt",
        status=DocumentStatus.READY,
        uploaded_by=user.id,
    )
    db.add(document)
    db.flush()
    db.add(DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="Our service includes a 30-day return period and free standard shipping.",
    ))
    db.commit()


def test_parse_faq_suggestions_accepts_fenced_json_with_provider_preamble():
    from app.api.routes.faq import _parse_faq_suggestions

    result = _parse_faq_suggestions(
        'Here are some ideas:\n```json\n'
        '[{"question":" How do returns work? ","answer":" Return within 30 days. "},'
        '{"question":"Shipping?","answer":"Free standard shipping."}]\n```\n'
        'Hope these help.'
    )

    assert result == [
        {"question": "How do returns work?", "answer": "Return within 30 days."},
        {"question": "Shipping?", "answer": "Free standard shipping."},
    ]


def test_parse_faq_suggestions_rejects_empty_or_invalid_pairs():
    import pytest
    from app.api.routes.faq import _parse_faq_suggestions

    with pytest.raises(ValueError):
        _parse_faq_suggestions(json.dumps([{"question": "", "answer": "   "}]))


def test_auto_generate_returns_parsed_suggestions(
    client, db, test_business, test_user, test_team_member, monkeypatch
):
    _add_ready_content(db, test_business, test_user)
    test_business.llm_provider = "openai"
    test_business.llm_api_key = "faq-test-key"
    db.commit()
    monkeypatch.setitem(
        LLM_PROVIDERS,
        "openai",
        lambda api_key, prompt: '```json\n[{"question":"When can I return an item?",'
        '"answer":"Within 30 days."}]\n```',
    )
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(test_user.id)})}"}

    response = client.post(f"/api/faq/{test_business.id}/auto-generate", headers=headers)

    assert response.status_code == 200
    assert response.json()["suggestions"] == [
        {"question": "When can I return an item?", "answer": "Within 30 days."}
    ]


def test_auto_generate_reports_safe_provider_diagnostics_without_api_key(
    client, db, test_business, test_user, test_team_member, monkeypatch
):
    _add_ready_content(db, test_business, test_user)
    test_business.llm_provider = "openai"
    test_business.llm_api_key = "private-faq-test-key"
    db.commit()

    def fail_provider(api_key, prompt):
        raise RuntimeError(f"Invalid API key: {api_key}")

    monkeypatch.setitem(LLM_PROVIDERS, "openai", fail_provider)
    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(test_user.id)})}"}

    response = client.post(f"/api/faq/{test_business.id}/auto-generate", headers=headers)

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["error_code"] == "INVALID_API_KEY"
    assert detail["message"]
    assert detail["action_hint"]
    assert "private-faq-test-key" not in json.dumps(detail)
