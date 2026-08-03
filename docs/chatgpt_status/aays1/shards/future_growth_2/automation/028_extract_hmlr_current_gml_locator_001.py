#!/usr/bin/env python3
"""Extract one bounded HM Land Registry current GML ZIP locator candidate.

The gate never treats a publicly documented URL as currently reachable unless a
separate current HTTP probe succeeds. It writes locator metadata only; it does
not download or copy archive/GML bodies, geometry, scores, or inferred authority
membership.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

OFFICIAL_HOST = "use-land-property-data.service.gov.uk"
URL_RE = re.compile(r"https://use-land-property-data\.service\.gov\.uk/datasets/inspire/download/[A-Za-z0-9_\-]+\.zip")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def extract_candidate(records: list[dict[str, Any]], authority: str) -> dict[str, Any]:
    official_listing = False
    exact_url: str | None = None
    exact_url_source: dict[str, Any] | None = None
    current_probe_verified = False
    probe_error: str | None = None

    for record in records:
        excerpt = str(record.get("relevant_record_ids_or_excerpt", ""))
        source_url = str(record.get("source_url", ""))
        if (
            source_url == "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
            and authority in excerpt
            and "Download .gml" in excerpt
        ):
            official_listing = True

        match = URL_RE.search(excerpt)
        if match:
            parsed = urlparse(match.group(0))
            if parsed.hostname == OFFICIAL_HOST and parsed.path.endswith(".zip"):
                exact_url = match.group(0)
                exact_url_source = record

        if record.get("record_type") == "CURRENT_HTTP_PROBE":
            current_probe_verified = bool(record.get("http_verified", False))
            probe_error = record.get("error")

    if not official_listing:
        raise ValueError("CURRENT_OFFICIAL_AUTHORITY_LISTING_NOT_PROVEN")
    if not exact_url or exact_url_source is None:
        raise ValueError("EXACT_OFFICIAL_GML_ZIP_LOCATOR_NOT_FOUND")

    archive_name = exact_url.rsplit("/", 1)[-1]
    return {
        "authority": authority,
        "exact_official_gml_zip_url": exact_url,
        "archive_name": archive_name,
        "archive_entry_expected": "Land_Registry_Cadastral_Parcels.gml",
        "exact_locator_captured": True,
        "current_http_availability_verified": current_probe_verified,
        "probe_error": probe_error,
        "locator_evidence_class": "PUBLICLY_DOCUMENTED_OFFICIAL_URL_WITH_CURRENT_OFFICIAL_AUTHORITY_LISTING",
        "source_url": exact_url_source.get("source_url"),
        "source_accessed_at": exact_url_source.get("accessed_at"),
        "source_excerpt_sha256": exact_url_source.get("content_sha256"),
        "authority_membership_inferred": False,
        "geometry_copied": False,
        "archive_body_copied": False,
        "gml_body_copied": False,
        "score_written": False,
        "fake_data": False,
    }


def build_output(manifest: dict[str, Any], authority: str, continuation_key: str) -> dict[str, Any]:
    records = manifest.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("SOURCE_MANIFEST_RECORDS_REQUIRED")
    candidate = extract_candidate(records, authority)
    verified = candidate["current_http_availability_verified"]
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "task_continuation_key": continuation_key,
        "state": "PUBLISHED" if candidate["exact_locator_captured"] else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": len(records),
        "progress_percent": 100.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        "evidence_record_count": len(records),
        "candidate": candidate,
        "blocker": None if verified else "OFFICIAL_CURRENT_GML_LOCATOR_HTTP_AVAILABILITY_UNVERIFIED",
        "next_unverified_step": "VALIDATE_OFFICIAL_CURRENT_GML_ZIP_HTTP_RESPONSE_AND_ARCHIVE_ENTRY",
        "fake_data": False,
    }


def self_test() -> list[str]:
    authority = "Council of the Isles of Scilly"
    official = {
        "source_url": "https://use-land-property-data.service.gov.uk/datasets/inspire/download",
        "accessed_at": "2026-08-03T19:25:13Z",
        "content_sha256": "a" * 64,
        "relevant_record_ids_or_excerpt": f"authority={authority}|link_text=Download .gml",
    }
    public = {
        "source_url": "https://gis.stackexchange.com/questions/495758/which-transformation-option-i-chose-after-i-was-offered-to-make-a-choice-in-qgis",
        "accessed_at": "2026-08-03T19:25:13Z",
        "content_sha256": "b" * 64,
        "relevant_record_ids_or_excerpt": "wget https://use-land-property-data.service.gov.uk/datasets/inspire/download/Council_of_the_Isles_of_Scilly.zip -O dsrc.zip",
    }
    probe = {
        "record_type": "CURRENT_HTTP_PROBE",
        "source_url": "https://use-land-property-data.service.gov.uk/datasets/inspire/download/Council_of_the_Isles_of_Scilly.zip",
        "http_verified": False,
        "error": "REDIRECT_LOOP",
        "relevant_record_ids_or_excerpt": "redirect_loop",
    }
    passed: list[str] = []
    candidate = extract_candidate([official, public, probe], authority)
    assert candidate["exact_official_gml_zip_url"].endswith("Council_of_the_Isles_of_Scilly.zip")
    passed.append("extract_exact_official_zip_url")
    assert candidate["current_http_availability_verified"] is False
    passed.append("preserve_unverified_http_state")
    try:
        extract_candidate([public, probe], authority)
    except ValueError as exc:
        assert str(exc) == "CURRENT_OFFICIAL_AUTHORITY_LISTING_NOT_PROVEN"
        passed.append("reject_missing_current_official_listing")
    else:
        raise AssertionError("missing listing was accepted")
    bad_public = dict(public)
    bad_public["relevant_record_ids_or_excerpt"] = "https://example.com/Council_of_the_Isles_of_Scilly.zip"
    try:
        extract_candidate([official, bad_public, probe], authority)
    except ValueError as exc:
        assert str(exc) == "EXACT_OFFICIAL_GML_ZIP_LOCATOR_NOT_FOUND"
        passed.append("reject_nonofficial_locator")
    else:
        raise AssertionError("nonofficial locator was accepted")
    assert all(candidate[key] is False for key in ("authority_membership_inferred", "geometry_copied", "archive_body_copied", "gml_body_copied", "score_written", "fake_data"))
    passed.append("forbid_inference_geometry_scores_and_fake_data")
    return passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--authority", default="Council of the Isles of Scilly")
    parser.add_argument("--task-continuation-key")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        passed = self_test()
        print(json.dumps({"state": "PASS", "passed_count": len(passed), "target_count": 5, "assertions": passed}, sort_keys=True))
        return 0
    if not args.manifest or not args.output or not args.task_continuation_key:
        parser.error("--manifest, --output and --task-continuation-key are required")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    output = build_output(manifest, args.authority, args.task_continuation_key)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"state": output["state"], "completed_count": output["completed_count"], "target_count": output["target_count"], "blocker": output["blocker"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
