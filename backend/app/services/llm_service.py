import logging
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.models.business import Business

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS: list[str] = ["gemini", "openai", "anthropic", "nvidia_nim"]
GEMINI_MODEL = "gemini-3.8-flash"
OPENAI_MODEL = "gpt-6-luna"
ANTHROPIC_MODEL = "claude-sonnet-5"
NVIDIA_NIM_MODEL = "openai/gpt-oss-20b"
NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MAX_PROVIDER_ATTEMPTS = 3
MAX_RETRY_DELAY_SECONDS = 2.0
DEFAULT_PROVIDER_TIMEOUT = httpx.Timeout(45.0, connect=5.0, write=10.0, pool=3.0)
NVIDIA_PROVIDER_TIMEOUT = httpx.Timeout(75.0, connect=5.0, write=10.0, pool=3.0)
PROBE_PROVIDER_TIMEOUT = httpx.Timeout(15.0, connect=5.0, write=10.0, pool=3.0)

SYSTEM_PROMPT = """You are a helpful customer support assistant for a business.
Answer the customer's question based ONLY on the provided context documents.
If the context doesn't contain enough information to answer, say so honestly.
Be concise, friendly, and professional.
Do NOT make up information that isn't in the context."""

PROVIDER_LABELS = {
    "gemini": "Google Gemini",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "nvidia_nim": "NVIDIA NIM",
}


def resolve_llm_credentials(business: Business | None = None) -> tuple[str, str]:
    """Resolve LLM provider and API key for a business or platform default."""
    if business is not None and business.llm_api_key and business.llm_api_key.strip():
        provider = (
            business.llm_provider.strip().lower()
            if business.llm_provider and business.llm_provider.strip()
            else "gemini"
        )
        if provider not in SUPPORTED_PROVIDERS:
            provider = "gemini"
        return (provider, business.llm_api_key.strip())

    settings = get_settings()
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        return ("gemini", settings.GEMINI_API_KEY.strip())

    raise HTTPException(status_code=400, detail="No LLM API key configured.")


