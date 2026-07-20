from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
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
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("REPO_ROOT_UNAVAILABLE")
    return Path(result.stdout.strip()).resolve()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(raw: bytes) -> str:
    return re.sub(r"\s+", " ", html.unescape(raw.decode("utf-8", errors="replace"))).casefold()


def request_url(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AAYS-TerraYield-Evidence/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    status = 0
    raw = b""
    final_url = url
    error = None
    content_type = None
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            status = int(response.status)
            final_url = response.geturl()
            content_type = response.headers.get("content-type")
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
    return {
        "http_status": status,
        "final_url": final_url,
        "content_type": content_type,
        "content_length_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "normalized": normalize(raw) if raw else "",
        "error": error,
        "retrieved_at": utc_now(),
    }


def marker_result(text: str, markers: list[str]) -> dict[str, Any]:
    checks = {marker: marker.casefold() in text for marker in markers}
    matched = sum(checks.values())
    total = len(checks)
    required = max(2, total - 1) if total else 0
    return {
        "checks": checks,
        "matched": matched,
        "total": total,
        "required": required,
        "pass": total > 0 and matched >= required,
    }


def main() -> int:
    root = repo_root()
    wave_paths = [
        root / "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_3_20260720.json",
        root / "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_4_20260720.json",
    ]
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in wave_paths:
        for candidate in read_json(path).get("candidates", []):
            candidate_id = str(candidate.get("candidate_id", ""))
            if candidate_id and candidate_id not in seen:
                seen.add(candidate_id)
                candidates.append(candidate)

    request_urls: list[str] = []
    for candidate in candidates:
        request_urls.append(candidate["source_url"])
        planning_url = candidate.get("official_planning_url")
        if planning_url:
            request_urls.append(planning_url)
    unique_urls = list(dict.fromkeys(request_urls))

    with concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="ready-to-sell-wave34") as pool:
        results = dict(zip(unique_urls, pool.map(request_url, unique_urls)))

    verified: list[dict[str, Any]] = []
    for candidate in candidates:
        source = results[candidate["source_url"]]
        source_markers = marker_result(source["normalized"], list(candidate.get("expected_markers", [])))
        source_live = source["http_status"] == 200 and source_markers["pass"]

        planning_url = candidate.get("official_planning_url")
        planning = results.get(planning_url) if planning_url else None
        planning_markers = marker_result(
            planning["normalized"] if planning else "",
            list(candidate.get("official_expected_markers", [])),
        ) if planning_url else None
        planning_live = bool(planning and planning["http_status"] == 200 and planning_markers and planning_markers["pass"])

        if source_live and planning_url and planning_live:
            score = 98 if candidate.get("official_planning_source_class") == "official_council_committee_decision" else 95
        elif source_live and not planning_url:
            score = max(90, min(94, int(candidate.get("source_confidence_score", 90))))
        elif source_live:
            score = 88
        else:
            score = 0

        row = dict(candidate)
        row.update({
            "retrieved_at": utc_now(),
            "http_status": source["http_status"],
            "final_url": source["final_url"],
            "content_type": source["content_type"],
            "content_length_bytes": source["content_length_bytes"],
            "sha256": source["sha256"],
            "marker_results": source_markers["checks"],
            "marker_match_count": source_markers["matched"],
            "marker_total": source_markers["total"],
            "source_live_verified": source_live,
            "source_confidence_score": score,
            "source_error": source["error"],
            "planning_http_status": planning["http_status"] if planning else None,
            "planning_sha256": planning["sha256"] if planning else None,
            "planning_marker_results": planning_markers["checks"] if planning_markers else None,
            "planning_marker_match_count": planning_markers["matched"] if planning_markers else None,
            "planning_marker_total": planning_markers["total"] if planning_markers else None,
            "planning_cross_check_verified": planning_live if planning_url else None,
            "planning_error": planning["error"] if planning else None,
            "parcel_match_confidence_score": 0,
            "geometry_match_status": "not_run",
            "promotion_allowed": False,
            "promotion_blocker": "CANONICAL_PARCEL_MATCH_AND_GEOMETRY_PROOF_NOT_RUN",
        })
        row.pop("normalized", None)
        verified.append(row)

    candidate_count = len(verified)
    live_count = sum(1 for row in verified if row["source_live_verified"])
    high_count = sum(1 for row in verified if row["source_confidence_score"] >= 90)
    hash_count = sum(1 for row in verified if row.get("sha256"))
    planning_targets = sum(1 for row in verified if row.get("official_planning_url"))
    planning_verified = sum(1 for row in verified if row.get("planning_cross_check_verified") is True)
    average_score = round(sum(row["source_confidence_score"] for row in verified) / max(1, candidate_count), 2)

    payload = {
        "schema_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "parcel_partition": PARTITION,
        "status": "RESEARCH_CANDIDATES_ONLY",
        "generated_at": utc_now(),
        "candidate_count": candidate_count,
        "source_live_verified_count": live_count,
        "high_source_confidence_count": high_count,
        "source_hash_count": hash_count,
        "planning_cross_check_target_count": planning_targets,
        "planning_cross_check_verified_count": planning_verified,
        "average_source_confidence": average_score,
        "promoted_row_count": 0,
        "promotion_policy": "canonical_parcel_match_and_geometry_proof_required",
        "candidates": verified,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }

    web_root = root / "england_map_web/data/aays_21_slots/ready_to_sell_3"
    docs_root = root / "docs/chatgpt_status/aays1/shards/ready_to_sell_3"
    write_json(web_root / "candidate_research_wave_34_latest.json", payload)
    write_json(web_root / "candidate_research_latest.json", payload)

    blockers = ["CANONICAL_PARCEL_MATCH_AND_GEOMETRY_PROOF_NOT_RUN"]
    if live_count < candidate_count:
        blockers.append(f"LIVE_SOURCE_VERIFICATION_PARTIAL:{live_count}/{candidate_count}")
    if planning_verified < planning_targets:
        blockers.append(f"PLANNING_CROSS_CHECK_PARTIAL:{planning_verified}/{planning_targets}")
    blockers.append("REMOTE_COMMIT_PUSH_READBACK_PENDING_SINGLE_COORDINATOR")

    status = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "parcel_partition": PARTITION,
        "status": "READY_FOR_SERIAL_PUBLISH_AND_REMOTE_ACCEPTANCE",
        "candidate_research": {
            "candidate_count": candidate_count,
            "source_live_verified_count": live_count,
            "high_source_confidence_count": high_count,
            "source_hash_count": hash_count,
            "planning_cross_check_verified_count": planning_verified,
            "planning_cross_check_target_count": planning_targets,
            "average_source_confidence": average_score,
            "promoted_row_count": 0,
        },
        "blockers": blockers,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "updated_at": utc_now(),
    }
    write_json(docs_root / "status/wave_34_live_hash_latest.json", status)

    report = [
        "# ReadyToSell 3 — Wave 3+4 Live HTTP/SHA256",
        "",
        f"- Candidates: {candidate_count}",
        f"- Live verified: {live_count}",
        f"- Source hashes: {hash_count}",
        f"- Source confidence >=90: {high_count}",
        f"- Planning cross-checks: {planning_verified}/{planning_targets}",
        "- Promoted rows: 0",
        "- Parcel/geometric promotion remains forbidden without canonical proof.",
        "",
        "## Blockers",
    ] + [f"- {blocker}" for blocker in blockers]
    report_path = docs_root / "reports/wave_34_live_hash_latest.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
