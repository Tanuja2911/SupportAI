"""
SupportAI Origin Guard Engine
Validates incoming Origin and Referer headers against tenant-configured
allowed domains and development localhost settings.
"""

import re
from urllib.parse import urlparse
from typing import Sequence
import idna

# Development host representations allowed when allow_localhost is True
DEV_HOSTS: set[str] = {
    "localhost",
    "127.0.0.1",
    "::1",
    "[::1]",
    "0.0.0.0",
    "null",
}

# Untrusted / browser-internal pseudo-schemes that must never be treated as valid origins
BLOCKED_SCHEMES: tuple[str, ...] = (
    "data:",
    "javascript:",
    "vbscript:",
    "about:",
    "blob:",
)


def clean_domain_entry(entry: str | None) -> str | None:
    """
    Sanitize an entry from allowed_domains.

    Operations:
    1. Trims leading and trailing whitespace.
    2. Rejects entries containing null bytes.
    3. Converts to lowercase.
    4. Strips scheme prefixes (e.g. http://, https://).
    5. Strips path, query parameters, and fragments.
    6. Strips port numbers, rejecting smuggled hostnames (containing dots).
    7. Strips leading wildcard prefixes (e.g. *. or .).
    8. Strips trailing dots (FQDN root qualification).
    9. Performs IDNA / Punycode normalization so unicode and punycode match seamlessly.
    10. Returns cleaned hostname string, or None if entry is empty/invalid.
    """
    if not entry or not isinstance(entry, str):
        return None
    d = entry.strip().lower()
    if not d or "\x00" in d or "%00" in d:
        return None

    # Strip scheme if present
    if "://" in d:
        d = d.split("://", 1)[1]

    # Strip path, query, hash
    for sep in ("/", "?", "#"):
        d = d.split(sep)[0]

    # Strip userinfo if present
    if "@" in d:
        d = d.rsplit("@", 1)[1]

    # Strip port (handle IPv6 brackets)
    if d.startswith("[") and "]" in d:
        closing = d.find("]")
        rest = d[closing + 1 :]
        if rest.startswith(":"):
            port_part = rest[1:]
            if "." in port_part:
                return None
        d = d[1:closing]
    elif ":" in d:
        if d.count(":") == 1:
            host_part, port_part = d.split(":", 1)
            if "." in port_part:
                return None
            d = host_part
        elif d.count(":") > 1:
            # multiple colons without brackets: could be unbracketed IPv6 like ::1
            pass

    # Strip leading *. or . and trailing .
    d = re.sub(r"^\*\.?", "", d)
    d = d.lstrip(".")
    d = d.rstrip(".")
    if not d:
        return None

    try:
        d = idna.encode(d).decode("ascii")
    except Exception:
        pass

    return d if d else None


def extract_domain(origin: str | None, referer: str | None) -> str | None:
    """
    Extract and normalize the domain/host from HTTP Origin or Referer headers.

    Normalization rules:
    - Prioritizes Origin header; falls back to Referer header if Origin is absent or empty.
    - Rejects headers containing null bytes (\\x00 or %00).
    - If input is literal "null" (browser sandboxed iframe or local file origin), returns "null".
    - If input starts with file:// scheme, treats as local file origin and returns "null".
    - Rejects untrusted pseudo-schemes (data:, javascript:, vbscript:, about:, blob:) by returning None.
    - Strips protocol prefixes (http://, https://, etc.).
    - Validates port numbers: rejects smuggled hostnames (containing dots) after colon.
    - Strips URL paths, query parameters, trailing slashes, fragments, and trailing dots.
    - Normalizes host string to lowercase and applies IDNA / Punycode encoding.
    - If neither header is provided, or extraction fails, returns None.
    """
    raw: str | None = None
    if origin is not None and origin.strip():
        raw = origin.strip()
    elif referer is not None and referer.strip():
        raw = referer.strip()

    if raw is None:
        return None

    if "\x00" in raw or "%00" in raw.lower():
        return None

    raw_lower = raw.lower()

    # Block pseudo-schemes immediately
    for scheme in BLOCKED_SCHEMES:
        if raw_lower.startswith(scheme):
            return None

    # Handle null origin (sandboxed iframe / privacy context)
    if raw_lower == "null":
        return "null"

    # Handle local file:// scheme
    if raw_lower.startswith("file://") or raw_lower == "file:":
        return "null"

    # Handle IPv6 without brackets
    if raw_lower in ("::1", "[::1]"):
        return "::1"

    # Normalize URL for urlparse: prepend // if scheme is missing so netloc is parsed
    candidate = raw_lower
    if not candidate.startswith("//") and "://" not in candidate:
        candidate = "//" + candidate

    try:
        parsed = urlparse(candidate)
        hostname = parsed.hostname
        if hostname:
            netloc_host_port = parsed.netloc.rsplit("@", 1)[-1]
            if netloc_host_port.startswith("[") and "]" in netloc_host_port:
                after_bracket = netloc_host_port.split("]", 1)[1]
                if after_bracket.startswith(":"):
                    port_str = after_bracket[1:]
                    if "." in port_str:
                        return None
                elif after_bracket:
                    return None
            elif ":" in netloc_host_port:
                if netloc_host_port.count(":") == 1:
                    _, port_str = netloc_host_port.split(":", 1)
                    if "." in port_str:
                        return None

            hostname = hostname.lower().strip().rstrip(".")
            try:
                hostname = idna.encode(hostname).decode("ascii")
            except Exception:
                pass
            return hostname
    except Exception:
        pass

    # Fallback parsing in case of unusual URI structures
    cleaned = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", raw_lower)
    if cleaned.startswith("//"):
        cleaned = cleaned.lstrip("/")
    authority = cleaned.split("/")[0].split("?")[0].split("#")[0]
    if "@" in authority:
        authority = authority.rsplit("@", 1)[1]
    if authority.startswith("[") and "]" in authority:
        closing = authority.find("]")
        rest = authority[closing + 1 :]
        if rest.startswith(":"):
            port_part = rest[1:]
            if "." in port_part:
                return None
        elif rest:
            return None
        authority = authority[1:closing]
    elif ":" in authority:
        if authority.count(":") == 1:
            host_part, port_part = authority.split(":", 1)
            if "." in port_part:
                return None
            authority = host_part
    authority = authority.strip().rstrip(".")
    if not authority:
        return None
    try:
        authority = idna.encode(authority).decode("ascii")
    except Exception:
        pass
    return authority if authority else None


