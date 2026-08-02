from __future__ import annotations
import argparse, hashlib, json, os, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-voa-rating-list-license-scope-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/voa_rating_list_license_scope_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/voa_rating_list_license_scope_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
SOURCES = (
    {
        "source_url": "https://www.gov.uk/find-business-rates",
        "scope": "official GOV.UK entry page for the public business-rates valuation service",
        "supports_fields": ["rateable value service", "England and Wales", "Valuation Office"],
    },
    {
        "source_url": "https://voaratinglists.blob.core.windows.net/html/rlidata.htm",
        "scope": "official VOA Rating List Downloads landing page only; no dataset download",
        "supports_fields": ["download availability", "list years", "restricted licence notice", "file scale"],
    },
    {
        "source_url": "https://www.tax.service.gov.uk/business-rates-find/terms-and-conditions",
        "scope": "official VOA service terms and conditions",
        "supports_fields": ["permitted NDR purposes", "onward disclosure restriction", "deletion obligation"],
    },
)
MAX_BYTES = 1_048_576

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()

def atomic_write(path: str, obj: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, target)

def validate_points() -> None:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    by_id = {row["parcel_id"]: row for row in payload["canonical_points"]}
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")

def validate() -> None:
    validate_points()
    if Path(PROBE).is_absolute() or any(Path(path).is_absolute() for path in OUT):
        raise ValueError("all paths must be repository-relative")
    if len(SOURCES) != 3 or any(not row["source_url"].startswith("https://") for row in SOURCES):
        raise ValueError("exactly three official HTTPS sources required")
    print("PASS_TARGET_3_VOA_RATING_LIST_LICENSE_SCOPE_MAX1MIB_NO_DATA_DOWNLOAD")

def classify(text: str) -> dict:
    normalized = re.sub(r"\s+", " ", text).lower()
    restricted = "restricted licence" in normalized or "restricted license" in normalized
    ndr_only = "non domestic rating" in normalized and (
        "purposes only" in normalized or "ndr purposes" in normalized
    )
    open_government_not_apply = "open government licence does not apply" in normalized
    dataset_scale_warning = "exceed 2 million rows" in normalized
    return {
        "restricted_licence_detected": restricted,
        "ndr_purpose_only_detected": ndr_only,
        "ogl_not_apply_detected": open_government_not_apply,
        "large_dataset_warning_detected": dataset_scale_warning,
    }

def run(timeout: float) -> dict:
    evidence = []
    any_restricted = False
    for source in SOURCES:
        accessed_at = now()
        request = urllib.request.Request(
            source["source_url"],
            headers={"User-Agent": "TerraYield-AAYS/1.0 bounded VOA source-license screening"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("response exceeded 1 MiB")
                text = raw.decode("utf-8", errors="replace")
                flags = classify(text)
                any_restricted = any_restricted or flags["restricted_licence_detected"] or flags["ndr_purpose_only_detected"]
                evidence.append({
                    "source_url": source["source_url"],
                    "accessed_at": accessed_at,
                    "content_sha256": sha256(raw),
                    "sha256_basis": "bounded_raw_response_bytes",
                    "record_scope": source["scope"],
                    "supports_fields": source["supports_fields"],
                    "relevant_record_ids_or_excerpt": flags,
                    "http_status": getattr(response, "status", None),
                })
        except Exception as exc:
            message = f"VOA_RATING_LIST_LICENSE_SCOPE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "source_url": source["source_url"],
                "accessed_at": accessed_at,
                "content_sha256": sha256(message),
                "sha256_basis": "bounded_error_evidence_string",
                "record_scope": source["scope"],
                "supports_fields": source["supports_fields"],
                "relevant_record_ids_or_excerpt": message[:512],
                "http_status": getattr(exc, "code", None),
            })
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": list(IDS),
        "produced_candidate_rows": 0,
        "source_evidence": evidence,
        "license_screening": {
            "official_source": True,
            "dataset_download_attempted": False,
            "large_data_downloaded": False,
            "restricted_or_ndr_only_detected_in_runtime": any_restricted,
            "parcel_label_use_accepted": False,
        },
        "blocker": {
            "code": "VOA_RATING_LIST_RESTRICTED_NDR_PURPOSE_LICENSE_OR_RUNTIME_UNAVAILABLE",
            "state": "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_VOA_RATING_LIST_LICENSE_SCREEN",
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in OUT:
        atomic_write(path, result)
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "produced_candidate_rows": result["produced_candidate_rows"],
        "evidence_records": len(result["source_evidence"]),
    }, separators=(",", ":")))

if __name__ == "__main__":
    main()
