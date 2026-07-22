#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,tempfile,zipfile
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).with_name("065_codepoint_open_exact_crosscheck.py");s=importlib.util.spec_from_file_location("cp",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 m=mod();checks=[]
 def ck(n,x,d=""):checks.append({"name":n,"passed":bool(x),"detail":d})
 ck("NORMALIZE_SPACED",m.normalize_postcode("SW1A 1AA")=="SW1A1AA");ck("NORMALIZE_COMPACT",m.normalize_postcode("sw1a1aa")=="SW1A1AA");ck("NORMALIZE_INVALID",m.normalize_postcode("bad") is None)
 payload=[{"fileName":"codepo_gb.zip","url":"https://example.test/codepo.zip","md5":"a"*32,"size":123,"format":"CSV","area":"GB"}];chosen=m.choose_download(payload);ck("CHOOSE_UNIQUE",chosen["file_name"]=="codepo_gb.zip")
 try:m.choose_download(payload+payload);dedup=True
 except ValueError:dedup=False
 ck("DEDUP_IDENTICAL",dedup)
 try:m.choose_download([{"fileName":"x.zip","url":"https://e/x","md5":"bad","size":1,"format":"CSV","area":"GB"}]);bad=False
 except ValueError:bad=True
 ck("INVALID_MD5_BLOCKED",bad);ck("COORD_PQI10",m.valid_coordinate(437292,115542,10));ck("COORD_PQI90_BLOCKED",not m.valid_coordinate(437292,115542,90));ck("COORD_RANGE_BLOCKED",not m.valid_coordinate(9999999,115542,10))
 with tempfile.TemporaryDirectory() as td:
  z=Path(td)/"x.zip"
  with zipfile.ZipFile(z,"w") as a:a.writestr("Data/CSV/so.csv",'"SO16 0AS",10,437292,115542,"E92000001","E19000002","E18000009","E10000014","E07000093","E05012936"\r\n')
  records,audit=m.read_target_records(z,{"SO160AS"});ck("ZIP_RECORD_FOUND","SO160AS" in records);ck("ZIP_MEMBER_COUNT",audit["csv_members_scanned"]==1);ck("ZIP_NO_CONFLICT",audit["duplicate_postcode_conflicts"]==[]);ck("ZIP_PQI",records["SO160AS"]["positional_quality_indicator"]==10)
 source=Path(__file__).with_name("065_codepoint_open_exact_crosscheck.py").read_text();ck("NO_PROMOTION","parcel_relations_promoted" in source and '"parcel_relation_promoted":False' in source);ck("SAMPLE_384",m.SAMPLE_SIZE==384);ck("API_PRODUCT_ID","CodePointOpen" in m.API_URL and "format=CSV" in m.API_URL and "area=GB" in m.API_URL)
 failed=[x for x in checks if not x["passed"]];out={"schema_version":1,"slot_id":"internet_access_3","tests_executed":len(checks),"tests_passed":len(checks)-len(failed),"tests_failed":len(failed),"checks":checks,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 if (o:=args()).repo_root:
  p=o.repo_root/"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/047_codepoint_open_exact_crosscheck_tests_latest.json";p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps(out,indent=2));return 0 if not failed else 2
if __name__=="__main__":raise SystemExit(main())
