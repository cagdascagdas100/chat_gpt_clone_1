#!/usr/bin/env python3
import hashlib, urllib.request
from datetime import datetime, timezone
import aays_fg7_severn_331_342_20260818 as m


def source_verify_v2():
    req = urllib.request.Request(
        m.SOURCE,
        headers={"User-Agent": "Mozilla/5.0 AAYS-FG7-Severn/2026-08-18", "Accept": "text/html,application/xhtml+xml"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        final = r.geturl()
        status = getattr(r, "status", 200)
    if status != 200:
        raise RuntimeError(f"SEVERN_SOURCE_HTTP_STATUS:{status}")
    txt = m.normalize(raw.decode("utf-8", "replace"))
    identity_tokens = [
        "The Severn Bridges",
        "M48 Severn Bridge: Upcoming resurfacing trial",
        "Saturday 01 August until Sunday 27 September 2026",
        "Contraflow will be in place from 8pm Saturday 08 August until 8pm Friday 18 September 2026",
    ]
    for token in identity_tokens:
        nt = m.normalize(token)
        if nt not in txt:
            raise RuntimeError(f"SEVERN_SOURCE_IDENTITY_TOKEN_MISSING:{token!r}:FINAL={final!r}:BYTES={len(raw)}")
    for batch, key, name, stage, tokens in m.BATCHES:
        for token in tokens:
            nt = m.normalize(token)
            if nt not in txt:
                raise RuntimeError(f"SEVERN_BATCH_TOKEN_MISSING:{batch}:{token!r}:FINAL={final!r}:BYTES={len(raw)}")
    return hashlib.sha256(raw).hexdigest(), len(raw), datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), final


m.source_verify = source_verify_v2

if __name__ == "__main__":
    m.main()
