#!/usr/bin/env python3
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
INPUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/016_revision_14_direct_hmlr_monthly_gml_refresh_latest.json"
OUTPUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/026_revision14_inspireid_provenance_guard_latest.json"
EXPECTED = {"parcel_2759", "parcel_2758", "parcel_2757"}
PROV_KEYS = ("identity_source_field", "inspire_id_source_field", "source_field_name", "xml_path", "identity_xml_path")
AMBIGUOUS_KEYS = ("national_cadastral_reference", "nationalCadastralReference", "label", "LABEL", "gml_id", "gml:id")

def nonempty(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())

def walk(v: Any):
    if isinstance(v, dict):
        yield v
        for child in v.values():
            yield from walk(child)
    elif isinstance(v, list):
        for child in v:
            yield from walk(child)

def provenance_text(d: dict[str, Any]) -> str:
    vals = [str(d[k]) for k in PROV_KEYS if d.get(k) is not None]
    p = d.get("inspire_id_provenance")
    if isinstance(p, dict):
        vals.extend(str(x) for x in p.values() if x is not None)
    return " ".join(vals).lower().replace("_", "")

def identity_from_dict(d: dict[str, Any]) -> tuple[str | None, str | None]:
    for key in ("INSPIREID", "inspireId"):
        value = d.get(key)
        if nonempty(value):
            return value.strip(), key
        if isinstance(value, dict):
            child = value.get("Identifier") if isinstance(value.get("Identifier"), dict) else value
            local_id = child.get("localId") or child.get("local_id")
            if nonempty(local_id):
                return local_id.strip(), f"{key}.Identifier.localId" if child is not value else f"{key}.localId"
    value = d.get("inspire_id")
    if nonempty(value):
        prov = provenance_text(d)
        if "inspireid" in prov and ("localid" in prov or "sourcefield" not in prov):
            return value.strip(), "inspire_id+provenance"
    return None, None

def candidate_record(root: Any, pid: str) -> dict[str, Any] | None:
    for d in walk(root):
        if d.get("parcel_id") == pid:
            return d
    return None

def validate_payload(payload: Any) -> dict[str, Any]:
    results: dict[str, Any] = {}
    all_ok = True
    for pid in sorted(EXPECTED):
        rec = candidate_record(payload, pid)
        if rec is None:
            results[pid] = {"ok": False, "reason": "CANDIDATE_RECORD_MISSING"}
            all_ok = False
            continue
        inspire_id, source = identity_from_dict(rec)
        if not inspire_id:
            results[pid] = {
                "ok": False,
                "reason": "EXPLICIT_INSPIREID_PROVENANCE_MISSING",
                "ambiguous_fields_present": [k for k in AMBIGUOUS_KEYS if nonempty(rec.get(k))],
                "standalone_local_id_present": nonempty(rec.get("local_id")) or nonempty(rec.get("localId")),
            }
            all_ok = False
            continue
        parcel_ref = str(rec.get("parcel_ref") or "").strip()
        if parcel_ref and inspire_id == parcel_ref:
            results[pid] = {"ok": False, "reason": "INSPIRE_ID_EQUALS_PARCEL_REF_ALIAS_COLLISION", "identity_source": source}
            all_ok = False
            continue
        results[pid] = {"ok": True, "inspire_id": inspire_id, "identity_source": source}
    return {"ok": all_ok, "candidates": results}

def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        OUTPUT.write_text(json.dumps({
            "schema_version": 1,
            "slot_id": "height_difference_1",
            "status": "BLOCKED_REVISION14_OUTPUT_016_ABSENT",
            "input": str(INPUT.relative_to(REPO)),
            "final_ready": False,
            "fake_data": False,
        }, indent=2), encoding="utf-8")
        return 2
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    result = validate_payload(payload)
    OUTPUT.write_text(json.dumps({
        "schema_version": 1,
        "slot_id": "height_difference_1",
        "status": "PASS_EXPLICIT_INSPIREID_PROVENANCE" if result["ok"] else "BLOCKED_IDENTITY_PROVENANCE",
        "input": str(INPUT.relative_to(REPO)),
        **result,
        "final_ready": False,
        "fake_data": False,
    }, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 3

if __name__ == "__main__":
    raise SystemExit(main())
