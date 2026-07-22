#!/usr/bin/env python3
"""Cross-check the exact 384-row manifest against current OS Code-Point Open.

This worker validates postcode existence and postcode-point coordinate quality only.
It never promotes a postcode proxy to an address or parcel relation.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,os,re,tempfile,time,urllib.request,zipfile
from collections import Counter
from pathlib import Path
from typing import Any
SLOT_ID="internet_access_3";SAMPLE_SIZE=384;API_URL="https://api.os.uk/downloads/v1/products/CodePointOpen/downloads?format=CSV&area=GB";VALID_PQI={10,20,30,40,50,60,90}
def parse_args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--manifest",default="england_map_web/data/aays_21_slots/internet_access_3/stratified_candidate_manifest_latest.json");p.add_argument("--registry",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/012_codepoint_open_release_registry_latest.json");p.add_argument("--cache-dir",default=".cache/aays/internet_access_3/codepoint_open");p.add_argument("--timeout",type=int,default=180);p.add_argument("--retries",type=int,default=3);p.add_argument("--minimum-match-ratio",type=float,default=.95);p.add_argument("--minimum-coordinate-ratio",type=float,default=.90);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/046_codepoint_open_exact_crosscheck_latest.json");p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/codepoint_open_exact_crosscheck_latest.json");p.add_argument("--web-candidates",default="england_map_web/data/aays_21_slots/internet_access_3/codepoint_open_exact_candidates_latest.json");return p.parse_args()
def repo_root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repository root not found")
def load_json(p):
 with p.open("r",encoding="utf-8-sig") as h:return json.load(h)
def atomic_json(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=p.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def normalize_postcode(v):
 x=re.sub(r"\s+","",str(v or "")).upper();return x if re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}",x) else None
def iter_download_candidates(v):
 out=[]
 if isinstance(v,dict):
  if (v.get("url") or v.get("downloadUrl") or v.get("downloadURL")) and (v.get("fileName") or v.get("filename") or v.get("name")):out.append(v)
  for x in v.values():out+=iter_download_candidates(x)
 elif isinstance(v,list):
  for x in v:out+=iter_download_candidates(x)
 return out
def val(d,*ks):
 for k in ks:
  if d.get(k) not in (None,""):return d[k]
 return None
def choose_download(payload):
 out=[]
 for raw in iter_download_candidates(payload):
  name=str(val(raw,"fileName","filename","name") or "");fmt=str(val(raw,"format","fileFormat") or "").upper();area=str(val(raw,"area","coverage") or "").upper();url=str(val(raw,"url","downloadUrl","downloadURL") or "");md5=str(val(raw,"md5","checksum","hash") or "").lower()
  try:size=int(val(raw,"size","fileSize","contentLength"))
  except (TypeError,ValueError):size=0
  if url.startswith("http") and ("CSV" in fmt or name.lower().endswith((".zip",".csv"))) and (area in {"","GB"} or "GB" in name.upper()) and re.fullmatch(r"[0-9a-f]{32}",md5) and size>0:out.append({"file_name":name,"url":url,"md5":md5,"size":size,"format":fmt or "CSV","area":area or "GB"})
 unique={(x["file_name"],x["url"],x["md5"],x["size"]):x for x in out};selected=list(unique.values())
 if len(selected)!=1:raise ValueError(f"CodePointOpen unique GB CSV download expected, found={len(selected)}")
 return selected[0]
def request_json(url,timeout):
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"TerraYield-AAYS-internet-access-3/1.0","Accept":"application/json"}),timeout=timeout) as r:return json.load(r)
def md5_file(p):
 d=hashlib.md5()
 with p.open("rb") as h:
  for b in iter(lambda:h.read(1048576),b""):d.update(b)
 return d.hexdigest()
def download_file(url,target,expected_md5,expected_size,retries,timeout):
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists() and target.stat().st_size==expected_size and md5_file(target)==expected_md5:return target,True
 last=None
 for attempt in range(max(1,retries)):
  tmp=target.with_suffix(target.suffix+".part")
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"TerraYield-AAYS-internet-access-3/1.0"}),timeout=timeout) as r,tmp.open("wb") as w:
    while True:
     b=r.read(1048576)
     if not b:break
     w.write(b)
   if tmp.stat().st_size!=expected_size:raise ValueError(f"download size mismatch:{tmp.stat().st_size}!={expected_size}")
   actual=md5_file(tmp)
   if actual!=expected_md5:raise ValueError(f"download md5 mismatch:{actual}!={expected_md5}")
   os.replace(tmp,target);return target,False
  except Exception as e:
   last=e
   try:tmp.unlink()
   except FileNotFoundError:pass
   if attempt+1<retries:time.sleep(min(8,2**attempt))
 raise RuntimeError(f"CodePointOpen download failed: {last}")
def valid_coordinate(e,n,pqi):
 try:e=int(e);n=int(n);pqi=int(pqi)
 except (TypeError,ValueError):return False
 return pqi in VALID_PQI and pqi!=90 and 0<e<800000 and 0<n<1400000
def read_target_records(path,targets):
 records={};invalid_width=invalid_pqi=members_count=0;conflicts=[]
 with zipfile.ZipFile(path,"r") as z:
  members=[n for n in z.namelist() if n.lower().endswith(".csv") and ("/data/" in ("/"+n.lower()) or "/csv/" in ("/"+n.lower()))] or [n for n in z.namelist() if n.lower().endswith(".csv")]
  for member in members:
   members_count+=1
   with z.open(member) as b:
    for raw in csv.reader(io.TextIOWrapper(b,encoding="utf-8-sig",newline="")):
     if not raw:continue
     if len(raw)<10:invalid_width+=1;continue
     pc=normalize_postcode(raw[0])
     if pc not in targets:continue
     try:pqi=int(raw[1])
     except (TypeError,ValueError):invalid_pqi+=1;continue
     if pqi not in VALID_PQI:invalid_pqi+=1
     record={"postcode":pc,"positional_quality_indicator":pqi,"eastings":int(raw[2] or 0),"northings":int(raw[3] or 0),"country_code":raw[4],"admin_district_code":raw[8],"admin_ward_code":raw[9],"source_member":member}
     if pc in records and records[pc]!=record:conflicts.append(pc)
     records[pc]=record
 return records,{"csv_members_scanned":members_count,"invalid_record_width_count":invalid_width,"invalid_pqi_count":invalid_pqi,"duplicate_postcode_conflicts":sorted(set(conflicts))}
def main():
 o=parse_args()
 if not 0<o.minimum_match_ratio<=1 or not 0<o.minimum_coordinate_ratio<=1:raise ValueError("ratios")
 r=repo_root(o.repo_root);manifest=load_json(r/o.manifest);registry=load_json(r/o.registry)
 if not isinstance(manifest,list) or len(manifest)!=SAMPLE_SIZE:raise ValueError("stratified manifest missing or wrong count")
 ids=[int(x["row_no"]) for x in manifest]
 if len(ids)!=len(set(ids)):raise ValueError("duplicate row identities in manifest")
 targets={normalize_postcode(x.get("postcode")) for x in manifest}-{None}
 if len(targets)<math.ceil(SAMPLE_SIZE*.90):raise ValueError("insufficient unique postcodes")
 selected=choose_download(request_json(str(registry["source"]["downloads_api"]),o.timeout));safe=re.sub(r"[^A-Za-z0-9._-]+","_",selected["file_name"]) or "codepointopen.zip";archive,cache_hit=download_file(selected["url"],r/o.cache_dir/selected["md5"]/safe,selected["md5"],selected["size"],o.retries,o.timeout);records,audit=read_target_records(archive,targets)
 candidates=[];pqi=Counter();matches=coords=0
 for item in manifest:
  pc=normalize_postcode(item.get("postcode"));rec=records.get(pc or "");found=rec is not None;coord=bool(rec and valid_coordinate(rec["eastings"],rec["northings"],rec["positional_quality_indicator"]));matches+=int(found);coords+=int(coord)
  if found:pqi[str(rec["positional_quality_indicator"])]+=1
  candidates.append({"row_no":int(item["row_no"]),"parcel_id":item.get("parcel_id"),"postcode":pc,"manifest_identity_matched":True,"codepoint_postcode_found":found,"codepoint_coordinate_available":coord,"codepoint_eastings":rec.get("eastings") if rec else None,"codepoint_northings":rec.get("northings") if rec else None,"codepoint_pqi":rec.get("positional_quality_indicator") if rec else None,"status":"OFFICIAL_CODEPOINT_POSTCODE_FOUND_NOT_PROMOTED" if found else "CODEPOINT_POSTCODE_NOT_FOUND","parcel_relation_promoted":False,"confidence_raised":False})
 min_match=math.ceil(SAMPLE_SIZE*o.minimum_match_ratio);min_coord=math.ceil(SAMPLE_SIZE*o.minimum_coordinate_ratio);blockers=[]
 if matches<min_match:blockers.append(f"CODEPOINT_EXACT_POSTCODE_MATCH_GATE:{matches}<{min_match}")
 if coords<min_coord:blockers.append(f"CODEPOINT_COORDINATE_GATE:{coords}<{min_coord}")
 if audit["duplicate_postcode_conflicts"]:blockers.append("CODEPOINT_DUPLICATE_POSTCODE_CONFLICTS")
 if audit["invalid_pqi_count"]:blockers.append("CODEPOINT_INVALID_PQI_VALUES")
 passed=not blockers;now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat();summary={"schema_version":1,"task_id":"aays1-internet-access-3-codepoint-open-exact-crosscheck-20260722","slot_id":SLOT_ID,"state":"runtime_validation_passed" if passed else "blocked","updated_at":now,"source_validation":{"authority":registry["source"]["authority"],"product":registry["source"]["product"],"version_date":registry["source"]["version_date"],"selected_download":selected,"archive_path":str(archive.relative_to(r)),"archive_cache_hit":cache_hit,"archive_md5":md5_file(archive),"archive_audit":audit},"guard":{"sample_size_required":SAMPLE_SIZE,"minimum_matches_required":min_match,"minimum_coordinates_required":min_coord,"exact_manifest_row_identity_required":True},"result":{"sample_rows_selected":len(candidates),"codepoint_exact_postcodes_found":matches,"codepoint_coordinates_available":coords,"pqi_distribution":dict(sorted(pqi.items())),"parcel_relations_promoted":0,"confidence_uplifts":0,"new_postcode_matches_created":0,"actual_business_data_rows_written":0},"validation":{"passed":passed,"blockers":blockers},"output_semantics":"OFFICIAL_POSTCODE_POINT_CROSSCHECK_ONLY_NOT_ADDRESS_OR_PARCEL_PROOF","final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 atomic_json(r/o.runner_output,summary);atomic_json(r/o.web_output,summary);atomic_json(r/o.web_candidates,candidates);print(json.dumps(summary,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=="__main__":
 try:raise SystemExit(main())
 except Exception as e:print(json.dumps({"slot_id":SLOT_ID,"state":"exception","error_type":type(e).__name__,"error":str(e),"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False),file=__import__("sys").stderr);raise
