#!/usr/bin/env python3
"""Final fail-closed acceptance for revision 16 UPRN release processing."""
from __future__ import annotations
import argparse,json,os,re,tempfile
from pathlib import Path
SLOT_ID="internet_access_3"
DEFAULT_PREFLIGHT="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/052_runtime_resource_download_preflight_latest.json"
DEFAULT_HYDRATION="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/050_full_release_hydration_manifest_latest.json"
DEFAULT_JOIN="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/053_exact_uprn_postcode_join_revision16_latest.json"
DEFAULT_CONSENSUS="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/048_official_postcode_source_consensus_latest.json"
DEFAULT_PREVIEW="england_map_web/data/aays_21_slots/internet_access_3/exact_uprn_postcode_join_revision16_preview_latest.json"
DEFAULT_RUNNER="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/054_revision16_runtime_acceptance_latest.json"
DEFAULT_WEB="england_map_web/data/aays_21_slots/internet_access_3/revision16_runtime_acceptance_latest.json"
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--preflight",default=DEFAULT_PREFLIGHT);p.add_argument("--hydration",default=DEFAULT_HYDRATION);p.add_argument("--join",default=DEFAULT_JOIN);p.add_argument("--consensus",default=DEFAULT_CONSENSUS);p.add_argument("--preview",default=DEFAULT_PREVIEW);p.add_argument("--runner-output",default=DEFAULT_RUNNER);p.add_argument("--web-output",default=DEFAULT_WEB);return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repo root")
def load(p):
 with p.open("r",encoding="utf-8-sig") as h:return json.load(h)
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=p.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(x,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def safe_flags(x):
 return all(x.get(k) is False or x.get(k)==0 for k in ("final_ready","fake_data","db_write","migration","production_deploy","parcel_relations_promoted","confidence_uplifts","actual_business_data_rows_written"))
def main():
 o=args();r=root(o.repo_root);items={"preflight":load(r/o.preflight),"hydration":load(r/o.hydration),"join":load(r/o.join),"consensus":load(r/o.consensus),"preview":load(r/o.preview)};blockers=[]
 for name in ("preflight","hydration","join","consensus"):
  x=items[name]
  if x.get("state")!="runtime_validation_passed":blockers.append(name.upper()+"_NOT_PASSED")
  if not safe_flags(x):blockers.append(name.upper()+"_SAFETY_FLAG_VIOLATION")
 h=items["hydration"];packs=h.get("packages") or []
 if int(h.get("packages_hydrated") or 0)!=4 or len(packs)!=4:blockers.append("HYDRATED_PACKAGE_COUNT_NOT_4")
 for p in packs:
  pid=str(p.get("package_id") or "UNKNOWN").upper()
  if not p.get("size_verified"):blockers.append(pid+"_SIZE_NOT_VERIFIED")
  if p.get("expected_md5") and not p.get("md5_verified"):blockers.append(pid+"_MD5_NOT_VERIFIED")
  if not re.fullmatch(r"[0-9a-f]{64}",str(p.get("actual_sha256") or "").lower()):blockers.append(pid+"_SHA256_MISSING")
  if p.get("media_type")=="application/zip" and not p.get("zip_integrity_passed"):blockers.append(pid+"_ZIP_NOT_VERIFIED")
 j=items["join"];stats=j.get("join_stats") or {}
 for source in ("nsul","onsud"):
  x=stats.get(source) or {}
  if float(x.get("join_ratio") or 0)<0.98:blockers.append(source.upper()+"_JOIN_BELOW_98")
  if int(x.get("duplicate_postcode_conflicts") or 0)!=0:blockers.append(source.upper()+"_CONFLICTS")
 if int(j.get("cross_source_postcode_conflicts") or 0)!=0:blockers.append("CROSS_SOURCE_POSTCODE_CONFLICTS")
 if float(j.get("common_exact_ratio") or 0)<0.95:blockers.append("COMMON_EXACT_RATIO_BELOW_95")
 pv=items["preview"];rows=pv.get("rows") or []
 if len(rows)!=40:blockers.append(f"PREVIEW_COUNT:{len(rows)}!=40")
 for x in rows:
  if set(x.get("sources") or [])!={"nsul","onsud"}:blockers.append("PREVIEW_NOT_DUAL_SOURCE");break
  if x.get("parcel_relation_promoted") is not False:blockers.append("PREVIEW_PARCEL_PROMOTION");break
 passed=not blockers;now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
 s={"schema_version":1,"task_id":"aays1-internet-access-3-revision16-runtime-acceptance-20260722","slot_id":SLOT_ID,"state":"runtime_validation_passed" if passed else "blocked","updated_at":now,
 "result":{"packages_hydrated":len(packs),"download_bytes_hydrated":int(h.get("download_bytes_hydrated") or 0),"os_open_uprn_rows":int((j.get("os_open_uprn") or {}).get("rows_inserted") or 0),
 "nsul_join_ratio":float((stats.get("nsul") or {}).get("join_ratio") or 0),"onsud_join_ratio":float((stats.get("onsud") or {}).get("join_ratio") or 0),
 "common_exact_uprn_postcode_rows":int(j.get("common_exact_uprn_postcode_rows") or 0),"preview_rows":len(rows),"parcel_relations_promoted":0,"actual_business_data_rows_written":0},
 "validation":{"passed":passed,"blockers":blockers},"acceptance_semantics":"OFFICIAL_RELEASE_AND_EXACT_UPRN_POSTCODE_SOURCE_RELATION_ACCEPTED_NOT_PARCEL_RELATION",
 "final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=="__main__":raise SystemExit(main())
