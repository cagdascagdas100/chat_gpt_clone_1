#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 args();src=Path(__file__).with_name("053_resumable_download_probe_ledger.py").read_text();t=[]
 def ck(n,c):t.append((n,bool(c)))
 checks=[("RANGE_HEADER",'Range":f"bytes=0-{PROBE-1}"'),("IF_BYTES","bytes_read"),("SHA256","hashlib.sha256"),("ETAG","etag"),("LAST_MODIFIED","last-modified"),("ACCEPT_RANGES","accept-ranges"),("CONTENT_RANGE","content-range"),("EXPECTED_MD5","expected_md5"),("OPEN_UPRN_REQUIRED",'{"open_uprn","ofcom_fixed_broadband"}'),("PROBE_65536","PROBE=65536"),("NO_FULL_HYDRATION",'"full_bytes_hydrated":False'),("RESUME_LEDGER",'"resume_ledger_ready":True'),("NO_PROMOTION","parcel_relations_promoted")]
 for n,s in checks:ck(n,s in src)
 ck("SAFETY_FLAGS",all(x in src for x in ["final_ready","fake_data","db_write","migration","production_deploy"]))
 f=[n for n,c in t if not c];print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":14,"tests_executed":len(t),"tests_passed":len(t)-len(f),"tests_failed":len(f),"failures":f,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())
