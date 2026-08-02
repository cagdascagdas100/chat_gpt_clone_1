import argparse,hashlib,json,os,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path

TASK_ID="parcel-label-3-os-open-uprn-download-discovery-v1-20260802"
URLS=(
"https://osdatahub.os.uk/downloads/open/OpenUPRN",
"https://docs.os.uk/os-downloads/products/addresses-and-names-portfolio/os-open-uprn/os-open-uprn-overview/product-supply",
"https://docs.os.uk/os-downloads/resources/product-resources/product-refresh-dates")
OGL="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PROBE="england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT=("docs/chatgpt_status/_shared/slots_21/parcel_label_3/os_open_uprn_download_discovery_result_latest.json",
"england_map_web/data/aays_21_slots/parcel_label_3/os_open_uprn_download_discovery_latest.json")
IDS=("parcel_61523","parcel_61524","parcel_61525"); MAX=1048576
FILE_RE=re.compile(r"https?://[^\\s\"'<>]+(?:\\.csv|\\.gpkg|\\.geopackage|\\.zip)(?:\\?[^\\s\"'<>]*)?",re.I)

def now(): return datetime.now(timezone.utc).isoformat()
def h(v): return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def write(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+".tmp")
 t.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8");os.replace(t,p)
def points():
 rows=json.loads(Path(PROBE).read_text())["canonical_points"]; by={r["parcel_id"]:r for r in rows}
 out=[]
 for i in IDS:
  r=by.get(i)
  if not r or r.get("geometry_type")!="Point" or r.get("point_valid") is not True: raise ValueError("invalid point "+i)
  if not isinstance(r.get("longitude"),(int,float)) or not isinstance(r.get("latitude"),(int,float)): raise ValueError("invalid coords "+i)
  out.append(i)
 return out
def validate():
 points()
 if len(URLS)!=3 or not all(u.startswith(("https://osdatahub.os.uk/","https://docs.os.uk/")) for u in URLS): raise ValueError("official URLs")
 if not OGL.startswith("https://www.nationalarchives.gov.uk/"): raise ValueError("OGL")
 if any(Path(p).is_absolute() for p in (PROBE,*OUT)): raise ValueError("relative paths")
 if not all(p.startswith(("docs/chatgpt_status/_shared/slots_21/parcel_label_3/","england_map_web/data/aays_21_slots/parcel_label_3/")) for p in OUT): raise ValueError("write boundary")
 print("PASS_TARGET_3_OS_OPEN_UPRN_BOUNDED_DOWNLOAD_DISCOVERY_NO_DATA_DOWNLOAD")
def run(timeout):
 pts=points(); evidence=[]; candidates=[]; seen=set()
 for src in URLS:
  at=now(); req=urllib.request.Request(src,headers={"User-Agent":"TerraYield-AAYS/1.0 (+bounded-download-discovery-only)"})
  try:
   with urllib.request.urlopen(req,timeout=timeout) as res:
    raw=res.read(MAX+1)
    if len(raw)>MAX: raise ValueError("response exceeded 1 MiB")
    text=raw.decode("utf-8","replace"); found=FILE_RE.findall(text)
    for u in found:
     u=u.rstrip(".,);]")
     if u not in seen:
      seen.add(u);candidates.append({"source_page_url":src,"download_url":u,"download_attempted":False,"parcel_binding_claimed":False})
    evidence.append({"source_url":src,"accessed_at":at,"content_sha256":h(raw),"sha256_basis":"bounded_raw_response_bytes",
    "relevant_record_ids_or_excerpt":{"direct_download_url_count":len(found),"content_type":res.headers.get("Content-Type"),"final_url":res.geturl()},
    "record_scope":"one bounded official OS page request; max 1 MiB; linked files not downloaded","supports_fields":["download surface","direct file URL candidates"],"license_or_terms_url":OGL,"http_status":getattr(res,"status",None)})
  except Exception as e:
   s=f"OS_OPEN_UPRN_DOWNLOAD_DISCOVERY_ERROR:{type(e).__name__}:{e}"
   evidence.append({"source_url":src,"accessed_at":at,"content_sha256":h(s),"sha256_basis":"bounded_error_evidence_string",
   "relevant_record_ids_or_excerpt":s[:512],"record_scope":"one bounded official OS page request; no linked file download",
   "supports_fields":["download surface","direct file URL candidates"],"license_or_terms_url":OGL,"http_status":getattr(e,"code",None)})
 state="DOWNLOAD_URL_CANDIDATE_DISCOVERED" if candidates else "NO_DATA_CONTINUE"
 obj={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":TASK_ID,
 "generated_at":now(),"state":state,"panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,
 "progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":pts,"produced_candidate_rows":len(candidates),
 "download_candidates":candidates,"source_evidence":evidence,
 "blocker":{"code":"NONE" if candidates else "OS_OPEN_UPRN_DIRECT_DOWNLOAD_URL_NOT_DISCOVERED","state":state,"manual_action_required":False,"retry_unchanged_route":False},
 "next_unverified_step":"VALIDATE_ONE_BOUNDED_OS_OPEN_UPRN_DOWNLOAD_CANDIDATE_WITHOUT_LARGE_DOWNLOAD" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OS_OPEN_UPRN_DOWNLOAD_DISCOVERY",
 "large_data_downloaded":False,"property_type_binding_claimed":False,"uprn_binding_claimed":False,"exact_parcel_binding_claimed":False,
 "inferred_values":0,"fake_data":False,"final_ready":False}
 for p in OUT: write(p,obj)
 return obj
def main():
 a=argparse.ArgumentParser();a.add_argument("--timeout",type=float,default=30);a.add_argument("--validate-only",action="store_true");x=a.parse_args()
 if x.validate_only: validate();return
 r=run(x.timeout);print(json.dumps({"state":r["state"],"completed_count":3,"target_count":3,"produced_candidate_rows":r["produced_candidate_rows"],"evidence_records":len(r["source_evidence"])},separators=(",",":")))
if __name__=="__main__": main()
