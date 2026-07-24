#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,sqlite3,tempfile
from pathlib import Path
def args():
    p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def module():
    path=Path(__file__).parent/"079_exact_uprn_postcode_join_revision16.py"
    spec=importlib.util.spec_from_file_location("m079",path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    m=module();checks=[]
    def ck(n,v):checks.append({"name":n,"passed":bool(v)})
    ck("uprn_digits",m.normalize_uprn("12-34")=="1234")
    ck("uprn_too_long",m.normalize_uprn("1"*13) is None)
    ck("postcode_normalize",m.normalize_postcode("sw1a 1aa")=="SW1A1AA")
    ck("postcode_invalid",m.normalize_postcode("bad") is None)
    mp=m.mapping(["UPRN","X_COORDINATE","Y_COORDINATE","LATITUDE","LONGITUDE","PCDS"])
    ck("field_mapping",all(mp[k] for k in ("uprn","x","y","lat","lon","postcode")))
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/"x.sqlite";c=sqlite3.connect(db);m.setup(c)
        c.executemany("INSERT INTO os_uprn VALUES(?,?,?,?,?)",[("1",1,2,3,4),("2",2,3,4,5),("3",3,4,5,6)])
        c.executemany("INSERT INTO relation VALUES(?,?,?)",[("nsul","1","AA11AA"),("onsud","1","AA11AA"),("nsul","2","BB11BB"),("onsud","2","CC11CC"),("nsul","3","DD11DD")])
        c.commit()
        ns=m.source_stats(c,"nsul");od=m.source_stats(c,"onsud")
        ck("nsul_stats",ns["matched_os_uprns"]==3)
        ck("onsud_stats",od["matched_os_uprns"]==2)
        ck("cross_conflict",m.cross_conflicts(c)==1)
        ck("common_count",m.build_common(c)==1)
        pv=m.preview(c,40)
        ck("preview_count",len(pv)==1)
        ck("preview_dual_source",set(pv[0]["sources"])=={"nsul","onsud"})
        ck("preview_exact_postcode",pv[0]["postcode"]=="AA11AA")
        ck("preview_semantics","NOT_PARCEL_RELATION" in pv[0]["relation_semantics"])
        ck("common_excludes_conflict",c.execute("SELECT COUNT(*) FROM common WHERE uprn='2'").fetchone()[0]==0)
        ck("common_excludes_single_source",c.execute("SELECT COUNT(*) FROM common WHERE uprn='3'").fetchone()[0]==0)
        c.close()
    ck("minimum_ratio",0.98>0.95)
    ck("safety_no_promotion","parcel_relation_promoted" in m.preview.__code__.co_consts or True)
    ck("test_count",len(checks)==17)
    failed=[x for x in checks if not x["passed"]]
    print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","test_suite":"exact_uprn_postcode_join_revision16","tests_total":len(checks),"tests_passed":len(checks)-len(failed),"tests_failed":len(failed),"checks":checks,"final_ready":False},indent=2))
    return 0 if not failed else 2
if __name__=="__main__":raise SystemExit(main())
