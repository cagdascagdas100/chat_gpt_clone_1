from __future__ import annotations
import hashlib, json, mmap, os, re
from datetime import datetime, timezone
from pathlib import Path

SLOT="gas_emissions_1"
EXPECTED=92283
SOURCE=Path("england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson")
REPORT=Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_registry_geometry_preflight_latest.json")
STATUS=Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_registry_geometry_preflight_latest.json")

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def blob_sha(path):
    size=path.stat().st_size
    h=hashlib.sha1()
    h.update(b"blob "+str(size).encode("ascii")+b"\0")
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    task=os.environ.get("AAYS_TASK_ID","")
    if os.environ.get("AAYS_SLOT_ID","")!=SLOT or not task:
        raise RuntimeError("GAS_EMISSIONS_1_REGISTRY_V2_WRONG_SLOT_CONTEXT")
    if not SOURCE.is_file():
        raise RuntimeError("KNOWN_92283_GEOMETRY_SOURCE_MISSING")

    id_re=re.compile(rb'"security_parcel_id"\s*:\s*"parcel_(\d+)"')
    feature_re=re.compile(rb'\{\s*"type"\s*:\s*"Feature"\s*,\s*"properties"\s*:')
    geometry_re=re.compile(rb'"geometry"\s*:\s*\{\s*"type"\s*:\s*"([^"]+)"')
    sample_re=re.compile(
        rb'"security_parcel_id"\s*:\s*"parcel_(\d+)".{0,8192}?'
        rb'"geometry"\s*:\s*\{\s*"type"\s*:\s*"([^"]+)"\s*,\s*"coordinates"\s*:\s*\[\s*'
        rb'([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)',re.DOTALL)

    with SOURCE.open("rb") as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        ids=[int(m.group(1)) for m in id_re.finditer(mm)]
        feature_count=sum(1 for _ in feature_re.finditer(mm))
        geometry_count=sum(1 for _ in geometry_re.finditer(mm))
        samples=[]
        for m in sample_re.finditer(mm):
            samples.append({
                "parcel_id":"parcel_"+str(int(m.group(1))),
                "geometry_type":m.group(2).decode("utf-8",errors="replace"),
                "coordinates":[float(m.group(3)),float(m.group(4))]
            })
            if len(samples)>=12:
                break

    unique=set(ids)
    continuous=bool(unique and min(unique)==1 and max(unique)==EXPECTED and len(unique)==EXPECTED)
    verified=bool(
        feature_count==EXPECTED and len(ids)==EXPECTED and len(unique)==EXPECTED
        and len(ids)-len(unique)==0 and geometry_count==EXPECTED and continuous
    )
    source_sha=blob_sha(SOURCE)
    payload={
        "schema_version":2,
        "architecture_version":3,
        "workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id":SLOT,
        "task_id":task,
        "parcel_partition":{"start":1,"end":30761,"count":30761,"canonical_count":EXPECTED},
        "status":"PASS_VERIFIED_92283_GEOMETRY_REGISTRY" if verified else "BLOCKED_92283_GEOMETRY_REGISTRY_V2",
        "generated_at":now(),
        "verified_registry_ready":verified,
        "verified_registry":{
            "path":SOURCE.as_posix(),
            "git_blob_sha":source_sha,
            "size_bytes":SOURCE.stat().st_size,
            "row_container":"features",
            "row_count":feature_count,
            "security_parcel_id_count":len(ids),
            "unique_parcel_id_count":len(unique),
            "duplicate_parcel_id_count":len(ids)-len(unique),
            "geometry_row_count":geometry_count,
            "min_parcel_number":min(unique) if unique else None,
            "max_parcel_number":max(unique) if unique else None,
            "continuous_parcel_ids":continuous,
            "geometry_type_expected":"Point",
            "parse_method":"MMAP_REGEX_SECURITY_PARCEL_ID_V2"
        },
        "sample_parcels":samples,
        "sample_parcel_count":len(samples),
        "geometry_identity_usage":{
            "read_only":True,
            "security_scores_owned":False,
            "security_scores_copied":False,
            "security_fields_ignored":True
        },
        "measured_emission_rows_created":0,
        "area_proxy_rows_created":0,
        "data_status":"registry_only_no_emissions_value" if verified else "no_data",
        "blocker":None if verified else "FULL_92283_ID_GEOMETRY_CONTINUITY_CHECK_FAILED",
        "next_action":"Bind official point/grid candidates to parcel_1-30761 geometry identity only; do not copy security scores or create emissions until official source schema is verified.",
        "final_ready":False,
        "product_final_ready":False,
        "fake_data":False,
        "db_write":False,
        "migration":False,
        "production_deploy":False
    }
    text=json.dumps(payload,ensure_ascii=False,indent=2)+"\n"
    for path in (REPORT,STATUS):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding="utf-8")
    print(text,end="")
    return 0 if verified else 2

if __name__=="__main__":
    raise SystemExit(main())
