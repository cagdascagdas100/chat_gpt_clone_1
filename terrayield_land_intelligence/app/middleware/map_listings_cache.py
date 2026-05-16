from __future__ import annotations

import time
from collections import OrderedDict
from threading import RLock

from starlette.types import ASGIApp, Message, Receive, Scope, Send


CACHEABLE_PATHS = {
    "/map/listings",
    "/map/listings/",
    "/map/sales-history/combined",
    "/map/sales-history/combined/",
}

DEFAULT_TTL_SECONDS = 300
MAX_CACHE_ENTRIES = 128


class MapListingsCacheMiddleware:
    """Pure ASGI warm response cache for heavy read-only map endpoints.

    Safe scope:
    - GET only
    - path + raw query string
    - HTTP 200 only
    - in-process TTL cache
    - no DB write, no DDL, no migration, no deploy side effects
    """

    def __init__(
        self,
        app: ASGIApp,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_entries: int = MAX_CACHE_ENTRIES,
    ) -> None:
        self.app = app
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._cache: OrderedDict[str, tuple[float, int, list[tuple[bytes, bytes]], bytes]] = OrderedDict()
        self._lock = RLock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method") or "").upper()
        path = str(scope.get("path") or "")

        if method != "GET" or path not in CACHEABLE_PATHS:
            await self.app(scope, receive, send)
            return

        raw_query = scope.get("query_string") or b""
        key = f"{path}?{raw_query.decode('latin-1')}"
        now = time.monotonic()

        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                expires_at, status_code, headers, body = cached
                if expires_at > now:
                    self._cache.move_to_end(key)
                    await send(
                        {
                            "type": "http.response.start",
                            "status": status_code,
                            "headers": self._set_header(headers, b"x-aays-cache", b"HIT"),
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": body,
                            "more_body": False,
                        }
                    )
                    return
                self._cache.pop(key, None)

        status_holder = {"status": 500}
        headers_holder: dict[str, list[tuple[bytes, bytes]]] = {"headers": []}
        chunks: list[bytes] = []

        async def capture_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = int(message.get("status", 500))
                headers_holder["headers"] = self._strip_headers(list(message.get("headers") or []))
                return

            if message["type"] == "http.response.body":
                body = message.get("body", b"") or b""
                if body:
                    chunks.append(body)

                if message.get("more_body", False):
                    return

                full_body = b"".join(chunks)
                response_headers = headers_holder["headers"]
                response_headers = self._set_header(response_headers, b"x-aays-cache", b"MISS")
                response_headers = self._set_header(response_headers, b"content-length", str(len(full_body)).encode("ascii"))

                await send(
                    {
                        "type": "http.response.start",
                        "status": status_holder["status"],
                        "headers": response_headers,
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": full_body,
                        "more_body": False,
                    }
                )

                if status_holder["status"] == 200:
                    cache_headers = self._set_header(headers_holder["headers"], b"x-aays-cache", b"HIT")
                    cache_headers = self._set_header(cache_headers, b"content-length", str(len(full_body)).encode("ascii"))

                    with self._lock:
                        self._cache[key] = (
                            now + self.ttl_seconds,
                            status_holder["status"],
                            cache_headers,
                            full_body,
                        )
                        self._cache.move_to_end(key)
                        while len(self._cache) > self.max_entries:
                            self._cache.popitem(last=False)
                return

            await send(message)

        await self.app(scope, receive, capture_send)

    @staticmethod
    def _strip_headers(headers: list[tuple[bytes, bytes]]) -> list[tuple[bytes, bytes]]:
        excluded = {
            b"connection",
            b"keep-alive",
            b"proxy-authenticate",
            b"proxy-authorization",
            b"te",
            b"trailer",
            b"transfer-encoding",
            b"upgrade",
            b"x-aays-cache",
            b"content-length",
        }
        return [(k, v) for k, v in headers if k.lower() not in excluded]

    @staticmethod
    def _set_header(headers: list[tuple[bytes, bytes]], name: bytes, value: bytes) -> list[tuple[bytes, bytes]]:
        lname = name.lower()
        cleaned = [(k, v) for k, v in headers if k.lower() != lname]
        cleaned.append((name, value))
        return cleaned
