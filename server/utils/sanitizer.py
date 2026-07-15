"""
Input Sanitization & Validation Utility
Ensures URLs are safe before passing to yt-dlp.
"""
import re
from urllib.parse import urlparse


# Blocked schemes to prevent SSRF
BLOCKED_SCHEMES = {"file", "ftp", "javascript", "data", "blob", "ssh"}

# Blocked private/loopback IP ranges
BLOCKED_HOSTS = [
    re.compile(r"^localhost$", re.IGNORECASE),
    re.compile(r"^127\.\d+\.\d+\.\d+$"),
    re.compile(r"^0\.0\.0\.0$"),
    re.compile(r"^::1$"),
    re.compile(r"^10\.\d+\.\d+\.\d+$"),
    re.compile(r"^172\.(1[6-9]|2\d|3[01])\.\d+\.\d+$"),
    re.compile(r"^192\.168\.\d+\.\d+$"),
    re.compile(r"^169\.254\.\d+\.\d+$"),  # Link-local
]


def sanitize_url(url: str) -> tuple[bool, str]:
    """
    Validate and sanitize a URL.
    Returns (is_valid, cleaned_url_or_error_message).
    """
    if not url:
        return False, "URL cannot be empty."

    # Strip whitespace
    url = url.strip()

    # Maximum URL length
    if len(url) > 2048:
        return False, "URL is too long (max 2048 characters)."

    # Must start with http:// or https://
    if not url.startswith(("http://", "https://")):
        # Try to prepend https:// as a convenience
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith("http"):
            url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format."

    # Validate scheme
    scheme = parsed.scheme.lower()
    if scheme in BLOCKED_SCHEMES:
        return False, f"Scheme '{scheme}' is not allowed."

    if scheme not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are supported."

    # Validate host
    host = parsed.hostname or ""
    if not host:
        return False, "URL must have a valid host."

    # Block private/loopback addresses (SSRF prevention)
    for blocked in BLOCKED_HOSTS:
        if blocked.match(host):
            return False, "Access to private or local addresses is not allowed."

    return True, url


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize a general string input."""
    if not value:
        return ""
    # Remove null bytes, control characters
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)
    return value[:max_length].strip()
