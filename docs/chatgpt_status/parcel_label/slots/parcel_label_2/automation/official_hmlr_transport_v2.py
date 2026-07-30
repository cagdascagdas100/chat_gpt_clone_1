from __future__ import annotations

import http.cookiejar
import ipaddress
import urllib.parse
import urllib.request


def _normalise_host(host: str) -> str:
    return host.casefold()


def _trusted_host(host: str, primary_host: str) -> bool:
    host = _normalise_host(host)
    primary = _normalise_host(primary_host)
    return host == primary or host == "landregistry.gov.uk" or host.endswith(".landregistry.gov.uk")


def validate_official_hmlr_url(url: str, *, primary_host: str, require_primary: bool = False) -> str:
    if any(ord(char) < 32 or ord(char) == 127 for char in url):
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_CONTAINS_CONTROL_CHARACTER")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.casefold() != "https":
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_NOT_HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_CONTAINS_USERINFO")
    if parsed.fragment:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_CONTAINS_FRAGMENT")
    raw_host = parsed.hostname or ""
    if not raw_host:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_HOST_MISSING")
    if raw_host.endswith("."):
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_HOST_TRAILING_DOT")
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_PORT_INVALID") from exc
    if port not in (None, 443):
        raise RuntimeError(f"OFFICIAL_DOWNLOAD_URL_PORT_NOT_443:{port}")
    try:
        ipaddress.ip_address(raw_host)
    except ValueError:
        pass
    else:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_IP_LITERAL_FORBIDDEN")
    host = _normalise_host(raw_host)
    primary = _normalise_host(primary_host)
    if require_primary and host != primary:
        raise RuntimeError(f"OFFICIAL_DOWNLOAD_INDEX_REDIRECT_CROSS_ORIGIN:{host}")
    if not _trusted_host(host, primary):
        raise RuntimeError(f"OFFICIAL_DOWNLOAD_URL_UNTRUSTED_HOST:{host}")
    return url


def validate_redirect_target(
    current_url: str,
    new_url: str,
    *,
    primary_host: str,
    require_primary: bool,
) -> str:
    absolute = urllib.parse.urljoin(current_url, new_url)
    return validate_official_hmlr_url(
        absolute,
        primary_host=primary_host,
        require_primary=require_primary,
    )


class TrustedHMLRRedirectHandler(urllib.request.HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2

    def __init__(self, primary_host: str, *, require_primary: bool) -> None:
        super().__init__()
        self.primary_host = primary_host
        self.require_primary = require_primary

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        absolute = validate_redirect_target(
            req.full_url,
            newurl,
            primary_host=self.primary_host,
            require_primary=self.require_primary,
        )
        return super().redirect_request(req, fp, code, msg, headers, absolute)


def build_trusted_opener(
    primary_host: str,
    *,
    require_primary: bool,
    cookie_jar: http.cookiejar.CookieJar | None = None,
):
    jar = cookie_jar if cookie_jar is not None else http.cookiejar.CookieJar()
    handler = TrustedHMLRRedirectHandler(primary_host, require_primary=require_primary)
    opener = urllib.request.build_opener(handler, urllib.request.HTTPCookieProcessor(jar))
    return opener, jar, handler
