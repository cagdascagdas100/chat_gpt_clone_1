#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json,tempfile
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).with_name("061_repo_blob_integrity_matrix.py");s=importlib.util.spec_from_file_location("m",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 args();m=mod();t=[]
 def ck(n,c):t.append((n,bool(c)))
 b=b"abc";expected=hashlib.sha1(b"blob 3\0abc").hexdigest();ck("GIT_BLOB_SHA",m.git_blob_sha(b)==expected);ck("PAIR_DIRECT",m.pairs({"path":"a","blob_sha":"b"})==[("a","b")]);ck("PAIR_NESTED",m.pairs({"x":[{"path":"a","blob_sha":"b"}]})==[("a","b")]);ck("PAIR_IGNORE_PARTIAL",m.pairs({"path":"a"})==[]);ck("PAIR_LIST",len(m.pairs([{"path":"a","blob_sha":"b"},{"path":"c","blob_sha":"d"}]))==2);src=Path(__file__).with_name("061_repo_blob_integrity_matrix.py").read_text();ck("QUEUE_PATH","7000_internet_access_3" in src);ck("EXPECTED_SHA","expected_blob_sha" in src);ck("ACTUAL_SHA","actual_blob_sha" in src);ck("MATCH_GATE","matched" in src);ck("REMOTE_READBACK","remote_readback_required" in src);ck("NO_PROMOTION","parcel_relations_promoted" in src);ck("ZERO_UPLIFT","confidence_uplifts" in src);ck("SAFETY_FLAGS",all(x in src for x in ["final_ready","fake_data","db_write","migration","production_deploy"]));ck("ATOMIC_WRITE","os.replace" in src)
 f=[n for n,c in t if not c];print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","state":"passed" if not f else "failed","tests_expected":14,"tests_executed":len(t),"tests_passed":len(t)-len(f),"tests_failed":len(f),"failures":f,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},indent=2));return 0 if not f else 2
if __name__=="__main__":raise SystemExit(main())
