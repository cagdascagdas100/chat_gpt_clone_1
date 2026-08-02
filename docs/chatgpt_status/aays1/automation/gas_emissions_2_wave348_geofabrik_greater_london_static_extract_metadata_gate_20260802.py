#!/usr/bin/env python3
"""Wave348: bounded Geofabrik Greater London static-extract metadata gate."""
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile, time
from pathlib import Path
from urllib import request, error

MAX_PAGE=400_000
MAX_MD5=2_000
MAX_POLY=200_000
UA="AAYS-Wave348/1.0 metadata-only"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, sort_keys=True, separators=(",",":"))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def bounded_get(url: str, timeout: float, max_bytes: int) -> dict:
    req=request.Request(url, headers={"User-Agent":UA,"Accept":"*/*"}, method="GET")
    out={"source_url":url,"method":"GET","http_status":None,"final_url":None,
         "content_type":None,"content_length_header":None,"bytes_read":0,
         "content_sha256":sha256_bytes(b""),"truncated":False,"network_error":None}
    try:
        with request.urlopen(req, timeout=timeout) as r:
            data=r.read(max_bytes+1)
            out["http_status"]=getattr(r,"status",None)
            out["final_url"]=r.geturl()
            out["content_type"]=r.headers.get("Content-Type")
            out["content_length_header"]=r.headers.get("Content-Length")
            if len(data)>max_bytes:
                data=data[:max_bytes]; out["truncated"]=True
            out["bytes_read"]=len(data); out["content_sha256"]=sha256_bytes(data)
            out["_text"]=data.decode("utf-8","replace")
    except Exception as exc:
        out["network_error"]=f"{type(exc).__name__}:{exc}"
        out["_text"]=""
    return out

def bounded_head(url: str, timeout: float) -> dict:
    req=request.Request(url, headers={"User-Agent":UA,"Accept":"*/*"}, method="HEAD")
    out={"source_url":url,"method":"HEAD","http_status":None,"final_url":None,
         "content_type":None,"content_length_header":None,"bytes_read":0,
         "content_sha256":sha256_bytes(b""),"truncated":False,"network_error":None}
    try:
        with request.urlopen(req, timeout=timeout) as r:
            out["http_status"]=getattr(r,"status",None)
            out["final_url"]=r.geturl()
            out["content_type"]=r.headers.get("Content-Type")
            out["content_length_header"]=r.headers.get("Content-Length")
    except Exception as exc:
        out["network_error"]=f"{type(exc).__name__}:{exc}"
    return out

def canonical_rows(doc: dict) -> list[dict]:
    rows=[]
    for row in doc.get("rows",[]):
        p=row.get("properties") or {}
        rows.append({
            "parcel_id":row.get("parcel_id") or p.get("parcel_id"),
            "row_no":p.get("row_no"),"hmlr_inspire_id":p.get("hmlr_inspire_id"),
            "longitude":p.get("hmlr_lon"),"latitude":p.get("hmlr_lat"),
            "london_authority":p.get("london_authority"),
            "geometry_type":row.get("geometry_type")
        })
    return rows

