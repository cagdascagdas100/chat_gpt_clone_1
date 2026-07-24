#!/usr/bin/env python3
"""Probe official package download endpoints for resume/cache integrity without full hydration."""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile,urllib.request
from pathlib import Path
SLOT="internet_access_3";PROBE=65536
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--timeout",type=int,default=90)
 p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/042_resumable_download_probe_ledger_latest.json")
 p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/resumable_download_probe_ledger_latest.json");return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError
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
def probe(url,timeout):
 req=urllib.request.Request(url,headers={"User-Agent":"AAYS-internet-access-3/12","Range":f"bytes=0-{PROBE-1}","Accept":"*/*"})
 with urllib.request.urlopen(req,timeout=timeout) as x:
  b=x.read(PROBE);h={k.lower():v for k,v in x.headers.items()}
  return {"status":getattr(x,"status",None),"final_url":x.geturl(),"bytes_read":len(b),"sha256":hashlib.sha256(b).hexdigest(),"etag":h.get("etag"),"last_modified":h.get("last-modified"),"accept_ranges":h.get("accept-ranges"),"content_range":h.get("content-range"),"content_length":h.get("content-length"),"content_type":h.get("content-type")}
def main():
 o=args();r=root(o.repo_root);sources={}
 osout=r/"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/041_os_opendata_download_resolution_latest.json"
 if osout.exists():
  x=load(osout);sel=x.get("selected") or {}
  for key in ["open_uprn","uprn_topographic_area"]:
   d=sel.get(key)
   if isinstance(d,dict) and d.get("url"):sources[key]={"url":d["url"],"expected_size":d.get("size"),"expected_md5":d.get("md5")}
 ofreg=r/"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/001_ofcom_spring_2026_registry_latest.json"
 if ofreg.exists():
  x=load(ofreg);u=x.get("download_url")
  if u:sources["ofcom_fixed_broadband"]={"url":u}
 rel=r/"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/015_ons_uprn_arcgis_release_discovery_latest.json"
 if rel.exists():
  x=load(rel)
  for k in ["nsul","onsud"]:
   d=((x.get("selected") or {}).get(k) or {});u=d.get("download_url") or d.get("url")
   if u:sources[k]={"url":u}
 checks=[];block=[]
 for name,d in sources.items():
  try:q=probe(d["url"],o.timeout);passed=q["status"] in [200,206] and q["bytes_read"]>0 and len(q["sha256"])==64
  except Exception as e:q={"error_type":type(e).__name__,"error":str(e)};passed=False
  checks.append({"source":name,"passed":passed,"contract":d,"probe":q})
  if not passed:block.append(name.upper()+"_RANGE_PROBE_FAILED")
 required={"open_uprn","ofcom_fixed_broadband"};missing=sorted(required-set(sources));block += [x.upper()+"_DOWNLOAD_NOT_RESOLVED" for x in missing]
 s={"schema_version":1,"slot_id":SLOT,"state":"passed" if not block else "blocked","probe_bytes":PROBE,"sources_discovered":len(sources),"checks_executed":len(checks),"checks":checks,"blockers":block,"full_bytes_hydrated":False,"resume_ledger_ready":True,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if not block else 2
if __name__=="__main__":raise SystemExit(main())
