#!/usr/bin/env python3
"""Fail closed unless OS Data Hub release pages, product metadata and download metadata agree."""
from __future__ import annotations
import argparse,json,os,re,tempfile,urllib.request
from pathlib import Path
SLOT="internet_access_3";HEX32=re.compile(r"^[0-9a-fA-F]{32}$")
ROOT="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3"
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--timeout",type=int,default=60)
 p.add_argument("--runner-output",default=ROOT+"/runner_outputs/044_os_release_consistency_acceptance_latest.json")
 p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/os_release_consistency_acceptance_latest.json");return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repo root")
def load(p):
 with p.open("r",encoding="utf-8-sig") as h:return json.load(h)
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
 req=urllib.request.Request(url,headers={"User-Agent":"AAYS-internet-access-3/13","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode("utf-8"))
def values(o):
 out=[]
 if isinstance(o,dict):
  for k,v in o.items():
   if str(k).lower() in {"version","versiondate","version_date","releasedate","release_date","latestversion"}:out.append(str(v))
   out+=values(v)
 elif isinstance(o,list):
  for v in o:out+=values(v)
 return out
def version_matches(meta,expected):return any(expected.lower() in v.lower() for v in values(meta))
def valid_download(d):return isinstance(d,dict) and str(d.get("area","")).upper()=="GB" and str(d.get("format","")).upper()=="CSV" and int(d.get("size") or 0)>0 and bool(HEX32.fullmatch(str(d.get("md5") or ""))) and bool(d.get("url")) and bool(d.get("fileName"))
def main():
 o=args();r=root(o.repo_root);reg=load(r/(ROOT+"/source_snapshots/011_os_datahub_release_consistency_registry_latest.json"));res=load(r/(ROOT+"/runner_outputs/041_os_opendata_download_resolution_latest.json"));checks=[];bad=[]
 def ck(n,c,d):checks.append({"name":n,"passed":bool(c),"detail":d});bad.extend([] if c else [n])
 metas={}
 for product in ["OpenUPRN","LIDS"]:
  try:metas[product]=fetch("https://api.os.uk/downloads/v1/products/"+product,o.timeout)
  except Exception as e:metas[product]={"error_type":type(e).__name__,"error":str(e)}
 exp=reg["sources"];ck("OPEN_UPRN_VERSION",version_matches(metas["OpenUPRN"],exp["open_uprn"]["version_date"]),repr(values(metas["OpenUPRN"])));ck("LIDS_VERSION",version_matches(metas["LIDS"],exp["open_linked_identifiers"]["version_date"]),repr(values(metas["LIDS"])))
 sel=res.get("selected") or {};u=sel.get("open_uprn");l=sel.get("uprn_topographic_area")
 ck("OPEN_UPRN_DOWNLOAD_VALID",valid_download(u),repr(u));ck("LIDS_DOWNLOAD_VALID",valid_download(l),repr(l));token=exp["open_linked_identifiers"]["required_download_label_token"].replace(" ","").lower();name=str((l or {}).get("fileName","")).replace(" ","").replace("_","").replace("-","").lower();ck("LIDS_REQUIRED_RELATION",token in name,name);size=int((l or {}).get("size") or 0);ck("LIDS_SIZE_PLAUSIBLE",750_000_000<=size<=1_050_000_000,str(size))
 state="accepted_not_promoted" if not bad else "blocked";s={"schema_version":1,"slot_id":SLOT,"state":state,"checks_total":len(checks),"checks_passed":sum(x["passed"] for x in checks),"checks_failed":len(bad),"checks":checks,"blockers":bad,"product_metadata":metas,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if not bad else 2
if __name__=="__main__":raise SystemExit(main())
