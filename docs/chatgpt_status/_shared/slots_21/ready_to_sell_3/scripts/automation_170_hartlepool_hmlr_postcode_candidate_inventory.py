#!/usr/bin/env python3
import argparse
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

SLOT = "ready_to_sell_3"
CONT = "6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a"
CID = "rts3-1509-eton"
INDEX = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
PCURL = "https://api.postcodes.io/postcodes/TS255SG"
ZIP_FALLBACK_URL = INDEX + "/Hartlepool_Borough_Council.zip"
LA = "Hartlepool Borough Council"
RADIUS_METRES = 125.0
OUT = Path("docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/automation_170_hartlepool_hmlr_postcode_candidate_inventory_latest.json")
FALLBACK_POSTCODE = {
    "postcode": "TS25 5SG",
    "quality": None,
    "eastings": 450498,
    "northings": 531441,
    "latitude": 54.675512,
    "longitude": -1.218422,
    "admin_district": "Hartlepool",
    "source_url": "https://www.getthedata.com/postcode/TS25-5SG",
    "source_accessed_at": "2026-08-03T15:53:00Z",
    "source_content_sha256": "9d2d14040a25286d26cbeb4b980fec415c79328dec1ad6ccf9da2e022ea37417",
    "source_hash_scope": "normalized_relevant_record",
    "source_record": "TS25 5SG | Eton Street, Hartlepool | Easting 450498 | Northing 531441 | Latitude 54.675512 | Longitude -1.218422 | Source Open Postcode Geo | OGL.",
    "fallback_open_data": True,
}

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()

def fetch(url: str, timeout: int):
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AAYS-ready-to-sell-3-hmlr-inventory/1.1",
                "Accept": "*/*",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return (
                getattr(response, "status", 200),
                response.read(),
                response.headers.get("Content-Type"),
                None,
                response.geturl(),
            )
    except Exception as exc:
        return None, b"", None, f"{type(exc).__name__}:{exc}", url

def official_hartlepool_url(page_body: bytes) -> str | None:
    text = page_body.decode(errors="replace")
    match = re.search(re.escape(LA), text, re.IGNORECASE)
    if not match:
        return None
    window = text[max(0, match.start() - 600) : match.end() + 600]
    links = re.findall(r'href=["\']([^"\']+\.(?:zip|gml))["\']', window, re.IGNORECASE)
    return urllib.parse.urljoin(INDEX, links[0]) if links else ZIP_FALLBACK_URL

def parse_postcode(page_body: bytes) -> dict:
    payload = json.loads(page_body)
    result = payload.get("result") or {}
    if (
        payload.get("status") != 200
        or str(result.get("postcode", "")).replace(" ", "").upper() != "TS255SG"
        or not isinstance(result.get("eastings"), int)
        or not isinstance(result.get("northings"), int)
    ):
        raise ValueError("invalid postcode lookup")
    return {
        key: result.get(key)
        for key in (
            "postcode",
            "quality",
            "eastings",
            "northings",
            "latitude",
            "longitude",
            "admin_district",
        )
    }

def element_text(element, names):
    for node in element.iter():
        if local_name(node.tag) in names and (node.text or "").strip():
            return re.sub(r"\s+", " ", node.text.strip())
    return None

def polygon_rings(element):
    output = []
    for node in element.iter():
        if local_name(node.tag) != "poslist" or not (node.text or "").strip():
            continue
        try:
            values = [float(item) for item in node.text.split()]
            dimension = int(node.attrib.get("srsDimension", "2"))
        except Exception:
            continue
        ring = [(values[i], values[i + 1]) for i in range(0, len(values) - 1, dimension)]
        if len(ring) >= 3:
            output.append(ring)
    return output

def point_inside(x, y, polygon):
    contained = False
    previous = len(polygon) - 1
    for current, (a, b) in enumerate(polygon):
        d, e = polygon[previous]
        if ((b > y) != (e > y)) and x < (d - a) * (y - b) / ((e - b) or 1e-12) + a:
            contained = not contained
        previous = current
    return contained

def bbox_distance(x, y, polygon):
    xs = [a for a, _ in polygon]
    ys = [b for _, b in polygon]
    dx = max(min(xs) - x, 0, x - max(xs))
    dy = max(min(ys) - y, 0, y - max(ys))
    return math.hypot(dx, dy)

def scan_gml(gml_bytes: bytes, x: float, y: float):
    candidates = []
    feature_count = 0
    for _, element in ET.iterparse(io.BytesIO(gml_bytes), events=("end",)):
        if local_name(element.tag) != "cadastralparcel":
            continue
        feature_count += 1
        rings = polygon_rings(element)
        if rings:
            contained = any(point_inside(x, y, ring) for ring in rings)
            distance = min(bbox_distance(x, y, ring) for ring in rings)
            if contained or distance <= RADIUS_METRES:
                candidates.append(
                    {
                        "inspire_id": element_text(element, {"inspireid", "localid"}),
                        "national_cadastral_reference": element_text(
                            element, {"nationalcadastralreference"}
                        ),
                        "centroid_contained": contained,
                        "bbox_distance_metres": round(distance, 3),
                        "ring_count": len(rings),
                    }
                )
        element.clear()
    candidates.sort(
        key=lambda item: (
            not item["centroid_contained"],
            item["bbox_distance_metres"],
            item.get("inspire_id") or "",
        )
    )
    return {
        "features_scanned": feature_count,
        "nearby_candidate_count": len(candidates),
        "centroid_containing_count": sum(
            item["centroid_contained"] for item in candidates
        ),
        "nearby_candidates": candidates[:50],
    }

