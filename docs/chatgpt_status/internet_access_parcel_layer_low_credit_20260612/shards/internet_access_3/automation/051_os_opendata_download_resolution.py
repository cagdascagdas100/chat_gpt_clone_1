#!/usr/bin/env python3
"""Resolve current OS OpenData download metadata without downloading full packages."""
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile, urllib.request
from pathlib import Path
SLOT="internet_access_3"
API="https://api.os.uk/downloads/v1/products/{product}/downloads?format=CSV&area=GB"
HEX32=re.compile(r"^[0-9a-fA-F]{32}$")
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--timeout",type=int,default=60)
 p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/041_os_opendata_download_resolution_latest.json")
 p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/os_opendata_download_resolution_latest.json");return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repo root")
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+".")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def fetch(url,timeout):
 req=urllib.request.Request(url,headers={"User-Agent":"AAYS-internet-access-3/12","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode("utf-8"))
def valid(d):
 return isinstance(d,dict) and str(d.get("area","")).upper()=="GB" and str(d.get("format","")).upper()=="CSV" and bool(d.get("url")) and bool(d.get("fileName")) and int(d.get("size") or 0)>0 and bool(HEX32.fullmatch(str(d.get("md5") or "")))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def main():
 o=args();r=root(o.repo_root);results={};blockers=[]
 for product in ["OpenUPRN","LIDS"]:
  url=API.format(product=product)
  try: raw=fetch(url,o.timeout)
  except Exception as e:raw=[];blockers.append(product+"_API_ERROR_"+type(e).__name__)
  rows=[x for x in raw if valid(x)] if isinstance(raw,list) else []
  results[product]={"endpoint":url,"raw_count":len(raw) if isinstance(raw,list) else 0,"valid_count":len(rows),"downloads":rows,"metadata_sha256":digest(rows)}
 uprn=results["OpenUPRN"]["downloads"];lid=[x for x in results["LIDS"]["downloads"] if "UPRN" in str(x.get("fileName","")).upper() and "TOPOGRAPHICAREA" in str(x.get("fileName","")).upper()]
 if len(uprn)!=1:blockers.append("OPEN_UPRN_GB_CSV_NOT_UNIQUE")
 if len(lid)!=1:blockers.append("LIDS_UPRN_TOPOGRAPHICAREA_NOT_UNIQUE")
 state="resolved" if not blockers else "blocked"
 s={"schema_version":1,"slot_id":SLOT,"state":state,"results":results,"selected":{"open_uprn":uprn[0] if len(uprn)==1 else None,"uprn_topographic_area":lid[0] if len(lid)==1 else None},"source_checks_executed":2,"blockers":blockers,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if not blockers else 2
if __name__=="__main__":raise SystemExit(main())
