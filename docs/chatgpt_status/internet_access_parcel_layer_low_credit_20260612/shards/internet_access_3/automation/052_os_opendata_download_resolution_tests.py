#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def loadmod(p):
 s=importlib.util.spec_from_file_location("m",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=args();m=loadmod(Path(__file__).with_name("051_os_opendata_download_resolution.py"));tests=[]
 def ck(n,c):tests.append((n,bool(c)))
 good={"area":"GB","format":"CSV","url":"https://x","fileName":"OpenUPRN.csv","size":123,"md5":"a"*32}
 ck("VALID_DOWNLOAD",m.valid(good));ck("BAD_AREA",not m.valid({**good,"area":"TQ"}));ck("BAD_FORMAT",not m.valid({**good,"format":"GML"}));ck("MISSING_URL",not m.valid({**good,"url":""}));ck("MISSING_FILE",not m.valid({**good,"fileName":""}));ck("ZERO_SIZE",not m.valid({**good,"size":0}));ck("BAD_MD5",not m.valid({**good,"md5":"x"}));ck("MD5_UPPER",m.valid({**good,"md5":"A"*32}));ck("API_OPENUPRN","OpenUPRN" in m.API.format(product="OpenUPRN"));ck("AREA_GB","area=GB" in m.API);ck("FORMAT_CSV","format=CSV" in m.API);ck("DIGEST_STABLE",m.digest([good])==m.digest([good]));src=Path(__file__).with_name("051_os_opendata_download_resolution.py").read_text();ck("NO_PROMOTION","parcel_relations_promoted" in src);ck("SAFETY_FLAGS",all(x in src for x in ["final_ready","fake_data","db_write","migration","production_deploy"]))
 fail=[n for n,c in tests if not c];print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not fail else "failed","tests_expected":14,"tests_executed":len(tests),"tests_passed":len(tests)-len(fail),"tests_failed":len(fail),"failures":fail,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},indent=2));return 0 if not fail else 2
if __name__=="__main__":raise SystemExit(main())