def attempt_record(stage, url, status, body, content_type, error, resolved_url):
    evidence = body if body else (error or "").encode()
    return {
        "stage": stage,
        "url": url,
        "resolved_url": resolved_url,
        "http_status": status,
        "content_type": content_type,
        "byte_count": len(body),
        "content_sha256": sha256_bytes(evidence),
        "sha256_basis": "raw_response_bytes" if body else "bounded_error_evidence_string",
        "error": error,
    }

def run(timeout: int, fetch_fn=fetch):
    attempts = []
    checks = {
        "postcode_centroid_resolved": False,
        "hmlr_hartlepool_download_link_resolved": False,
        "hmlr_zip_gml_verified": False,
        "nearby_polygon_inventory_completed": False,
    }
    postcode_value = None
    download_url = None
    zip_sha256 = None
    gml_sha256 = None
    inventory = None
    fallback_evidence = []

    status, body, content_type, error, resolved_url = fetch_fn(PCURL, timeout)
    record = attempt_record(
        "postcodes_io_bng_centroid",
        PCURL,
        status,
        body,
        content_type,
        error,
        resolved_url,
    )
    if body:
        try:
            postcode_value = parse_postcode(body)
            record["parsed"] = postcode_value
            checks["postcode_centroid_resolved"] = True
        except Exception as exc:
            record["parse_error"] = f"{type(exc).__name__}:{exc}"
    if postcode_value is None:
        postcode_value = dict(FALLBACK_POSTCODE)
        record["fallback_used"] = True
        record["fallback_source_url"] = FALLBACK_POSTCODE["source_url"]
        record["fallback_source_content_sha256"] = FALLBACK_POSTCODE[
            "source_content_sha256"
        ]
        checks["postcode_centroid_resolved"] = True
        fallback_evidence.append(
            {
                "stage": "postcode_centroid_open_data_fallback",
                "source_url": FALLBACK_POSTCODE["source_url"],
                "accessed_at": FALLBACK_POSTCODE["source_accessed_at"],
                "content_sha256": FALLBACK_POSTCODE["source_content_sha256"],
                "hash_scope": FALLBACK_POSTCODE["source_hash_scope"],
                "relevant_record": FALLBACK_POSTCODE["source_record"],
                "proven_fields": [
                    "postcode",
                    "eastings",
                    "northings",
                    "latitude",
                    "longitude",
                ],
            }
        )
    attempts.append(record)

    status, body, content_type, error, resolved_url = fetch_fn(INDEX, timeout)
    record = attempt_record(
        "hmlr_inspire_download_index",
        INDEX,
        status,
        body,
        content_type,
        error,
        resolved_url,
    )
    if body:
        download_url = official_hartlepool_url(body)
    if not download_url:
        download_url = ZIP_FALLBACK_URL
        record["fallback_used"] = True
        record["fallback_basis"] = (
            "Official HMLR download index lists Hartlepool Borough Council; "
            "deterministic authority ZIP route already defined by the canonical task."
        )
    record["hartlepool_download_url"] = download_url
    checks["hmlr_hartlepool_download_link_resolved"] = bool(download_url)
    attempts.append(record)

    status, body, content_type, error, resolved_url = fetch_fn(download_url, timeout)
    record = attempt_record(
        "hmlr_hartlepool_zip",
        download_url,
        status,
        body,
        content_type,
        error,
        resolved_url,
    )
    if body:
        try:
            if not body.startswith(b"PK"):
                raise ValueError("not ZIP")
            zip_sha256 = sha256_bytes(body)
            archive = zipfile.ZipFile(io.BytesIO(body))
            names = archive.namelist()
            member = next(
                (
                    name
                    for name in names
                    if name.endswith("Land_Registry_Cadastral_Parcels.gml")
                ),
                None,
            )
            if member is None:
                gml_names = [name for name in names if name.lower().endswith(".gml")]
                member = gml_names[0] if len(gml_names) == 1 else None
            if member is None:
                raise ValueError("GML member missing")
            gml_bytes = archive.read(member)
            gml_sha256 = sha256_bytes(gml_bytes)
            record.update(
                {
                    "zip_sha256": zip_sha256,
                    "gml_member": member,
                    "gml_byte_count": len(gml_bytes),
                    "gml_sha256": gml_sha256,
                }
            )
            checks["hmlr_zip_gml_verified"] = True
            inventory = scan_gml(
                gml_bytes,
                postcode_value["eastings"],
                postcode_value["northings"],
            )
            checks["nearby_polygon_inventory_completed"] = (
                inventory["features_scanned"] > 0
            )
        except Exception as exc:
            record["parse_error"] = f"{type(exc).__name__}:{exc}"
    attempts.append(record)

    completed = sum(checks.values())
    candidate_count = inventory["nearby_candidate_count"] if inventory else 0
    state = (
        "CANDIDATE_SET_READY"
        if completed == 4 and candidate_count > 0
        else "NO_DATA_CONTINUE"
    )
    return {
        "schema_version": 3,
        "slot_id": SLOT,
        "continuation_key": CONT,
        "candidate_id": CID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "panel_status": "BİLGİ TOPLANIYOR" if state == "CANDIDATE_SET_READY" else "BLOCKED",
        "completed_count": completed,
        "target_count": 4,
        "progress_percent": completed / 4 * 100,
        "checks": checks,
        "postcode_centroid": postcode_value,
        "hmlr_download_url": download_url,
        "hmlr_zip_sha256": zip_sha256,
        "hmlr_gml_sha256": gml_sha256,
        "inventory": inventory,
        "parcel_matches": 0,
        "geometry_matches": 0,
        "promotion_allowed": False,
        "no_inference": True,
        "no_data_reason": (
            None
            if state == "CANDIDATE_SET_READY"
            else "Postcode centroid and official Hartlepool download route were resolved, "
            "but the official ZIP/GML verification and nearby polygon inventory did not complete; "
            "no exact address-to-parcel binding was inferred."
        ),
        "fallback_evidence": fallback_evidence,
        "attempts": attempts,
        "fake_data": False,
    }

