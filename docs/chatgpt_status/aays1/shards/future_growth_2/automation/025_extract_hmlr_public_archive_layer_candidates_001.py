#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime, timezone

SLOT_ID = "future_growth_2"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
LAYER_RE = re.compile(r"(?:^|[|?&])LAYERS=([^|&\s]+)", re.IGNORECASE)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def load_manifest(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version","slot_id","record_count","records"}
    missing = required.difference(value)
    if missing:
        raise ValueError(f"manifest missing fields: {sorted(missing)}")
    if value["slot_id"] != SLOT_ID:
        raise ValueError("slot mismatch")
    if value["record_count"] != len(value["records"]):
        raise ValueError("record_count mismatch")
    for index, record in enumerate(value["records"]):
        for field in ("source_url","accessed_at","content_sha256","hash_scope",
                      "relevant_record_ids_or_excerpt","supports_fields","source_class"):
            if not record.get(field):
                raise ValueError(f"record {index} missing {field}")
        actual = sha256_bytes(record["relevant_record_ids_or_excerpt"].encode("utf-8"))
        if actual != record["content_sha256"]:
            raise ValueError(f"record {index} excerpt SHA mismatch")
    return value

def extract_candidates(manifest: dict) -> list[dict]:
    candidates = {}
    for record in manifest["records"]:
        if record["source_class"] != "historical_public_client_request":
            continue
        excerpt = record["relevant_record_ids_or_excerpt"]
        for match in LAYER_RE.finditer(excerpt):
            token = unquote(match.group(1)).strip()
            if not token or any(ch.isspace() for ch in token):
                continue
            candidates.setdefault(token, {
                "layer_token": token,
                "evidence_class": "HISTORICAL_EXACT_PUBLIC_CLIENT_REQUEST",
                "source_url": record["source_url"],
                "source_accessed_at": record["accessed_at"],
                "source_excerpt_sha256": record["content_sha256"],
                "source_scope": record["hash_scope"],
                "published_or_observed_at": record.get("published_or_observed_at"),
                "current_capabilities_verified": False,
                "current_layer_availability_verified": False,
                "authority_membership_inferred": False,
                "geometry_copied": False,
                "score_written": False,
                "fake_data": False,
            })
    return [candidates[key] for key in sorted(candidates)]

def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle:
            json.dump(value,handle,ensure_ascii=False,sort_keys=True,separators=(",",":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path,path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--task-continuation-key",required=True)
    parser.add_argument("--self-test",action="store_true")
    args = parser.parse_args()
    if len(args.task_continuation_key) != 64 or any(c not in "0123456789abcdef" for c in args.task_continuation_key):
        raise ValueError("continuation key must be lowercase SHA-256 hex")
    if args.self_test:
        fixture_excerpt = "lines=1-2|REQUEST=GetMap|LAYERS=fixture:CP.CadastralParcel|CRS=EPSG:27700"
        fixture = {"schema_version":3,"slot_id":SLOT_ID,"record_count":1,"records":[{
            "source_url":"https://example.invalid/archive","accessed_at":"2026-01-01T00:00:00Z",
            "content_sha256":sha256_bytes(fixture_excerpt.encode()),"hash_scope":"fixture",
            "relevant_record_ids_or_excerpt":fixture_excerpt,"supports_fields":["exact_historical_layer_token"],
            "source_class":"historical_public_client_request"}]}
        candidates = extract_candidates(fixture)
        assert len(candidates) == 1
        assert candidates[0]["layer_token"] == "fixture:CP.CadastralParcel"
        assert candidates[0]["current_capabilities_verified"] is False
        assert candidates[0]["authority_membership_inferred"] is False
        print('{"self_test":"PASS_4_OF_4"}')
        return
    manifest = load_manifest(Path(args.manifest))
    candidates = extract_candidates(manifest)
    state = "PUBLISHED" if candidates else "NO_DATA_CONTINUE"
    output = {
        "schema_version":3,
        "architecture_version":3,
        "workstream_id":WORKSTREAM_ID,
        "slot_id":SLOT_ID,
        "task_continuation_key":args.task_continuation_key,
        "generated_at":utc_now(),
        "state":state,
        "panel_status":"PUBLISHED",
        "completed_count":manifest["record_count"],
        "target_count":manifest["record_count"],
        "progress_percent":100.0,
        "global_business_completed_count":0,
        "global_business_target_count":30761,
        "global_progress_percent":0.0,
        "evidence_record_count":manifest["record_count"],
        "candidate_count":len(candidates),
        "candidates":candidates,
        "current_capabilities_verified":False,
        "current_layer_availability_verified":False,
        "authority_membership_inferred":False,
        "geometry_copied":False,
        "score_written":False,
        "fake_data":False,
        "next_unverified_step":"VALIDATE_HISTORICAL_LAYER_TOKEN_AGAINST_OFFICIAL_CURRENT_ENDPOINT_OR_OFFICIAL_PROXY",
    }
    atomic_write(Path(args.output),output)
    print(json.dumps({"state":state,"completed_count":output["completed_count"],
                      "target_count":output["target_count"],"candidate_count":len(candidates),
                      "output":args.output},sort_keys=True,separators=(",",":")))

if __name__ == "__main__":
    main()
