import json
import logging
import httpx
from app.core.config import get_settings
from app.services.embedding_service import EmbeddingService

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful customer support assistant for a business.
Answer the customer's question based ONLY on the provided context documents.
If the context doesn't contain enough information to answer, say so honestly.
Be concise, friendly, and professional.
Do NOT make up information that isn't in the context."""


def _call_gemini(api_key: str, prompt: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.6-flash")
    response = model.generate_content(
        [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
    )
    return response.text


def _call_openai(api_key: str, prompt: str) -> str:
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _call_anthropic(api_key: str, prompt: str) -> str:
    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]


LLM_PROVIDERS = {
    "gemini": _call_gemini,
    "openai": _call_openai,
    "anthropic": _call_anthropic,
}


class RAGEngine:
    def __init__(self, business_id: str, llm_provider: str = None, llm_api_key: str = None):
        self.business_id = business_id
        self.llm_provider = llm_provider or "gemini"
        self.llm_api_key = llm_api_key
        self.embedding_service = EmbeddingService()

    def query(self, question: str, db=None) -> dict:
        search_results = self.embedding_service.search(self.business_id, question, top_k=5)

        if not search_results:
            return {
                "answer": "I don't have enough information to answer that question yet. The knowledge base may still be loading.",
                "confidence": 0.0,
                "sources": [],
            }

        context = "\n\n---\n\n".join([r["chunk"] for r in search_results])
        best_score = max(r["score"] for r in search_results)

        prompt = f"""Context documents:
{context}

Customer question: {question}

Based on the context above, provide a helpful answer."""

        api_key = self.llm_api_key
        if not api_key:
            if self.llm_provider == "gemini":
                api_key = settings.GEMINI_API_KEY
            if not api_key:
                return {
                    "answer": "No API key configured. Please add your LLM API key in AI Settings.",
                    "confidence": 0.0,
                    "sources": [],
                }

        try:
            call_fn = LLM_PROVIDERS.get(self.llm_provider, _call_gemini)
            answer = call_fn(api_key, prompt)
        except Exception as e:
            logger.error(f"LLM API error ({self.llm_provider}): {e}")
            answer = "I'm having trouble generating a response right now. Please try again."
            best_score = 0.0

        confidence = min(max(best_score * 5.0, 0.0), 1.0)

        sources = []
        seen_docs = set()
        for r in search_results:
            if r["doc_id"] not in seen_docs:
                sources.append({
                    "doc_id": r["doc_id"],
                    "relevance": round(r["score"], 3),
                    "preview": r["chunk"][:150] + "...",
                })
                seen_docs.add(r["doc_id"])

        return {
            "answer": answer,
            "confidence": round(confidence, 3),
            "sources": sources,
        }
