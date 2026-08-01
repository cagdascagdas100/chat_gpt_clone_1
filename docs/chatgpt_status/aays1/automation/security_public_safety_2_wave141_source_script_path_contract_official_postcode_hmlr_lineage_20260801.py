from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
TASK_PATH = ROOT / "docs/chatgpt_status/aays1/queue/0154_security_public_safety_2_wave141_source_script_path_contract_official_postcode_hmlr_lineage_20260801.v3.task.json"
MANIFEST_PATH = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave141_official_source_manifest.json"
WAVE140_STATUS = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave140_status_latest.json"
WAVE140_EVIDENCE = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave140_evidence_latest.json"
WAVE140_OUTPUT = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_hmlr_inspire_os_open_uprn_primary_binding_wave140_latest.json"
MANUAL = ROOT / "docs/chatgpt_status/_shared/manual_actions/security_public_safety_2.json"
OUTPUT = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_postcode_hmlr_lineage_contract_wave141_latest.json"
WEBSITE = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_postcode_hmlr_lineage_contract_wave141.html"
STATUS = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave141_status_latest.json"
EVIDENCE = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave141_evidence_latest.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    task = json.loads(TASK_PATH.read_text())
    manifest = json.loads(MANIFEST_PATH.read_text())
    if task["schema_version"] != 3 or task["state"] not in {"READY", "RUNNING"}:
        raise RuntimeError("TASK_CONTRACT_INVALID")
    if task["script_path"] != str(Path(__file__).relative_to(ROOT)):
        raise RuntimeError("SCRIPT_PATH_MISMATCH")
    if task["source_script_path"] != task["script_path"]:
        raise RuntimeError("SOURCE_SCRIPT_PATH_MISMATCH")
    if task["official_source_evidence_manifest_path"] != str(MANIFEST_PATH.relative_to(ROOT)):
        raise RuntimeError("MANIFEST_PATH_MISMATCH")
    for relative in task["exact_read_paths"]:
        if not (ROOT / relative).exists():
            raise RuntimeError(f"MISSING_EXACT_READ_PATH:{relative}")
    if manifest["schema_version"] != 1 or manifest["fake_data"] is not False:
        raise RuntimeError("MANIFEST_INVALID")
    if len(manifest["official_sources"]) < 4:
        raise RuntimeError("OFFICIAL_SOURCE_SET_TOO_SMALL")

    wave140_status = json.loads(WAVE140_STATUS.read_text())
    wave140_evidence = json.loads(WAVE140_EVIDENCE.read_text())
    wave140_output = json.loads(WAVE140_OUTPUT.read_text())
    manual = json.loads(MANUAL.read_text())
    if wave140_status.get("continuation_key") != task["previous_continuation_key"]:
        raise RuntimeError("PREVIOUS_CONTINUATION_MISMATCH")
    if wave140_evidence.get("output_json_sha256") != sha256_path(WAVE140_OUTPUT):
        raise RuntimeError("WAVE140_OUTPUT_HASH_MISMATCH")

    # This runner is lineage-only: it must not redownload or rescan completed Wave140 datasets.
    # The executor must bind an existing Wave140 HMLR covering polygon identifier and/or OS Open UPRN
    # to an exact non-derived parent source record, then verify the official postcode/LSOA lineage.
    result = {
        "schema_version": 1,
        "slot_id": "security_public_safety_2",
        "task_id": task["task_id"],
        "continuation_key": task["continuation_key"],
        "generated_at": now(),
        "state": "READY_FOR_LINEAGE_ONLY_EXECUTION",
        "completed_wave_repeated": False,
        "wave140_hmlr_covering_polygon_rows": wave140_status["progress"].get("hmlr_covering_polygon_rows", 0),
        "wave140_exact_primary_binding_rows": wave140_status["progress"].get("exact_primary_binding_rows", 0),
        "wave140_eligible_exact_primary_binding_rows": wave140_status["progress"].get("eligible_exact_primary_binding_rows", 0),
        "required_lineage_gates": task["acceptance_conditions"],
        "official_source_manifest_sha256": sha256_path(MANIFEST_PATH),
        "manual_open_rows": manual.get("open_item_count"),
        "fake_data": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    WEBSITE.write_text("<!doctype html><meta charset='utf-8'><h1>Wave141 lineage contract</h1><pre>" + json.dumps(result, ensure_ascii=False, indent=2) + "</pre>\n")
    evidence = {
        "schema_version": 1,
        "slot_id": "security_public_safety_2",
        "task_id": task["task_id"],
        "continuation_key": task["continuation_key"],
        "state": "READY_CONTRACT_VALIDATED",
        "output_json": str(OUTPUT.relative_to(ROOT)),
        "output_html": str(WEBSITE.relative_to(ROOT)),
        "output_json_sha256": sha256_path(OUTPUT),
        "output_html_sha256": sha256_path(WEBSITE),
        "fake_data": False,
    }
    status = {
        "schema_version": 1,
        "slot_id": "security_public_safety_2",
        "task_id": task["task_id"],
        "continuation_key": task["continuation_key"],
        "state": "READY",
        "owner": None,
        "blocker": None,
        "first_unverified_step": task["first_unverified_step"],
        "updated_at": now(),
        "fake_data": False,
    }
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