def self_test() -> None:
    assert re.fullmatch(r"[0-9a-f]{64}", sha256_bytes(b"abc"))
    sample={"rows":[{"parcel_id":"parcel_30762","geometry_type":"Point",
                     "properties":{"row_no":30762,"hmlr_inspire_id":"46058185",
                     "hmlr_lon":-0.0407406,"hmlr_lat":51.6769078,
                     "london_authority":"Enfield"}}]}
    rows=canonical_rows(sample)
    assert rows[0]["parcel_id"]=="parcel_30762"
    assert rows[0]["london_authority"]=="Enfield"
    md5="0123456789abcdef0123456789abcdef  greater-london-latest.osm.pbf\n"
    assert re.search(r"\b[0-9a-fA-F]{32}\b", md5)
    print("SELF_TEST_PASS")

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--canonical")
    ap.add_argument("--fixture")
    ap.add_argument("--output")
    ap.add_argument("--timeout",type=float,default=30)
    ap.add_argument("--delay",type=float,default=1.0)
    ap.add_argument("--accessed-at",required=False)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not (args.canonical and args.fixture and args.output):
        ap.error("--canonical, --fixture and --output are required")
    canonical=json.loads(Path(args.canonical).read_text(encoding="utf-8"))
    fixture=json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    rows=canonical_rows(canonical)
    targets={"parcel_30762","parcel_30763","parcel_30764"}
    scoped=[r for r in rows if r["parcel_id"] in targets]
    if len(scoped)!=3 or any(r["london_authority"]!="Enfield" for r in scoped):
        raise SystemExit("CANONICAL_SCOPE_VALIDATION_FAILED")
    urls=fixture["candidate_urls"]
    probes=[]
    probes.append(bounded_get(urls["download_page"],args.timeout,MAX_PAGE)); time.sleep(args.delay)
    probes.append(bounded_head(urls["pbf"],args.timeout)); time.sleep(args.delay)
    probes.append(bounded_get(urls["md5"],args.timeout,MAX_MD5)); time.sleep(args.delay)
    probes.append(bounded_get(urls["poly"],args.timeout,MAX_POLY))
    page, pbf, md5, poly = probes
    md5_text=md5.pop("_text","")
    page_text=page.pop("_text","")
    poly_text=poly.pop("_text","")
    md5_match=re.search(r"\b([0-9a-fA-F]{32})\b",md5_text)
    page_mentions=bool(re.search(r"greater-london-latest\.osm\.pbf",page_text,re.I))
    poly_has_coords=bool(re.search(r"-?\d+\.\d+\s+-?\d+\.\d+",poly_text))
    live_count=sum(1 for p in probes if p["network_error"] is None and p["http_status"] and 200<=p["http_status"]<400)
    metadata_live=(live_count==4 and bool(md5_match) and page_mentions and poly_has_coords)
    state="STATIC_EXTRACT_METADATA_AVAILABLE_CONTINUE_LOCAL_EXTRACTION" if metadata_live else "NO_DATA_CONTINUE"
    decision="GEOFABRIK_GREATER_LONDON_STATIC_EXTRACT_METADATA_GATE_ASSESSED"
    blocker=("PBF_NOT_DOWNLOADED_BY_DESIGN;THREE_EXACT_BUILDING_GEOMETRIES_NOT_EXTRACTED;"
             "THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE")
    if not metadata_live:
        blocker=("GEOFABRIK_GREATER_LONDON_STATIC_EXTRACT_METADATA_NOT_LIVE_ACQUIRED;"+blocker)
    next_step=("PLAN_BOUNDED_LOCAL_GREATER_LONDON_PBF_BUILDING_EXTRACTION"
               if metadata_live else
               "ASSESS_ALTERNATIVE_STATIC_VECTOR_EXTRACT_OR_NO_DATA_CONTINUE")
    errors=[f"{p['method']} {p['source_url']}:{p['network_error']}" for p in probes if p["network_error"]]
    runtime_evidence=[{
        "source_url":"https://download.geofabrik.de/europe/united-kingdom/england/",
        "accessed_at":args.accessed_at,
        "content_sha256":sha256_bytes(("\n".join(errors)).encode("utf-8") if errors else json.dumps(probes,sort_keys=True).encode("utf-8")),
        "hash_scope":"four_bounded_metadata_probe_receipts",
        "record_scope":"Download page GET, PBF HEAD, MD5 GET and region poly GET; no PBF body download.",
        "relevant_record_ids_or_excerpt":"; ".join(errors) if errors else f"live_count={live_count}; md5={md5_match.group(1) if md5_match else None}",
        "supports_fields":["bounded_metadata_probe","pbf_body_not_downloaded","live_network_or_http_evidence","no_exact_binding_claim"],
        "license_or_terms_url":"https://www.openstreetmap.org/copyright"
    }]
    payload={
        "schema_version":1,"architecture_version":3,
        "workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"gas_emissions_2","wave":348,
        "accessed_at":args.accessed_at,"state":state,"decision":decision,
        "canonical_sample_rows_in_scope":3,"assessments":scoped,
        "probe_count":4,"live_probe_count":live_count,
        "network_error_count":sum(1 for p in probes if p["network_error"]),
        "total_bytes_read":sum(p["bytes_read"] for p in probes),
        "pbf_body_downloaded":False,"pbf_content_length_header":pbf["content_length_header"],
        "page_mentions_latest_pbf":page_mentions,"md5_manifest_valid":bool(md5_match),
        "md5_value":md5_match.group(1).lower() if md5_match else None,
        "poly_coordinate_payload_detected":poly_has_coords,
        "probes":probes,"source_evidence_manifest":fixture["source_evidence_manifest"],
        "runtime_source_evidence":runtime_evidence,
        "business_rows_produced":0,"parcel_rows_bound":0,
        "completed_count":0,"target_count":30761,"previous_percent":0.0,
        "current_percent":0.0,"percent_increase":0.0,
        "blocker":blocker,"first_unverified_step":next_step,
        "fake_data":False,"final_ready":False
    }
    atomic_json(Path(args.output),payload)
    print(json.dumps({
        "state":state,"probe_count":4,"live_probe_count":live_count,
        "network_error_count":payload["network_error_count"],
        "total_bytes_read":payload["total_bytes_read"],
        "pbf_body_downloaded":False,"business_rows_produced":0,
        "parcel_rows_bound":0,"first_unverified_step":next_step
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
