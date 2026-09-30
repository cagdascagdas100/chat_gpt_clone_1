from __future__ import annotations
import csv, hashlib, html, io, json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
PAGE_GENERATION=1
PARTITION=[61524,76903]
SEMANTIC_MODE="AREA_JOIN"
CATEGORY="AAYS_SOURCE_AREA_V1"
SOURCE_WINDOW="mps_lsoa_crime_sep2024_aug2026_first50_sps5_v1"
META_URL="https://data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m"
EXPECTED_RANGE_LABEL="Sep 2024 – Aug 2026"
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_source_area_latest.json"

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha(b:bytes):
    return hashlib.sha256(b).hexdigest()
def fetch(url,accept):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-security-public-safety-5/mps-lsoa-source-area-v1","Accept":accept})
    with urllib.request.urlopen(req,timeout=120) as resp:
        b=resp.read()
        return int(resp.status),resp.geturl(),resp.headers.get("Content-Type"),b
def save(o):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

base={
 "schema_version":14,"slot_id":SLOT_ID,"owner":None,"partition":PARTITION,"lineage_id":LINEAGE_ID,
 "page_generation":PAGE_GENERATION,"category":CATEGORY,"semantic_mode":SEMANTIC_MODE,
 "source_window_id":SOURCE_WINDOW,"generated_at_utc":now(),"fake_data":False,
 "accepted_count":0,"materialized_parcel_count":0,"direct_parcel_count":0,
 "verified_no_building_count":0,"unprocessed_count":0,"planned_building_count":0,
 "first_missing_criterion":"LOCAL_OPENCODE_SPATIAL_JOIN_AND_MATERIALIZATION_REQUIRED"
}
try:
    mstatus,mfinal,mctype,mbody=fetch(META_URL,"text/html,application/xhtml+xml")
    mtext=mbody.decode("utf-8","replace")
    if "MPS LSOA Level Crime.csv" not in mtext or ("Sep 2024" not in mtext or "Aug 2026" not in mtext):
        raise RuntimeError("LATEST_MPS_LSOA_VERSION_NOT_CONFIRMED_IN_METADATA")
    norm=html.unescape(mtext).replace("\\/","/").replace("\\u002F","/").replace("\\u002f","/").replace("\\u0026","&")
    raw=[]
    for pat in [
        r'https?://data\.london\.gov\.uk/download/exy3m/[^"\'<>\\\s]+',
        r'/download/exy3m/[^"\'<>\\\s]+'
    ]:
        raw.extend(re.findall(pat,norm))
    candidates=[]
    seen=set()
    for u in raw:
        if u.startswith("/"): u="https://data.london.gov.uk"+u
        u=u.rstrip("),;")
        dec=urllib.parse.unquote(u)
        if "MPS LSOA Level Crime.csv" in dec and "Historical" not in dec and u not in seen:
            seen.add(u); candidates.append(u)
    if not candidates:
        raise RuntimeError("LATEST_MPS_LSOA_DOWNLOAD_URL_NOT_DISCOVERED")
    data_url=candidates[0]
    access_utc=now()
    status,final_url,ctype,body=fetch(data_url,"text/csv,application/csv,text/plain,*/*")
    if status!=200 or len(body)<1000:
        raise RuntimeError("MPS_LSOA_CSV_DOWNLOAD_INVALID")
    try: text=body.decode("utf-8-sig")
    except UnicodeDecodeError: text=body.decode("cp1252")
    rd=csv.DictReader(io.StringIO(text))
    if not rd.fieldnames:
        raise RuntimeError("MPS_LSOA_CSV_HEADER_MISSING")
    fields=list(rd.fieldnames)
    lsoa_field=None
    for f in fields:
        k=re.sub(r"[^a-z0-9]+"," ",f.lower()).strip()
        if "lsoa" in k and "code" in k:
            lsoa_field=f; break
    if lsoa_field is None:
        for f in fields:
            if f.strip().lower() in ("lsoa","lsoa code","lsoa_code"):
                lsoa_field=f; break
    if lsoa_field is None:
        raise RuntimeError("MPS_LSOA_IDENTIFIER_FIELD_NOT_FOUND")
    rows=[]
    for idx,row in enumerate(rd,1):
        if idx>50: break
        clean={str(k): ("" if v is None else str(v)) for k,v in row.items()}
        code=clean.get(lsoa_field,"").strip().upper()
        row_bytes=json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
        rows.append({"record_index":idx,"coverage_area_id":code,"row_sha256":sha(row_bytes),"row":clean})
    if not rows:
        raise RuntimeError("MPS_LSOA_FIRST50_EMPTY")
    valid=[]; rejected=[]
    for r in rows:
        if re.fullmatch(r"[A-Z]\d{8}",r["coverage_area_id"] or ""):
            valid.append(r)
        else:
            rejected.append({"record_index":r["record_index"],"reason":"INVALID_OR_MISSING_LSOA_CODE","raw_value":r["coverage_area_id"],"row_sha256":r["row_sha256"]})
    first_by_id={}
    dup=0
    for r in valid:
        cid=r["coverage_area_id"]
        if cid in first_by_id: dup+=1
        else: first_by_id[cid]=r
    features=[]
    for cid,r in first_by_id.items():
        p={
          "evidence_scope":"coverage_area",
          "coverage_area_id":cid,
          "identifier_scheme":"ONS_LSOA_CODE",
          "source_resolution":"MPS_LSOA_LEVEL_CRIME",
          "time_window":"2024-09/2026-08",
          "measurement_date":"2026-08-31",
          "measurement_method":"official MPS LSOA Level Crime CSV exact identifier evidence",
          "spatial_binding_method":"DEFERRED_TO_LOCAL_OPENCODE",
          "source_url":data_url,
          "final_url":final_url,
          "accessed_at_utc":access_utc,
          "licence":"Open Government Licence v2",
          "source_file_sha256":sha(body),
          "field_evidence":{
             "lsoa_field":lsoa_field,
             "source_record_index":r["record_index"],
             "source_row_sha256":r["row_sha256"],
             "source_row":r["row"]
          },
          "confidence_score_0_100":100,
          "evidence_grade":"A",
          "fake_data":False,
          "source_window_id":SOURCE_WINDOW,
          "cursor":f"{SOURCE_WINDOW}:record={r['record_index']}"
        }
        features.append({"type":"Feature","id":cid,"geometry":None,"properties":p})
    base.update(
      status="SOURCE_WINDOW_COMPLETE",
      metadata_url=META_URL,metadata_final_url=mfinal,metadata_http_status=mstatus,metadata_content_type=mctype,
      metadata_accessed_at_utc=access_utc,metadata_sha256=sha(mbody),
      source_url=data_url,final_url=final_url,http_status=status,content_type=ctype,accessed_at_utc=access_utc,
      data_date="2024-09/2026-08",licence="Open Government Licence v2",source_file_sha256=sha(body),
      csv_header=fields,lsoa_identifier_field=lsoa_field,
      source_records_processed_count=len(rows),
      new_source_records=len(rows),
      source_area_count=len(features),
      duplicate_count=dup,
      rejected_count=len(rejected),
      unmatched_count=0,
      records_geojson={"type":"FeatureCollection","features":features},
      rejected_records=rejected,
      cursor=f"{SOURCE_WINDOW}:record={len(rows)}",
      semantic_precheck_passed=(len(rows)<=50 and len(features)>0),
      delivery_blocked=None
    )
except Exception as ex:
    base.update(status="BLOCKED",source_records_processed_count=0,new_source_records=0,source_area_count=0,duplicate_count=0,rejected_count=0,unmatched_count=0,
                records_geojson={"type":"FeatureCollection","features":[]},error=str(ex),semantic_precheck_passed=False,delivery_blocked="SOURCE_DISCOVERY_OR_PARSE_FAILED")
save(base)
print("STATUS="+base.get("status",""))
print("SOURCE_AREA_COUNT="+str(base.get("source_area_count",0)))
print("NEW_SOURCE_RECORDS="+str(base.get("new_source_records",0)))
print("SEMANTIC_PRECHECK_PASSED="+str(base.get("semantic_precheck_passed",False)).lower())
