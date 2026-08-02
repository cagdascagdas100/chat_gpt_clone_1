from __future__ import annotations

import ipaddress
import urllib.parse
import urllib.request

_EXACT_TRUSTED_REDIRECT_HOSTS = frozenset({
    "datapub-prd-s3-bucket.s3.amazonaws.com",
})


def _normalise_host(host: str) -> str:
    return host.casefold()


def _trusted_host(host: str, primary_host: str) -> bool:
    host = _normalise_host(host)
    primary = _normalise_host(primary_host)
    return (
        host == primary
        or host == "landregistry.gov.uk"
        or host.endswith(".landregistry.gov.uk")
        or host in _EXACT_TRUSTED_REDIRECT_HOSTS
    )


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


class TrustedHMLRRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, primary_host: str) -> None:
        super().__init__()
        self.primary_host = primary_host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        absolute = urllib.parse.urljoin(req.full_url, newurl)
        validate_official_hmlr_url(absolute, primary_host=self.primary_host)
        return super().redirect_request(req, fp, code, msg, headers, absolute)
