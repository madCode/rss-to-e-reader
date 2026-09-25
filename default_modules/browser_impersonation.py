"""
Retries blocked requests while impersonating a real browser.

Many sites (often behind Cloudflare, Akamai or similar) turn away scripts based on how the connection looks, not
on what is requested: the TLS handshake and HTTP/2 settings of Python's requests library are easy to tell apart from
a browser's, whatever User-Agent header is sent. curl_cffi (https://github.com/lexiforest/curl_cffi) makes
connections that look like Chrome's or Safari's.

Plain requests are still tried first: some sites do the opposite and block impersonated browsers, and requests is
lighter. Only responses that look blocked (see looks_blocked) are retried.

This doesn't get past JavaScript challenges ("Just a moment...") or real paywalls; those need a real browser or a
subscription (pass a requests.Session with your cookies to DefaultArticleFetcher).

curl_cffi is optional. Without it, impersonated_get returns None and nothing is retried.
"""
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

DEFAULT_IMPERSONATE = 'chrome'
BLOCKED_STATUS_CODES = {401, 403, 429, 503}
# Text found in bot-check pages that some sites serve with a 200 status.
CHALLENGE_MARKERS = (
    '<title>Just a moment...</title>', 'cf-browser-verification', 'challenge-platform', '_Incapsula_Resource',
    'captcha-delivery.com', 'px-captcha', 'Enable JavaScript and cookies to continue',
)
CHALLENGE_PAGE_MAX_BYTES = 150 * 1024


def is_available() -> bool:
    try:
        import curl_cffi  # type: ignore # noqa: F401
        return True
    except ImportError:
        return False


def looks_blocked(response: Any) -> bool:
    """True for responses that look like a bot check rather than the page itself."""
    if response.status_code in BLOCKED_STATUS_CODES:
        return True
    content = response.content or b''
    if response.status_code == 200 and len(content) < CHALLENGE_PAGE_MAX_BYTES:
        head = content[:30000].decode('utf-8', errors='ignore')
        return any(marker in head for marker in CHALLENGE_MARKERS)
    return False


def _cookies_for(session: Optional[requests.Session], url: str) -> Dict[str, str]:
    """The session's cookies that apply to url's host, so subscriptions keep working when impersonating."""
    if session is None:
        return {}
    host = (urlparse(url).hostname or '').lower()
    cookies = {}
    for cookie in session.cookies:
        domain = (cookie.domain or '').lstrip('.').lower()
        if not domain or host == domain or host.endswith('.' + domain):
            if cookie.value is not None:
                cookies[cookie.name] = cookie.value
    return cookies


def impersonated_get(
    url: str, impersonate: str = DEFAULT_IMPERSONATE, timeout: float = 20,
    session: Optional[requests.Session] = None, referer: str = '',
) -> Optional[Any]:
    """
    GETs url as the given browser ('chrome', 'safari', 'firefox', 'edge', or a specific version like 'chrome131';
    see curl_cffi's docs). Like requests, curl_cffi honours HTTPS_PROXY and REQUESTS_CA_BUNDLE/CURL_CA_BUNDLE.
    Returns curl_cffi's response (which has the same status_code/content/headers/url/encoding attributes as
    requests'), or None if curl_cffi isn't installed or the request failed.
    """
    try:
        from curl_cffi import requests as curl_requests  # type: ignore
    except ImportError:
        return None
    try:
        return curl_requests.get(
            url, impersonate=impersonate, timeout=timeout, allow_redirects=True,
            cookies=_cookies_for(session, url) or None, headers={'Referer': referer} if referer else None,
        )
    except Exception:
        return None
