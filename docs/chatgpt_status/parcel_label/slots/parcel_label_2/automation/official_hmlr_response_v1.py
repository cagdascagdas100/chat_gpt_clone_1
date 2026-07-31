from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, NamedTuple


class ResponseIntegrity(NamedTuple):
    status: int
    content_length: int | None
    transfer_encoding: str | None
    content_encoding: str | None


def _header_values(headers, name: str) -> list[str]:
    getter = getattr(headers, "get_all", None)
    if callable(getter):
        raw_values = getter(name) or []
    else:
        value = headers.get(name) if headers is not None else None
        raw_values = [] if value is None else [value]
    values: list[str] = []
    for raw in raw_values:
        values.extend(part.strip() for part in str(raw).split(",") if part.strip())
    return values


def _single_token_header(headers, name: str) -> str | None:
    values = [value.casefold() for value in _header_values(headers, name)]
    if not values:
        return None
    if len(set(values)) != 1:
        raise RuntimeError(f"OFFICIAL_HMLR_RESPONSE_{name.upper().replace('-', '_')}_CONFLICT")
    return values[0]


def _content_length(headers) -> int | None:
    values = _header_values(headers, "Content-Length")
    if not values:
        return None
    parsed: list[int] = []
    for value in values:
        if not value.isascii() or not value.isdigit():
            raise RuntimeError("OFFICIAL_HMLR_RESPONSE_CONTENT_LENGTH_INVALID")
        parsed.append(int(value))
    if len(set(parsed)) != 1:
        raise RuntimeError("OFFICIAL_HMLR_RESPONSE_CONTENT_LENGTH_CONFLICT")
    return parsed[0]


def validate_response_integrity(response, *, limit: int) -> ResponseIntegrity:
    status = getattr(response, "status", None)
    if status is None:
        getter = getattr(response, "getcode", None)
        status = getter() if callable(getter) else None
    if status != 200:
        raise RuntimeError(f"OFFICIAL_HMLR_RESPONSE_STATUS_NOT_200:{status}")

    headers = getattr(response, "headers", None)
    if headers is None:
        raise RuntimeError("OFFICIAL_HMLR_RESPONSE_HEADERS_MISSING")
    if _header_values(headers, "Content-Range"):
        raise RuntimeError("OFFICIAL_HMLR_RESPONSE_CONTENT_RANGE_FORBIDDEN")

    content_length = _content_length(headers)
    if content_length is not None and content_length > limit:
        raise RuntimeError(f"OFFICIAL_HMLR_RESPONSE_CONTENT_LENGTH_LIMIT_EXCEEDED:{limit}")

    transfer_encoding = _single_token_header(headers, "Transfer-Encoding")
    if transfer_encoding is not None and transfer_encoding != "chunked":
        raise RuntimeError(f"OFFICIAL_HMLR_RESPONSE_TRANSFER_ENCODING_UNSUPPORTED:{transfer_encoding}")
    if transfer_encoding is not None and content_length is not None:
        raise RuntimeError("OFFICIAL_HMLR_RESPONSE_LENGTH_AND_TRANSFER_ENCODING_CONFLICT")

    content_encoding = _single_token_header(headers, "Content-Encoding")
    if content_encoding not in (None, "identity"):
        raise RuntimeError(f"OFFICIAL_HMLR_RESPONSE_CONTENT_ENCODING_UNSUPPORTED:{content_encoding}")

    return ResponseIntegrity(
        status=int(status),
        content_length=content_length,
        transfer_encoding=transfer_encoding,
        content_encoding=content_encoding,
    )


def verify_complete_body(observed_bytes: int, metadata: ResponseIntegrity) -> int:
    if observed_bytes <= 0:
        raise RuntimeError("OFFICIAL_HMLR_RESPONSE_BODY_EMPTY")
    if metadata.content_length is not None and observed_bytes != metadata.content_length:
        raise RuntimeError(
            f"OFFICIAL_HMLR_RESPONSE_BODY_LENGTH_MISMATCH:{observed_bytes}:{metadata.content_length}"
        )
    return observed_bytes


def read_bounded_complete(response: BinaryIO, *, limit: int, metadata: ResponseIntegrity) -> bytes:
    payload = response.read(limit + 1)
    if len(payload) > limit:
        raise RuntimeError(f"OFFICIAL_HMLR_RESPONSE_SIZE_LIMIT_EXCEEDED:{limit}")
    verify_complete_body(len(payload), metadata)
    return payload


def verify_file_complete(path: Path, metadata: ResponseIntegrity) -> int:
    return verify_complete_body(path.stat().st_size, metadata)
