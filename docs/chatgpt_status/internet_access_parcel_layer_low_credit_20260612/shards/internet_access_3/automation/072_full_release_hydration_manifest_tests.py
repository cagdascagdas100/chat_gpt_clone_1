#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,tempfile,zipfile
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).parent/"071_full_release_hydration_manifest.py";s=importlib.util.spec_from_file_location("h",p)
 if not s or not s.loader:raise ImportError(p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 m=mod();c=[]
 def ok(n,v):
  if not v:raise AssertionError(n)
  c.append(n)
 ok("SAFE",m.safe("A B/C")=="A_B_C")
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);csv=d/"a.csv";csv.write_text("UPRN,X\n1,2\n");info=m.inspect(csv);ok("CSV_MEDIA",info["media_type"]=="text/csv-or-text")
  z=d/"a.zip"
  with zipfile.ZipFile(z,"w") as a:a.writestr("x.csv","UPRN,PCDS\n1,AA11AA\n")
  zi=m.inspect(z);ok("ZIP_MEDIA",zi["media_type"]=="application/zip");ok("ZIP_INTEGRITY",zi["zip_integrity_passed"]);ok("ZIP_MEMBER_COUNT",zi["zip_member_count"]==1);ok("ZIP_CSV_COUNT",zi["zip_csv_member_count"]==1);ok("MD5_LENGTH",len(m.digest(csv,"md5"))==32);ok("SHA256_LENGTH",len(m.digest(csv,"sha256"))==64)
  spec={"package_id":"os_open_uprn","expected_size":z.stat().st_size,"expected_md5":m.digest(z,"md5")};v=m.validate(z,spec);ok("VALID_OS_ZIP",v["valid"]);ok("MISSING_REJECTED",not m.validate(d/"missing",spec)["valid"])
  bad=d/"bad.zip";bad.write_bytes(b"x"*z.stat().st_size);ok("SAME_SIZE_CORRUPT_REJECTED",not m.validate(bad,spec)["valid"]);q=m.quarantine(bad,d,"bad md5");ok("QUARANTINE_MOVES",q and Path(q).exists() and not bad.exists());ok("RANGE_START",m.range_start("bytes 10-19/100")==10);ok("RANGE_INVALID",m.range_start("x") is None)
 osr={"state":"resolved","selected":{"open_uprn":{"fileName":"open.zip","url":"https://x/open","size":10,"md5":"0"*32},"uprn_topographic_area":{"fileName":"lids.zip","url":"https://x/lids","size":20,"md5":"1"*32}}};ons={"state":"runtime_validation_passed","release_label":"May 2026","products":[{"product_id":"nsul","selected":{"id":"abc","title":"NSUL","size":30}},{"product_id":"onsud","selected":{"id":"def","title":"ONSUD","size":40}}]}
 ps=m.packages(osr,ons);ok("PACKAGE_COUNT",len(ps)==4);ok("OS_UPRN",ps[0]["package_id"]=="os_open_uprn");ok("OS_LIDS",ps[1]["package_id"]=="os_lids_uprn_topographic_area");ok("NSUL",ps[2]["package_id"]=="nsul");ok("ONSUD",ps[3]["package_id"]=="onsud");ok("NSUL_URL",ps[2]["download_url"].endswith("/abc/data"));ok("ONSUD_URL",ps[3]["download_url"].endswith("/def/data"));ok("OS_MD5",ps[0]["expected_md5"]=="0"*32);ok("ONS_MD5_OPTIONAL",ps[2]["expected_md5"] is None)
 try:m.packages({"state":"blocked"},ons);blocked=False
 except ValueError:blocked=True
 ok("BLOCK_UNRESOLVED_OS",blocked)
 e=24;z={"schema_version":2,"suite":"full_release_hydration_manifest","tests_expected":e,"tests_passed":len(c),"tests_failed":e-len(c),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};print(json.dumps(z,indent=2));return 0 if len(c)==e else 2
if __name__=="__main__":raise SystemExit(main())
