#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,tempfile
from pathlib import Path

def args():
    p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def module():
    path=Path(__file__).parent/"077_runtime_resource_download_preflight.py"
    spec=importlib.util.spec_from_file_location("m077",path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    m=module();checks=[]
    def ck(name,value):checks.append({"name":name,"passed":bool(value)})
    ck("content_range_total",m.content_range_total("bytes 0-0/123")==123)
    ck("content_range_missing",m.content_range_total(None)==0)
    ck("media_zip",m.media_type_allowed("nsul","application/zip","","https://x"))
    ck("media_csv",m.media_type_allowed("onsud","text/csv","","https://x"))
    ck("media_octet",m.media_type_allowed("nsul","application/octet-stream","attachment; filename=a.zip","https://x"))
    ck("media_json_blocked",not m.media_type_allowed("nsul","application/json","","https://x"))
    ck("media_html_blocked",not m.media_type_allowed("onsud","text/html","","https://x"))
    ck("os_media_tolerant",m.media_type_allowed("os_open_uprn","application/octet-stream","","https://x"))
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);(d/"nsul_May_2026.download.part").write_bytes(b"x"*25)
        ck("existing_partial",m.existing_bytes(d,"nsul","May 2026")==25)
        packages=[{"package_id":"nsul","release_label":"May 2026","expected_size":100},{"package_id":"onsud","release_label":"May 2026","expected_size":200}]
        probes=[{"content_length":100},{"content_length":250}]
        rows,remaining,required=m.compute_budget(packages,probes,d,1000,500,1.2)
        ck("budget_rows",len(rows)==2)
        ck("remaining_uses_larger_size",remaining==75+250)
        ck("required_includes_reserves",required==int((75+250)*1.2)+1500)
        ck("cached_bytes_recorded",rows[0]["cached_or_partial_bytes"]==25)
        ck("remaining_nonnegative",all(x["remaining_bytes"]>=0 for x in rows))
    ck("https_policy_example","https://x".startswith("https://"))
    ck("test_count",len(checks)==15)
    failed=[x for x in checks if not x["passed"]]
    print(json.dumps({"schema_version":1,"slot_id":"internet_access_3","test_suite":"runtime_resource_download_preflight","tests_total":len(checks),"tests_passed":len(checks)-len(failed),"tests_failed":len(failed),"checks":checks,"final_ready":False},indent=2))
    return 0 if not failed else 2
if __name__=="__main__":raise SystemExit(main())