def classify_llm_error(
    exception: Exception | str,
    provider: str = "gemini",
    api_key: str | None = None,
) -> dict:
    """Classify provider errors and keep credentials out of diagnostics."""
    if isinstance(exception, str) and isinstance(provider, Exception):
        exception, provider = provider, exception

    if isinstance(exception, str):
        safe_error = exception
        exc_type = "Exception"
    else:
        safe_error = str(exception)
        exc_type = type(exception).__name__
    if api_key:
        safe_error = safe_error.replace(api_key, "[REDACTED]")

    err_str = safe_error.lower()
    prov = provider.strip().lower() if provider else "gemini"
    label = PROVIDER_LABELS.get(prov, prov.capitalize())

    invalid_key_patterns = (
        "api_key_invalid",
        "invalid_api_key",
        "api key not valid",
        "invalid api key",
        "api key expired",
        "unauthorized",
        "authentication failed",
        "permissiondenied",
        "permission_denied",
        "401",
    )
    if any(pattern in err_str for pattern in invalid_key_patterns) or (
        "400" in err_str and "key" in err_str
    ):
        status = next((code for code in ("401", "400", "403") if code in err_str), None)
        return {
            "error_code": "INVALID_API_KEY",
            "user_message": "The AI service is unavailable due to an invalid or unconfigured API key. Please check the AI Settings in your dashboard.",
            "diagnostic": f"Provider '{prov}' rejected the API key ({status or '400'} API_KEY_INVALID; authentication failed).",
            "action_hint": {
                "gemini": "Check project access at aistudio.google.com. As of September 2026, Gemini rejects standard API keys; replace one with an AI Studio authorization key in AI Settings.",
                "openai": "Verify your OpenAI API key in AI Settings or create one at platform.openai.com/api-keys.",
                "anthropic": "Verify your Anthropic API key in AI Settings or create one at console.anthropic.com/settings/keys.",
                "nvidia_nim": "Verify your NVIDIA NIM API key in AI Settings or create one at build.nvidia.com.",
            }.get(prov, f"Verify and update your {label} API key in AI Settings."),
        }

    access_denied_patterns = (
        "denied access",
        "access denied",
        "not authorized to access",
        "does not have permission",
        "model access is restricted",
        "403",
    )
    if any(pattern in err_str for pattern in access_denied_patterns):
        return {
            "error_code": "PROVIDER_ACCESS_DENIED",
            "user_message": f"{label} authenticated the request but denied generation access for this project or account.",
            "diagnostic": safe_error[:240] if safe_error else f"Provider '{prov}' denied generation access.",
            "action_hint": (
                "Check project/model access in Google AI Studio. As of September 2026, Gemini rejects standard API keys; replace one with an AI Studio authorization key in AI Settings."
                if prov == "gemini"
                else f"Check that this project or account is enabled for the selected {label} model, or choose another provider."
            ),
        }

    quota_patterns = (
        "resource_exhausted",
        "resourceexhausted",
        "quota exceeded",
        "quota metric",
        "insufficient_quota",
        "spend limit",
        "spend cap",
        "usage limit",
        "payment required",
        "payment_required",
        "http 402",
        " 402",
    )
    if any(pattern in err_str for pattern in quota_patterns):
        return {
            "error_code": "QUOTA_EXCEEDED",
            "user_message": "The AI provider account has reached its usage or billing limit. Please check the provider account before retrying.",
            "diagnostic": safe_error[:240] if safe_error else f"Provider '{prov}' usage or billing limit reached.",
            "action_hint": f"Check your {label} billing plan, usage quota, and account spend limits.",
        }

    if "429" in err_str or "rate_limit" in err_str or "ratelimit" in err_str or "too many requests" in err_str:
        return {
            "error_code": "RATE_LIMITED",
            "user_message": "The AI provider is receiving requests too quickly. Please wait a moment and try again.",
            "diagnostic": safe_error[:240] if safe_error else f"Provider '{prov}' temporarily rate limited the request.",
            "action_hint": "Wait briefly before retrying. If this continues, check the provider's rate limits and usage tier.",
        }

    timeout_patterns = (
        "timeout",
        "timed out",
        "deadlineexceeded",
        "deadline_exceeded",
        "connecttimeout",
        "readtimeout",
    )
    if any(pattern in err_str for pattern in timeout_patterns):
        return {
            "error_code": "TIMEOUT",
            "user_message": "I'm having trouble generating a response right now. The request timed out. Please try again in a few moments.",
            "diagnostic": f"Provider '{prov}' connection timed out.",
            "action_hint": "Check network connectivity or retry in a few moments.",
        }

    if "404" in err_str or "notfound" in err_str or "not found" in err_str:
        model = GEMINI_MODEL if prov == "gemini" else (NVIDIA_NIM_MODEL if prov == "nvidia_nim" else None)
        return {
            "error_code": "MODEL_NOT_FOUND",
            "user_message": f"The configured {label} model is unavailable to this account.",
            "diagnostic": safe_error[:240] if safe_error else f"Provider '{prov}' returned HTTP 404 for the configured model.",
            "action_hint": f"Check model availability and access{f' for {model}' if model else ''}, or select another provider.",
        }

    # Keep the longstanding generic response wording, but retain safe upstream HTTP details.
    diagnostic = f"Provider '{prov}' raised unexpected error: {exc_type}"
    if "http" in err_str or "status code" in err_str:
        diagnostic = safe_error[:240]
    return {
        "error_code": "PROVIDER_ERROR",
        "user_message": "I'm having trouble generating a response right now. Please try again.",
        "diagnostic": diagnostic,
        "action_hint": "Please try again later or contact support if the issue persists.",
    }


