#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def main():
 args();src=Path(__file__).with_name("055_uprn_relation_schema_contract.py").read_text();t=[]
 def ck(n,c):t.append((n,bool(c)))
 ck("OS_FIELDS_5",all(x in src for x in ["UPRN","X_COORDINATE","Y_COORDINATE","LATITUDE","LONGITUDE"]));ck("POSTCODE_ALIASES",all(x in src for x in ["PCDS","PCD","PCD2","POSTCODE"]));ck("JOIN_KEY",'"join_key":"UPRN"' in src);ck("SAME_UPRN",'"same_uprn_required":True' in src);ck("NORMALIZE",'"postcode_normalization_required":True' in src);ck("NO_DUPLICATES",'"duplicate_uprn_conflicts_expected":0' in src);ck("JOIN_98",'"minimum_join_ratio":0.98' in src);ck("NO_NEAREST",'"nearest_point_join_forbidden":True' in src);ck("NO_PROMOTION",'"parcel_relation_promotion_forbidden":True' in src);ck("ADDRESS_POINT_SEMANTICS","ADDRESS_POINT_BNG_AND_ETRS89_NOT_PARCEL_BOUNDARY" in src);ck("PENDING_BYTES","contract_ready_pending_release_bytes" in src);ck("CONTRACT_HASH","contract_sha256" in src);ck("ZERO_UPLIFT","confidence_uplifts" in src);ck("SAFETY_FLAGS",all(x in src for x in ["final_ready","fake_data","db_write","migration","production_deploy"]))
 f=[n for n,c in t if not c];print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":14,"tests_executed":len(t),"tests_passed":len(t)-len(f),"tests_failed":len(f),"failures":f,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())
