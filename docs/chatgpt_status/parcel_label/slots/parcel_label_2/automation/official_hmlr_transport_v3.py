from __future__ import annotations

import errno
import functools
import http.client
import http.cookiejar
import ipaddress
import socket
import sys
import urllib.request
from collections.abc import Callable, Iterable

BASE_RESOLVER = Callable[[str, int], list[str]]


def validate_public_addresses(addresses: Iterable[str]) -> list[str]:
    """Return stable unique globally routable addresses or fail closed."""
    unique: list[str] = []
    seen: set[str] = set()
    rejected: list[str] = []
    for raw in addresses:
        address = str(raw).strip()
        if not address:
            rejected.append("<empty>")
            continue
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as exc:
            raise RuntimeError(f"OFFICIAL_HMLR_DNS_ADDRESS_INVALID:{address}") from exc
        canonical = parsed.compressed
        if (
            not parsed.is_global
            or parsed.is_private
            or parsed.is_loopback
            or parsed.is_link_local
            or parsed.is_multicast
            or parsed.is_reserved
            or parsed.is_unspecified
        ):
            rejected.append(canonical)
            continue
        if canonical not in seen:
            seen.add(canonical)
            unique.append(canonical)
    if rejected:
        raise RuntimeError(f"OFFICIAL_HMLR_DNS_NON_PUBLIC_ADDRESS:{','.join(sorted(rejected))}")
    if not unique:
        raise RuntimeError("OFFICIAL_HMLR_DNS_NO_PUBLIC_ADDRESS")
    return unique


def resolve_public_addresses(host: str, port: int = 443) -> list[str]:
    try:
        records = socket.getaddrinfo(
            host,
            port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise RuntimeError(f"OFFICIAL_HMLR_DNS_RESOLUTION_FAILED:{host}:{exc}") from exc
    return validate_public_addresses(record[4][0] for record in records)


class PublicDNSHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection pinned to a validated DNS result while preserving TLS SNI."""

    def __init__(self, *args, resolver: BASE_RESOLVER = resolve_public_addresses, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._public_resolver = resolver

    def connect(self) -> None:
        sys.audit("http.client.connect", self, self.host, self.port)
        if self._tunnel_host:
            raise RuntimeError("OFFICIAL_HMLR_PROXY_TUNNEL_FORBIDDEN")
        addresses = self._public_resolver(self.host, self.port)
        errors: list[OSError] = []
        for address in addresses:
            sock = None
            try:
                sock = socket.create_connection(
                    (address, self.port),
                    self.timeout,
                    self.source_address,
                )
                try:
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                except OSError as exc:
                    if exc.errno != errno.ENOPROTOOPT:
                        raise
                self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
                return
            except OSError as exc:
                errors.append(exc)
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass
        detail = "; ".join(str(error) for error in errors) or "no connection attempts"
        raise OSError(f"OFFICIAL_HMLR_PUBLIC_ADDRESS_CONNECT_FAILED:{self.host}:{detail}")


class PublicDNSHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, *, resolver: BASE_RESOLVER = resolve_public_addresses, context=None) -> None:
        super().__init__(context=context)
        self.resolver = resolver

    def https_open(self, req):
        connection = functools.partial(PublicDNSHTTPSConnection, resolver=self.resolver)
        return self.do_open(connection, req, context=self._context)


def build_public_dns_opener(
    redirect_handler: urllib.request.HTTPRedirectHandler,
    *,
    cookie_jar: http.cookiejar.CookieJar | None = None,
    resolver: BASE_RESOLVER = resolve_public_addresses,
    context=None,
):
    jar = cookie_jar if cookie_jar is not None else http.cookiejar.CookieJar()
    proxy_handler = urllib.request.ProxyHandler({})
    https_handler = PublicDNSHTTPSHandler(resolver=resolver, context=context)
    opener = urllib.request.build_opener(
        proxy_handler,
        redirect_handler,
        urllib.request.HTTPCookieProcessor(jar),
        https_handler,
    )
    return opener, jar, proxy_handler, https_handler