def _response_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except (ValueError, AttributeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    error = payload.get("error", payload)
    if isinstance(error, dict):
        detail = error.get("message") or error.get("detail") or error.get("title")
        return str(detail)[:300] if detail else ""
    return str(error)[:300] if error else ""


class ProviderHTTPError(RuntimeError):
    def __init__(self, provider: str, status_code: int, detail: str = ""):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"{PROVIDER_LABELS.get(provider, provider)} API HTTP {status_code}: {detail}")


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    headers = getattr(response, "headers", {}) or {}
    retry_after_value = headers.get("Retry-After") if hasattr(headers, "get") else None
    retry_after = str(retry_after_value) if retry_after_value is not None else None
    try:
        if retry_after is None:
            raise ValueError("Retry-After header is missing")
        requested_delay = float(retry_after)
    except (TypeError, ValueError):
        try:
            if retry_after is None:
                raise ValueError("Retry-After header is missing")
            retry_at = parsedate_to_datetime(retry_after)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            requested_delay = (retry_at - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            requested_delay = 0.25 * (2 ** (attempt - 1))
    if not math.isfinite(requested_delay):
        requested_delay = 0.25 * (2 ** (attempt - 1))
    return min(max(requested_delay, 0.0), MAX_RETRY_DELAY_SECONDS)


def _is_retryable_response(response: httpx.Response) -> bool:
    status_code = getattr(response, "status_code", None)
    try:
        status_code = int(str(status_code))
    except (TypeError, ValueError):
        return False
    if status_code == 429:
        detail = _response_error_detail(response).lower()
        exhausted = ("quota", "insufficient_quota", "spend", "billing", "payment", "resource_exhausted")
        return not any(marker in detail for marker in exhausted)
    return status_code in {500, 502, 503, 504}


def _post_with_retries(url: str, *, timeout: httpx.Timeout, **kwargs) -> httpx.Response:
    """Retry only explicit transient responses and pre-request connection failures.

    Read/write timeouts are deliberately not retried because a provider may already
    have processed and billed the generation before the connection stalled.
    """
    for attempt in range(1, MAX_PROVIDER_ATTEMPTS + 1):
        try:
            response = httpx.post(url, timeout=timeout, **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout):
            if attempt == MAX_PROVIDER_ATTEMPTS:
                raise
            time.sleep(min(0.25 * (2 ** (attempt - 1)), MAX_RETRY_DELAY_SECONDS))
            continue
        if not _is_retryable_response(response) or attempt == MAX_PROVIDER_ATTEMPTS:
            return response
        time.sleep(_retry_delay(response, attempt))
    raise RuntimeError("Provider request exhausted retry attempts.")


def _raise_provider_error(provider: str, response: httpx.Response) -> None:
    if not response.is_success:
        detail = _response_error_detail(response)
        status_code = getattr(response, "status_code", 0)
        try:
            status_code = int(str(status_code))
        except (TypeError, ValueError):
            status_code = 0
        raise ProviderHTTPError(provider, status_code, detail)


def _call_gemini(api_key: str, prompt: str) -> str:
    response = _post_with_retries(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        },
        timeout=DEFAULT_PROVIDER_TIMEOUT,
    )
    _raise_provider_error("gemini", response)
    candidates = response.json().get("candidates") or []
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    answer = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if not answer.strip():
        raise RuntimeError("Gemini response did not include generated text.")
    return answer.strip()


def _call_openai(api_key: str, prompt: str) -> str:
    response = _post_with_retries(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_completion_tokens": 1024,
            "reasoning_effort": "none",
        },
        timeout=DEFAULT_PROVIDER_TIMEOUT,
    )
    _raise_provider_error("openai", response)
    answer = response.json()["choices"][0]["message"]["content"]
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("OpenAI response did not include generated text.")
    return answer.strip()


def _call_anthropic(api_key: str, prompt: str) -> str:
    response = _post_with_retries(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=DEFAULT_PROVIDER_TIMEOUT,
    )
    _raise_provider_error("anthropic", response)
    blocks = response.json().get("content", [])
    answer = "".join(block.get("text", "") for block in blocks if isinstance(block, dict))
    if not answer.strip():
        raise RuntimeError("Anthropic response did not include generated text.")
    return answer.strip()


def _call_nvidia_nim(api_key: str, prompt: str) -> str:
    response = _post_with_retries(
        NVIDIA_NIM_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": NVIDIA_NIM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 1,
            "top_p": 1,
            "max_tokens": 4096,
            "stream": False,
        },
        timeout=NVIDIA_PROVIDER_TIMEOUT,
    )
    _raise_provider_error("nvidia_nim", response)
    answer = response.json()["choices"][0]["message"]["content"]
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("NVIDIA NIM response did not include generated text.")
    return answer.strip()


def _probe_generated_text(provider: str, payload: dict) -> str:
    if provider == "gemini":
        candidates = payload.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if provider == "anthropic":
        blocks = payload.get("content", [])
        return "".join(block.get("text", "") for block in blocks if isinstance(block, dict)).strip()
    choices = payload.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    content = (message.get("content") or message.get("reasoning_content") or "") if isinstance(message, dict) else ""
    return content.strip() if isinstance(content, str) else ""


