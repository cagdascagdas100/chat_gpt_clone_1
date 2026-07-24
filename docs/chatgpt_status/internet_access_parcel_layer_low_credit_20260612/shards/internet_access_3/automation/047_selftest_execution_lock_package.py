#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,py_compile,subprocess,sys
from pathlib import Path

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--automation-root",required=True,type=Path);p.add_argument("--web-root",required=True,type=Path);a=p.parse_args()
    scripts=[a.automation_root/f for f in ("044_execution_lock_audit.py","045_selftest_execution_lock_audit.py","046_selftest_execution_lock_web_contract.py")]
    results=[]
    for s in scripts: py_compile.compile(str(s),doraise=True);results.append("compile_"+s.name)
    for cmd,name in (([sys.executable,str(scripts[1])],"audit_selftest"),([sys.executable,str(scripts[2]),"--web-root",str(a.web_root)],"web_selftest")):
        r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if r.returncode: raise RuntimeError(r.stderr or r.stdout)
        results.append(name)
    index=(a.web_root/"index.html").read_text(encoding="utf-8")
    required=("execution_lock_latest.json","EXACT_EXECUTION_LOCK_AUDIT","locked_blob_count","exact_execution_lock_pass")
    for token in required:
        if token not in index and token not in (a.web_root/"progress_latest.json").read_text(encoding="utf-8") and token not in (a.web_root/"runner_task_latest.json").read_text(encoding="utf-8"):
            raise AssertionError(token)
        results.append("wiring_"+token)
    print(json.dumps({"passed":len(results),"total":len(results),"results":results},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
