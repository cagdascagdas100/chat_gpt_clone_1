#!/usr/bin/env python3
"""Verify that queued worker paths still match their declared Git blob SHA-1 values."""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile
from pathlib import Path
SLOT="internet_access_3";QUEUE="docs/chatgpt_status/aays1/queue/7000_internet_access_3_migrate_existing_then_no_data_20260722.task.json"
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path)
 p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/045_repo_blob_integrity_matrix_latest.json")
 p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/repo_blob_integrity_matrix_latest.json");return p.parse_args()
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
def git_blob_sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def pairs(o):
 out=[]
 if isinstance(o,dict):
  if isinstance(o.get("path"),str) and isinstance(o.get("blob_sha"),str):out.append((o["path"],o["blob_sha"]))
  for v in o.values():out+=pairs(v)
 elif isinstance(o,list):
  for v in o:out+=pairs(v)
 return out
def main():
 o=args();r=root(o.repo_root);q=load(r/QUEUE);seen=set();rows=[]
 for path,expected in pairs(q):
  if path in seen:continue
  seen.add(path);p=r/path;actual=git_blob_sha(p.read_bytes()) if p.exists() else None;rows.append({"path":path,"expected_blob_sha":expected,"actual_blob_sha":actual,"exists":p.exists(),"matched":actual==expected})
 bad=[x["path"] for x in rows if not x["matched"]];s={"schema_version":1,"slot_id":SLOT,"state":"passed" if not bad else "blocked","artifacts_total":len(rows),"artifacts_matched":len(rows)-len(bad),"artifacts_failed":len(bad),"rows":rows,"blockers":["BLOB_MISMATCH:"+x for x in bad],"remote_readback_required":True,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if not bad else 2
if __name__=="__main__":raise SystemExit(main())