def _probe_request(provider: str, api_key: str) -> tuple[httpx.Response, str]:
    if provider == "gemini":
        response = _post_with_retries(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={
                "contents": [{"role": "user", "parts": [{"text": "Reply with OK."}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 2},
            },
            timeout=PROBE_PROVIDER_TIMEOUT,
        )
        return response, GEMINI_MODEL

    if provider == "openai":
        response = _post_with_retries(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": OPENAI_MODEL, "messages": [{"role": "user", "content": "Reply with OK."}], "max_completion_tokens": 16, "reasoning_effort": "none"},
            timeout=PROBE_PROVIDER_TIMEOUT,
        )
        return response, OPENAI_MODEL

    if provider == "anthropic":
        response = _post_with_retries(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": ANTHROPIC_MODEL, "max_tokens": 16, "thinking": {"type": "disabled"}, "messages": [{"role": "user", "content": "Reply with OK."}]},
            timeout=PROBE_PROVIDER_TIMEOUT,
        )
        return response, ANTHROPIC_MODEL

    response = _post_with_retries(
        NVIDIA_NIM_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": NVIDIA_NIM_MODEL, "messages": [{"role": "user", "content": "Reply with OK."}], "temperature": 1, "top_p": 1, "max_tokens": 16, "stream": False},
        timeout=PROBE_PROVIDER_TIMEOUT,
    )
    return response, NVIDIA_NIM_MODEL


def test_llm_connection(provider: str = "gemini", api_key: str | None = None) -> dict:
    """Run a minimal completion so a successful check proves generation access."""
    prov = (provider or "gemini").strip().lower()
    if prov not in SUPPORTED_PROVIDERS:
        return {
            "status": "error",
            "provider": prov,
            "model": None,
            "latency_ms": None,
            "message": f"Unsupported LLM provider: '{prov}'.",
            "diagnostic": f"Provider '{prov}' is not supported.",
            "action_hint": f"Choose one of: {', '.join(SUPPORTED_PROVIDERS)}.",
        }

    key = (api_key or "").strip()
    if not key:
        return {
            "status": "error",
            "provider": prov,
            "model": None,
            "latency_ms": None,
            "message": f"No API key provided for {PROVIDER_LABELS[prov]}.",
            "diagnostic": "API key is missing or empty.",
            "action_hint": f"Please enter a valid {PROVIDER_LABELS[prov]} API key.",
        }

    start_time = time.perf_counter()
    try:
        response, model = _probe_request(prov, key)
        latency_ms = max(int((time.perf_counter() - start_time) * 1000), 1)
        if 200 <= response.status_code < 300:
            answer = _probe_generated_text(prov, response.json())
            if answer:
                return {
                    "status": "connected",
                    "provider": prov,
                    "model": model,
                    "latency_ms": latency_ms,
                    "message": f"Successfully generated a test response with {PROVIDER_LABELS[prov]}.",
                    "error_code": None,
                    "diagnostic": None,
                    "action_hint": None,
                }
            detail = "Provider returned HTTP 200 but no generated text."
            err_info = classify_llm_error(RuntimeError(detail), prov, key)
        else:
            detail = _response_error_detail(response)
            err_info = classify_llm_error(RuntimeError(f"HTTP {response.status_code}: {detail}"), prov, key)
        return {
            "status": "error",
            "provider": prov,
            "model": None,
            "latency_ms": latency_ms,
            "message": err_info["user_message"],
            "error_code": err_info["error_code"],
            "diagnostic": err_info["diagnostic"],
            "action_hint": err_info["action_hint"],
        }
    except httpx.TimeoutException:
        latency_ms = max(int((time.perf_counter() - start_time) * 1000), 1)
        return {
            "status": "error",
            "provider": prov,
            "model": None,
            "latency_ms": latency_ms,
            "message": f"Connection to {PROVIDER_LABELS[prov]} timed out.",
            "error_code": "TIMEOUT",
            "diagnostic": f"Request to {prov} timed out after 10 seconds.",
            "action_hint": "Check network connectivity or retry in a few moments.",
        }
    except Exception as exception:
        latency_ms = max(int((time.perf_counter() - start_time) * 1000), 1)
        err_info = classify_llm_error(exception, prov, key)
        return {
            "status": "error",
            "provider": prov,
            "model": None,
            "latency_ms": latency_ms,
            "message": err_info["user_message"],
            "error_code": err_info["error_code"],
            "diagnostic": err_info["diagnostic"],
            "action_hint": err_info["action_hint"],
        }
