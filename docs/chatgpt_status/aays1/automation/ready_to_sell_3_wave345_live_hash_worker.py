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
WAVES = (
    "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_3_20260720.json",
    "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_4_20260720.json",
    "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_5_20260720.json",
)


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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_document(url: str, markers: list[str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AAYS-TerraYield-Evidence/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    status = 0
    final_url = url
    raw = b""
    error = None
    headers: dict[str, str] = {}
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
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

    decoded = html.unescape(raw.decode("utf-8", errors="replace"))
    normalized = re.sub(r"\s+", " ", decoded).casefold()
    marker_results = {marker: marker.casefold() in normalized for marker in markers}
    marker_count = sum(1 for value in marker_results.values() if value)
    marker_total = len(marker_results)
    required = max(2, marker_total - 1) if marker_total else 0
    verified = status == 200 and marker_count >= required
    return {
        "requested_url": url,
        "final_url": final_url,
        "retrieved_at": utc_now(),
        "http_status": status,
        "content_type": headers.get("content-type"),
        "content_length_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "marker_results": marker_results,
        "marker_match_count": marker_count,
        "marker_total": marker_total,
        "verified": verified,
        "error": error,
    }


def process_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    source = fetch_document(candidate["source_url"], list(candidate.get("expected_markers") or []))
    planning = None
    planning_url = candidate.get("official_planning_url")
    if planning_url:
        planning = fetch_document(planning_url, list(candidate.get("official_expected_markers") or []))

    source_verified = bool(source["verified"])
    planning_required = bool(planning_url)
    planning_verified = bool(planning and planning["verified"])
    if source_verified and planning_required and planning_verified:
        score = 98
    elif source_verified and not planning_required:
        score = 94
    elif source_verified:
        score = 88
    else:
        score = 0

    blockers: list[str] = []
    if not source_verified:
        blockers.append("SOURCE_HTTP_OR_MARKER_VERIFICATION_FAILED")
    if planning_required and not planning_verified:
        blockers.append("PLANNING_CROSS_CHECK_FAILED")
    blockers.extend(["CANONICAL_PARCEL_MATCH_NOT_RUN", "GEOMETRY_PROOF_NOT_RUN"])

    return {
        **candidate,
        "source_live_verified": source_verified,
        "source_http_status": source["http_status"],
        "source_final_url": source["final_url"],
        "source_hash": source["sha256"],
        "source_marker_match_count": source["marker_match_count"],
        "source_marker_total": source["marker_total"],
        "source_marker_results": source["marker_results"],
        "source_fetch_error": source["error"],
        "planning_cross_check_required": planning_required,
        "planning_cross_check_verified": planning_verified if planning_required else None,
        "planning_http_status": planning["http_status"] if planning else None,
        "planning_hash": planning["sha256"] if planning else None,
        "planning_marker_match_count": planning["marker_match_count"] if planning else None,
        "planning_marker_total": planning["marker_total"] if planning else None,
        "planning_fetch_error": planning["error"] if planning else None,
        "runner_source_confidence_score": score,
        "parcel_match_confidence_score": 0,
        "geometry_match_status": "not_run",
        "promotion_allowed": False,
        "promotion_blockers": blockers,
    }


def main() -> int:
    root = repo_root()
    candidates_by_id: dict[str, dict[str, Any]] = {}
    for relative in WAVES:
        payload = read_json(root / relative)
        for candidate in payload.get("candidates", []):
            candidates_by_id[str(candidate["candidate_id"])] = candidate

    candidates = list(candidates_by_id.values())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="ready-to-sell-wave345") as pool:
        rows = list(pool.map(process_candidate, candidates))

    live_count = sum(1 for row in rows if row["source_live_verified"])
    high_count = sum(1 for row in rows if row["runner_source_confidence_score"] >= 90)
    planning_required_count = sum(1 for row in rows if row["planning_cross_check_required"])
    planning_verified_count = sum(1 for row in rows if row["planning_cross_check_verified"] is True)
    hash_count = sum(1 for row in rows if row["source_hash"])
    average = round(sum(row["runner_source_confidence_score"] for row in rows) / max(1, len(rows)), 2)

    payload = {
        "schema_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "parcel_partition": PARTITION,
        "status": "RESEARCH_CANDIDATES_ONLY",
        "generated_at": utc_now(),
        "candidate_count": len(rows),
        "source_live_verified_count": live_count,
        "source_hash_count": hash_count,
        "runner_high_source_confidence_count": high_count,
        "average_runner_source_confidence": average,
        "planning_cross_check_required_count": planning_required_count,
        "planning_cross_check_verified_count": planning_verified_count,
        "promoted_row_count": 0,
        "parcel_match_count": 0,
        "geometry_match_count": 0,
        "concurrent_request_limit": 3,
        "promotion_policy": "canonical_parcel_match_and_geometry_proof_required",
        "candidates": rows,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }

    web_output = root / "england_map_web/data/aays_21_slots/ready_to_sell_3/candidate_research_latest.json"
    status_output = root / "docs/chatgpt_status/aays1/shards/ready_to_sell_3/status/wave345_live_hash_latest.json"
    report_output = root / "docs/chatgpt_status/aays1/shards/ready_to_sell_3/reports/wave345_live_hash_latest.md"
    write_json(web_output, payload)

    blockers: list[str] = []
    if live_count != len(rows):
        blockers.append(f"LIVE_SOURCE_VERIFICATION_PARTIAL:{live_count}/{len(rows)}")
    if planning_verified_count != planning_required_count:
        blockers.append(f"PLANNING_CROSS_CHECK_PARTIAL:{planning_verified_count}/{planning_required_count}")
    blockers.extend(["CANONICAL_PARCEL_MATCH_NOT_RUN", "GEOMETRY_PROOF_NOT_RUN", "REMOTE_PUBLISH_READBACK_PENDING"])
    status = {
        **payload,
        "status": "READY_FOR_SERIAL_PUBLISH_WITH_TRUTHFUL_BLOCKERS",
        "acceptance_pass": live_count == len(rows) and planning_verified_count == planning_required_count,
        "blockers": blockers,
        "web_output_path": str(web_output.relative_to(root)).replace("\\", "/"),
        "report_path": str(report_output.relative_to(root)).replace("\\", "/"),
    }
    write_json(status_output, status)

    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(
        "\n".join([
            "# ReadyToSell 3 — Wave 3/4/5 live source evidence",
            "",
            f"- Candidates processed: {len(rows)}",
            f"- Live source verified: {live_count}",
            f"- SHA256 stored: {hash_count}",
            f"- Runner confidence >=90: {high_count}",
            f"- Planning cross-checks: {planning_verified_count}/{planning_required_count}",
            "- Promoted rows: 0",
            "- Parcel matches: 0",
            "- Geometry matches: 0",
            f"- Blockers: {'; '.join(blockers)}",
            "- final_ready: false",
            "",
        ]),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
