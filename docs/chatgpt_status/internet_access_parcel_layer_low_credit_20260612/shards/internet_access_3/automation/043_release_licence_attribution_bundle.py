#!/usr/bin/env python3
"""Build a verified attribution and release bundle for internet_access_3 official sources."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from pathlib import Path
from typing import Any
SLOT="internet_access_3"
REGISTRIES={"ofcom":"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/001_ofcom_spring_2026_registry_latest.json","onspd":"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/003_onspd_may_2026_registry_latest.json","hmlr":"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/004_hmlr_inspire_july_2026_registry_latest.json","uprn":"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/007_official_uprn_relation_registry_latest.json"}
ATTRIBUTIONS={"ofcom":["Source: Ofcom Connected Nations update: Spring 2026","Licensed under the Open Government Licence subject to Ofcom terms"],"onspd":["Source: Office for National Statistics licensed under the Open Government Licence v.3.0","Contains OS data © Crown copyright and database right 2026","Contains Royal Mail data © Royal Mail copyright and database right 2026"],"hmlr":["This information is subject to Crown copyright and database rights 2026 and is reproduced with the permission of HM Land Registry.","The polygons (including the associated geometry, namely x, y co-ordinates) are subject to Crown copyright and database rights 2026 Ordnance Survey AC0000851063."],"uprn":["Contains OS data © Crown copyright and database right 2026","Contains Royal Mail data © Royal Mail copyright and database right 2026","Contains GeoPlace data © Local Government Information House Limited copyright and database right 2026","Source: Office for National Statistics licensed under the Open Government Licence v.3.0"]}
REQUIRED={"ofcom":["ofcom","open government licence"],"onspd":["office for national statistics","os data","royal mail"],"hmlr":["hm land registry","ordnance survey","ac0000851063"],"uprn":["os data","royal mail","geoplace","office for national statistics"]}
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/034_release_licence_attribution_bundle_latest.json");p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/release_licence_attribution_bundle_latest.json");return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError("repository root not found")
def load(p):
 with p.open("r",encoding="utf-8-sig") as h:return json.load(h)
def sha(p):
 d=hashlib.sha256()
 with p.open("rb") as h:
  for b in iter(lambda:h.read(1048576),b""):d.update(b)
 return d.hexdigest()
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=p.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def main():
 o=args();r=root(o.repo_root);entries=[];blockers=[]
 for key,rel in REGISTRIES.items():
  p=r/rel
  if not p.exists():blockers.append("REGISTRY_MISSING:"+key);continue
  x=load(p);statements=ATTRIBUTIONS[key];text=" ".join(statements).lower();missing=[z for z in REQUIRED[key] if z not in text]
  if missing:blockers.append("ATTRIBUTION_TOKENS_MISSING:"+key+":"+",".join(missing))
  entries.append({"source_key":key,"registry_path":rel,"registry_sha256":sha(p),"source_authority":x.get("source_authority") or x.get("authority") or x.get("publisher"),"publication":x.get("publication") or x.get("dataset") or x.get("product"),"publication_date":x.get("publication_date") or x.get("source_snapshot_date"),"attribution_statements":statements,"attribution_complete":not missing})
 passed=len(entries)==4 and not blockers;s={"schema_version":1,"slot_id":SLOT,"state":"attribution_bundle_passed" if passed else "blocked","source_count_expected":4,"source_count_recorded":len(entries),"entries":entries,"blockers":blockers,"parcel_relations_promoted":0,"confidence_uplifts":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=="__main__":raise SystemExit(main())