def validate_origin(
    origin: str | None,
    referer: str | None,
    allowed_domains: Sequence[str] | None,
    allow_localhost: bool = True,
) -> bool:
    """
    Validate incoming Origin or Referer header against allowed domains and dev settings.

    Rules:
    1. Rejection of null bytes in raw origin or referer (\\x00 or %00).
    2. Localhost / Dev Mode (allow_localhost = True):
       - If both Origin and Referer are absent (None or empty/whitespace), returns True.
       - If extracted domain is in DEV_HOSTS ("localhost", "127.0.0.1", "::1", "[::1]", "0.0.0.0", "null"),
         returns True.
    3. Localhost Disabled (allow_localhost = False):
       - If headers are absent, returns False.
       - Localhost/null/dev origins are rejected unless explicitly listed in allowed_domains.
    4. Untrusted Pseudo-schemes:
       - Inputs starting with data:, javascript:, etc. are rejected (returns False) regardless of allow_localhost.
    5. Domain Whitelist Matching:
       - Sanitizes each entry in allowed_domains (stripping scheme, port, paths, leading *., trailing .).
       - IDNA / Punycode normalization ensures international domains match browser ASCII punycode.
       - Exact match: extracted_domain == allowed_domain.
       - Subdomain match: extracted_domain.endswith("." + allowed_domain).
       - Prevents prefix spoofing (evil-example.com does NOT match example.com).
       - Prevents suffix spoofing (example.com.evil.co does NOT match example.com).
       - Returns True on first match; False if no match found.
    """
    if origin is not None and ("\x00" in origin or "%00" in origin.lower()):
        return False
    if referer is not None and ("\x00" in referer or "%00" in referer.lower()):
        return False

    is_origin_empty = (origin is None or not origin.strip())
    is_referer_empty = (referer is None or not referer.strip())

    # When both headers are omitted
    if is_origin_empty and is_referer_empty:
        return bool(allow_localhost)

    # Check for blocked pseudo-schemes directly on the provided raw header
    raw = (origin.strip() if not is_origin_empty else referer.strip()).lower()
    for scheme in BLOCKED_SCHEMES:
        if raw.startswith(scheme):
            return False

    domain = extract_domain(origin, referer)
    if domain is None:
        return False

    # Dev / Localhost check
    if allow_localhost and (domain in DEV_HOSTS or domain.strip("[]") in DEV_HOSTS):
        return True

    # Check allowed_domains
    if not allowed_domains:
        return False

    cleaned_allowed: list[str] = []
    for d in allowed_domains:
        cd = clean_domain_entry(d)
        if cd:
            cleaned_allowed.append(cd)

    for allowed in cleaned_allowed:
        if domain == allowed or domain.strip("[]") == allowed:
            return True
        if domain.endswith("." + allowed):
            return True

    return False
