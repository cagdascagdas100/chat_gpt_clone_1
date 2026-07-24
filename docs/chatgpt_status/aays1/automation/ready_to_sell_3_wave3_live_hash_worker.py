from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "ready_to_sell_3"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
PARTITION = {"start": 61523, "end": 92283, "count": 30761, "canonical_count": 92283}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError("REPO_ROOT_UNAVAILABLE")
    return Path(completed.stdout.strip()).resolve()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_page(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AAYS-TerraYield-Evidence/1.1)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    status = 0
    final_url = url
    headers: dict[str, str] = {}
    raw = b""
    error = None
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            status = int(response.status)
            final_url = response.geturl()
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            raw = response.read(8_000_000)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        final_url = exc.geturl()
        error = f"HTTPError:{exc.code}"
        try:
            raw = exc.read(2_000_000)
        except Exception:
            raw = b""
    except Exception as exc:
        error = f"{type(exc).__name__}:{exc}"
    text = re.sub(r"\s+", " ", html.unescape(raw.decode("utf-8", errors="replace"))).casefold()
    return {
        "http_status": status,
        "final_url": final_url,
        "content_type": headers.get("content-type"),
        "content_length_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "normalized_text": text,
        "error": error,
    }


def verify_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    source = fetch_page(str(candidate["source_url"]))
    markers = [str(value) for value in candidate.get("expected_markers") or [] if str(value).strip()]
    marker_results = {marker: marker.casefold() in source["normalized_text"] for marker in markers}
    marker_count = sum(marker_results.values())
    marker_total = len(marker_results)
    source_live = source["http_status"] == 200 and marker_count >= max(2, marker_total - 1)

    official_url = candidate.get("official_planning_url")
    official = fetch_page(str(official_url)) if official_url else None
    official_markers = [
        str(value)
        for value in (candidate.get("planning_reference"), candidate.get("title"), candidate.get("location"))
        if value
    ][:3]
    official_results = {
        marker: marker.casefold() in official["normalized_text"]
        for marker in official_markers
    } if official else {}
    official_verified = bool(
        official
        and official["http_status"] == 200
        and official_results
        and sum(official_results.values()) >= max(1, len(official_results) - 1)
    )

    source_type = str(candidate.get("source_type") or "").casefold()
    if source_live:
        score = 96 if "official_agent" in source_type else 94 if marker_count == marker_total else 88
        if official_verified:
            score = min(99, score + 4)
    else:
        score = 0

    return {
        **candidate,
        "retrieved_at": utc_now(),
        "http_status": source["http_status"],
        "final_url": source["final_url"],
        "content_type": source["content_type"],
        "content_length_bytes": source["content_length_bytes"],
        "sha256": source["sha256"],
        "marker_results": marker_results,
        "marker_match_count": marker_count,
        "marker_total": marker_total,
        "source_live_verified": source_live,
        "official_planning_http_status": official["http_status"] if official else None,
        "official_planning_sha256": official["sha256"] if official else None,
        "official_planning_marker_results": official_results,
        "official_planning_verified": official_verified,
        "source_confidence_score": score,
        "parcel_match_confidence_score": 0,
        "geometry_match_status": "not_run",
        "promotion_allowed": False,
        "promotion_blocker": "CANONICAL_PARCEL_MATCH_AND_GEOMETRY_PROOF_NOT_RUN",
        "error": source["error"],
        "official_planning_error": official["error"] if official else None,
    }


def main() -> int:
    root = repo_root()
    slot_id = os.environ.get("AAYS_SLOT_ID", SLOT_ID)
    task_id = os.environ.get("AAYS_TASK_ID", "aays1-ready-to-sell-3-wave3-live-hash-20260720")
    if slot_id != SLOT_ID:
        raise RuntimeError(f"SLOT_ID_MISMATCH:{slot_id}")

    web_root = root / "england_map_web/data/aays_21_slots/ready_to_sell_3"
    docs_root = root / "docs/chatgpt_status/aays1/shards/ready_to_sell_3"
    preload_path = web_root / "research_preload_wave_3_20260720.json"
    preload = read_json(preload_path) or {}
    candidates = [value for value in preload.get("candidates") or [] if value.get("source_url")]

    with concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="rts3-wave3") as pool:
        rows = list(pool.map(verify_candidate, candidates))

    live_count = sum(1 for row in rows if row["source_live_verified"])
    hash_count = sum(1 for row in rows if row.get("sha256"))
    official_count = sum(1 for row in rows if row.get("official_planning_verified"))
    high_count = sum(1 for row in rows if int(row.get("source_confidence_score") or 0) >= 90)
    average_score = round(
        sum(int(row.get("source_confidence_score") or 0) for row in rows) / max(1, len(rows)),
        2,
    )

    result = {
        "schema_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "task_id": task_id,
        "parcel_partition": PARTITION,
        "status": "RESEARCH_CANDIDATES_ONLY",
        "generated_at": utc_now(),
        "candidate_count": len(rows),
        "source_live_verified_count": live_count,
        "source_hash_count": hash_count,
        "official_planning_verified_count": official_count,
        "high_source_confidence_count": high_count,
        "average_source_confidence": average_score,
        "promoted_row_count": 0,
        "concurrent_request_limit": 3,
        "promotion_policy": "canonical_parcel_match_and_geometry_proof_required",
        "candidates": rows,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write_json(web_root / "candidate_research_wave_3_latest.json", result)

    blockers = []
    if live_count < len(rows):
        blockers.append(f"LIVE_SOURCE_MARKER_VERIFICATION_PARTIAL:{live_count}/{len(rows)}")
    if hash_count < len(rows):
        blockers.append(f"SOURCE_HASH_PARTIAL:{hash_count}/{len(rows)}")
    if official_count < 2:
        blockers.append(f"OFFICIAL_PLANNING_CROSS_CHECK_PARTIAL:{official_count}/2")
    blockers.append("CANONICAL_PARCEL_AND_GEOMETRY_MATCH_NOT_RUN")

    status = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "task_id": task_id,
        "status": "WAVE_3_LIVE_HASH_COMPLETE_CANDIDATE_ONLY",
        "candidate_count": len(rows),
        "live_verified_count": live_count,
        "source_hash_count": hash_count,
        "official_planning_verified_count": official_count,
        "high_source_confidence_count": high_count,
        "average_source_confidence": average_score,
        "promoted_row_count": 0,
        "blockers": blockers,
        "single_runner_only": True,
        "new_runner": False,
        "parallel_runner": False,
        "final_ready": False,
        "updated_at": utc_now(),
    }
    write_json(docs_root / "status/wave_3_live_hash_latest.json", status)

    report = [
        "# ReadyToSell 3 — Wave 3 Live Hash",
        "",
        f"- candidate_count: `{len(rows)}`",
        f"- live_verified: `{live_count}`",
        f"- source_hashes: `{hash_count}`",
        f"- official_planning_verified: `{official_count}`",
        f"- source_confidence_gte_90: `{high_count}`",
        f"- average_source_confidence: `{average_score}`",
        "- promoted_rows: `0`",
        f"- blockers: `{' ; '.join(blockers)}`",
        "",
        "No candidate was promoted without canonical parcel and geometry evidence.",
    ]
    report_path = docs_root / "reports/wave_3_live_hash_latest.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
