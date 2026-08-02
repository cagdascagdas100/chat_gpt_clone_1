#!/usr/bin/env python3
"""Wave346: bounded Nominatim reverse-address and OSM identifier assessment."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
EXPECTED_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_rows(path: Path) -> list[dict[str, Any]]:
    obj=json.loads(path.read_text(encoding="utf-8"))
    rows=obj.get("rows") or []
    found={r.get("parcel_id"):r for r in rows}
    if any(x not in found for x in EXPECTED_IDS):
        raise ValueError("canonical sample missing required parcel ids")
    return [found[x] for x in EXPECTED_IDS]

def fetch_bounded(url: str, timeout: int, max_bytes: int) -> dict[str, Any]:
    req=Request(url, headers={
        "User-Agent":"AAYS-gas-emissions-evidence/1.0 (three bounded research requests)",
        "Accept":"application/json",
        "Accept-Language":"en"
    })
    raw=b""; status=None; final_url=None; ctype=None; err=None; truncated=False
    try:
        with urlopen(req, timeout=timeout) as resp:
            status=getattr(resp, "status", None); final_url=resp.geturl()
            ctype=resp.headers.get("Content-Type")
            raw=resp.read(max_bytes+1)
            if len(raw)>max_bytes:
                raw=raw[:max_bytes]; truncated=True
    except HTTPError as e:
        status=e.code; final_url=e.geturl(); ctype=e.headers.get("Content-Type") if e.headers else None
        raw=e.read(max_bytes+1)[:max_bytes]; err=f"HTTPError:{e.code}"
    except URLError as e:
        err=f"URLError:{e}"
    except Exception as e:
        err=f"{type(e).__name__}:{e}"
    parsed=None; parse_error=None
    if raw:
        try: parsed=json.loads(raw.decode("utf-8"))
        except Exception as e: parse_error=f"{type(e).__name__}:{e}"
    return {"source_url":url,"http_status":status,"final_url":final_url,"content_type":ctype,
            "bytes_read":len(raw),"content_sha256":sha256_bytes(raw),"truncated":truncated,
            "network_error":err,"parse_error":parse_error,"parsed":parsed}

def normalize_candidate(parsed: Any) -> dict[str, Any] | None:
    if not isinstance(parsed, dict) or "error" in parsed:
        return None
    osm_type=parsed.get("osm_type"); osm_id=parsed.get("osm_id")
    address=parsed.get("address") if isinstance(parsed.get("address"), dict) else {}
    return {
        "place_id":parsed.get("place_id"),
        "osm_type":osm_type,"osm_id":osm_id,
        "category":parsed.get("category"),"type":parsed.get("type"),
        "addresstype":parsed.get("addresstype"),"display_name":parsed.get("display_name"),
        "result_lat":parsed.get("lat"),"result_lon":parsed.get("lon"),
        "boundingbox":parsed.get("boundingbox"),
        "house_number":address.get("house_number"),"house_name":address.get("house_name"),
        "road":address.get("road"),"postcode":address.get("postcode"),
        "city":address.get("city") or address.get("town") or address.get("village"),
        "country_code":address.get("country_code"),
        "osm_reference_present":bool(osm_type and osm_id),
        "candidate_is_exact_property_identity":False,
        "candidate_is_exact_parcel_binding":False,
        "candidate_is_uprn":False
    }

def self_test() -> None:
    fake={"place_id":1,"osm_type":"way","osm_id":123,"category":"building","type":"yes",
          "display_name":"Example","lat":"51","lon":"-0.1",
          "address":{"house_number":"1","road":"Test Road","postcode":"N1","country_code":"gb"}}
    c=normalize_candidate(fake)
    assert c and c["osm_reference_present"] and not c["candidate_is_exact_parcel_binding"]
    assert c["house_number"]=="1" and c["postcode"]=="N1"
    print("SELF_TEST_PASS")

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--canonical"); ap.add_argument("--fixture"); ap.add_argument("--output")
    ap.add_argument("--timeout", type=int, default=30); ap.add_argument("--self-test", action="store_true")
    args=ap.parse_args()
    if args.self_test: self_test(); return 0
    if not (args.canonical and args.fixture and args.output):
        ap.error("--canonical --fixture --output required")
    fixture=json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    rows=load_rows(Path(args.canonical))
    max_each=int(fixture.get("max_bytes_per_request",500000))
    max_total=int(fixture.get("max_total_bytes",1500000))
    delay=float(fixture.get("request_delay_seconds",1.1))
    assessments=[]; total=0
    for idx,row in enumerate(rows):
        p=row["properties"]; lat=p["hmlr_lat"]; lon=p["hmlr_lon"]
        qs=urlencode({"format":"jsonv2","lat":lat,"lon":lon,"zoom":18,"addressdetails":1,"layer":"address"})
        url="https://nominatim.openstreetmap.org/reverse?"+qs
        probe=fetch_bounded(url,args.timeout,max_each); total+=probe["bytes_read"]
        candidate=normalize_candidate(probe.pop("parsed"))
        assessments.append({
          "parcel_id":row["parcel_id"],"row_no":p["row_no"],"hmlr_inspire_id":p["hmlr_inspire_id"],
          "longitude":lon,"latitude":lat,"london_authority":p.get("london_authority"),
          "nominatim_candidate":candidate,"probe":probe,
          "candidate_is_exact_property_identity":False,
          "candidate_is_exact_parcel_binding":False,"uprn_claimed":False
        })
        if idx+1<len(rows): time.sleep(delay)
    if total>max_total: raise RuntimeError("max_total_bytes exceeded")
    candidate_count=sum(1 for x in assessments if x["nominatim_candidate"])
    osm_ref_count=sum(1 for x in assessments if x["nominatim_candidate"] and x["nominatim_candidate"]["osm_reference_present"])
    network_error_count=sum(1 for x in assessments if x["probe"]["network_error"])
    blocker=("THREE_EXACT_OPEN_ADDRESS_BUILDING_IDENTIFIERS_NOT_ACQUIRED;"
             "NOMINATIM_CLOSEST_OSM_OBJECT_IS_NOT_EXACT_PROPERTY_ADDRESS_OR_UPRN;"
             "THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE")
    if network_error_count:
        blocker="NOMINATIM_REVERSE_REQUESTS_NOT_LIVE_ACQUIRED;"+blocker
    result={
      "schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
      "slot_id":"gas_emissions_2","wave":346,"accessed_at":utc_now(),"state":"NO_DATA_CONTINUE",
      "decision":"OPEN_OSM_ADDRESS_BUILDING_IDENTIFIER_GATE_ASSESSED_NO_EXACT_PROPERTY_BINDING",
      "canonical_sample_rows_in_scope":3,"assessment_count":len(assessments),
      "nominatim_candidate_count":candidate_count,"osm_reference_candidate_count":osm_ref_count,
      "network_error_count":network_error_count,"total_bytes_read":total,
      "business_rows_produced":0,"parcel_rows_bound":0,"address_claimed":False,"uprn_claimed":False,
      "candidate_semantics":fixture["candidate_semantics"],"assessments":assessments,
      "official_or_open_source_evidence_count":len(fixture["source_evidence_manifest"]),
      "source_evidence_manifest":fixture["source_evidence_manifest"],
      "runtime_source_evidence":[{
        "source_url":fixture["endpoint_template"],"accessed_at":utc_now(),
        "content_sha256":EMPTY_SHA256 if total==0 else sha256_bytes(
            "".join(x["probe"]["content_sha256"] for x in assessments).encode()),
        "hash_scope":"three_bounded_live_response_receipts",
        "record_scope":"Three delayed anonymous Nominatim reverse requests for exact canonical coordinates.",
        "relevant_record_ids_or_excerpt":"; ".join(
           f'{x["parcel_id"]}:{x["probe"]["network_error"] or x["probe"]["http_status"]}' for x in assessments),
        "supports_fields":["bounded_request_attempt","live_network_or_http_evidence",
                           "no_form_submission","no_personal_data_submission","no_exact_binding_claim"],
        "license_or_terms_url":"https://www.openstreetmap.org/copyright"
      }],
      "blocker":blocker,
      "first_unverified_step":"ASSESS_OPENSTREETMAP_OVERPASS_BUILDING_GEOMETRY_CANDIDATES_FOR_THREE_COORDINATES_OR_NO_DATA_CONTINUE",
      "completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,
      "fake_data":False,"final_ready":False
    }
    atomic_json(Path(args.output),result)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