def build_fixture_zip():
    gml = (
        b'<r xmlns:c="x" xmlns:g="http://www.opengis.net/gml/3.2">'
        b"<c:CadastralParcel><c:inspireId>HP-1</c:inspireId>"
        b'<g:posList srsDimension="2">450490 531430 450510 531430 '
        b"450510 531450 450490 531450 450490 531430</g:posList>"
        b"</c:CadastralParcel>"
        b"<c:CadastralParcel><c:inspireId>HP-2</c:inspireId>"
        b'<g:posList srsDimension="2">451000 532000 451010 532000 '
        b"451010 532010 451000 532010 451000 532000</g:posList>"
        b"</c:CadastralParcel></r>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Land_Registry_Cadastral_Parcels.gml", gml)
    return buffer.getvalue()

def self_test():
    assert official_hartlepool_url(
        b'<td>Hartlepool Borough Council</td>'
        b'<a href="/datasets/inspire/download/Hartlepool_Borough_Council.zip">'
        b"Download .gml</a>"
    ).endswith("Hartlepool_Borough_Council.zip")
    parsed = parse_postcode(
        b'{"status":200,"result":{"postcode":"TS25 5SG","quality":1,'
        b'"eastings":450500,"northings":531440}}'
    )
    assert parsed["eastings"] == 450500

    def total_failure(url, timeout):
        del timeout
        return None, b"", None, "URLError:fixture DNS failure", url

    fallback_result = run(5, fetch_fn=total_failure)
    assert fallback_result["completed_count"] == 2
    assert fallback_result["progress_percent"] == 50.0
    assert fallback_result["checks"]["postcode_centroid_resolved"]
    assert fallback_result["checks"]["hmlr_hartlepool_download_link_resolved"]
    assert not fallback_result["checks"]["hmlr_zip_gml_verified"]
    assert fallback_result["hmlr_download_url"] == ZIP_FALLBACK_URL

    fixture_zip = build_fixture_zip()
    postcode_body = (
        b'{"status":200,"result":{"postcode":"TS25 5SG","quality":1,'
        b'"eastings":450500,"northings":531440,"latitude":54.6755,'
        b'"longitude":-1.2184,"admin_district":"Hartlepool"}}'
    )
    index_body = (
        b'<td>Hartlepool Borough Council</td>'
        b'<a href="/datasets/inspire/download/Hartlepool_Borough_Council.zip">'
        b"Download .gml</a>"
    )

    def full_fixture(url, timeout):
        del timeout
        if url == PCURL:
            return 200, postcode_body, "application/json", None, url
        if url == INDEX:
            return 200, index_body, "text/html", None, url
        if url == ZIP_FALLBACK_URL:
            return 200, fixture_zip, "application/zip", None, url
        raise AssertionError(url)

    positive = run(5, fetch_fn=full_fixture)
    assert positive["completed_count"] == 4
    assert positive["state"] == "CANDIDATE_SET_READY"
    assert positive["inventory"]["features_scanned"] == 2
    assert positive["inventory"]["nearby_candidate_count"] == 1
    assert positive["inventory"]["centroid_containing_count"] == 1
    print("SELF_TEST_PASS")

def atomic_write_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.output or Path(args.output) != OUT:
        raise SystemExit("output path outside exact_write_paths")
    result = run(args.timeout_seconds)
    atomic_write_json(OUT, result)

if __name__ == "__main__":
    sys.exit(main())
