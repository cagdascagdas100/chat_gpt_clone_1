#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).with_name("059_os_release_consistency_acceptance.py");s=importlib.util.spec_from_file_location("m",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 args();m=mod();t=[]
 def ck(n,c):t.append((n,bool(c)))
 good={"area":"GB","format":"CSV","url":"https://x","fileName":"BLPU_UPRN_TopographicArea_TOID_5.csv","size":842200000,"md5":"a"*32}
 ck("VERSION_DIRECT",m.version_matches({"version":"June 2026"},"June 2026"));ck("VERSION_NESTED",m.version_matches({"x":[{"versionDate":"June 2026"}]},"June 2026"));ck("VERSION_REJECT",not m.version_matches({"version":"April 2026"},"June 2026"));ck("DOWNLOAD_VALID",m.valid_download(good));ck("AREA_REJECT",not m.valid_download({**good,"area":"TQ"}));ck("FORMAT_REJECT",not m.valid_download({**good,"format":"GPKG"}));ck("SIZE_REJECT",not m.valid_download({**good,"size":0}));ck("MD5_REJECT",not m.valid_download({**good,"md5":"x"}));ck("URL_REJECT",not m.valid_download({**good,"url":""}));ck("NAME_REJECT",not m.valid_download({**good,"fileName":""}));src=Path(__file__).with_name("059_os_release_consistency_acceptance.py").read_text();ck("PRODUCT_DETAILS",all(x in src for x in ["products/\"+product","OpenUPRN","LIDS"]));ck("LIDS_TOKEN","required_download_label_token" in src);ck("LIDS_SIZE_GATE","750_000_000" in src and "1_050_000_000" in src);ck("NO_PROMOTION","parcel_relations_promoted" in src);ck("ZERO_UPLIFT","confidence_uplifts" in src);ck("SAFETY_FLAGS",all(x in src for x in ["final_ready","fake_data","db_write","migration","production_deploy"]))
 f=[n for n,c in t if not c];print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":16,"tests_executed":len(t),"tests_passed":len(t)-len(f),"tests_failed":len(f),"failures":f,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())
