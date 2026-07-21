#!/usr/bin/env python3
from __future__ import annotations
import copy, importlib.util, json, subprocess, tempfile
from pathlib import Path
from typing import Any, Callable

MODULE_PATH=Path(__file__).with_name("044_execution_lock_audit.py")

def load()->Any:
    spec=importlib.util.spec_from_file_location("lock044",MODULE_PATH)
    if spec is None or spec.loader is None: raise RuntimeError("load failed")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def run(repo:Path,*args:str)->str:
    result=subprocess.run(["git","-C",str(repo),*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return result.stdout.strip()

def write(path:Path,text:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding="utf-8")

def expect_fail(fn:Callable[[],None])->None:
    try: fn()
    except Exception: return
    raise AssertionError("expected failure")

def setup(module:Any,root:Path)->tuple[dict[str,Any],Path,Path]:
    run(root,"init"); run(root,"config","user.email","test@example.invalid"); run(root,"config","user.name","Test")
    files={
      "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/automation/a.py":"print('a')\n",
      "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/automation/b.py":"print('b')\n",
      "england_map_web/data/program_layer_matrix/security.geojson":"{\"type\":\"FeatureCollection\",\"features\":[]}\n",
      "england_map_web/data/program_layer_matrix/internet.geojson":"{\"type\":\"FeatureCollection\",\"features\":[]}\n",
    }
    for path,text in files.items(): write(root/path,text)
    run(root,"add","."); run(root,"commit","-m","base")
    locked=[]
    for path in files:
        role="critical_script" if path.endswith(".py") else "canonical_source"
        locked.append({"path":path,"git_blob_sha":run(root,"rev-parse",f"HEAD:{path}"),"role":role})
    manifest={
      "slot_id":module.SLOT_ID,"row_partition":{"start":61523,"end":92283,"count":30761},
      "allowed_paths":list(module.ALLOWED_PATHS),"direct_push_forbidden":True,"single_shared_runner_only":True,
      "create_new_runner":False,"queue_submission":False,"auto_claim":False,"locked_blobs":locked,
      "fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False,
    }
    manifest_path=root/"manifest.json"; output=root/"out.json"; manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
    return manifest,manifest_path,output

def main()->int:
    module=load(); results=[]
    with tempfile.TemporaryDirectory() as temp:
      root=Path(temp); manifest,mp,out=setup(module,root)
      payload=module.audit(root,mp,out); assert payload["locked_blob_count"]==4; results.append("valid_lock")
      write(root/"unrelated.txt","x\n"); run(root,"add","unrelated.txt"); run(root,"commit","-m","unrelated")
      payload=module.audit(root,mp,out); assert payload["locked_blob_count"]==4; results.append("unrelated_head_move_allowed")
      critical=root/manifest["locked_blobs"][0]["path"]; critical.write_text("print('dirty')\n",encoding="utf-8")
      expect_fail(lambda:module.audit(root,mp,out)); results.append("dirty_critical_blocked")
      run(root,"checkout","--",manifest["locked_blobs"][0]["path"])
      critical.write_text("print('changed')\n",encoding="utf-8"); run(root,"add",manifest["locked_blobs"][0]["path"]); run(root,"commit","-m","critical")
      expect_fail(lambda:module.audit(root,mp,out)); results.append("critical_head_drift_blocked")
    base={
      "slot_id":module.SLOT_ID,"row_partition":{"start":61523,"end":92283,"count":30761},"allowed_paths":list(module.ALLOWED_PATHS),
      "direct_push_forbidden":True,"single_shared_runner_only":True,"create_new_runner":False,"queue_submission":False,"auto_claim":False,
      "locked_blobs":[
        {"path":module.ALLOWED_PATHS[0]+"/automation/a.py","git_blob_sha":"a"*40,"role":"script"},
        {"path":"england_map_web/data/program_layer_matrix/security.geojson","git_blob_sha":"b"*40,"role":"source"},
        {"path":"england_map_web/data/program_layer_matrix/internet.geojson","git_blob_sha":"c"*40,"role":"source"},
      ],"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False,
    }
    cases=[]
    def case(name:str,change:Callable[[dict[str,Any]],None])->None:
      value=copy.deepcopy(base); change(value); expect_fail(lambda:module.validate_manifest(value)); cases.append(name)
    case("wrong_slot",lambda x:x.update(slot_id="internet_access_2"))
    case("wrong_partition",lambda x:x["row_partition"].update(count=1))
    case("wrong_allowed",lambda x:x["allowed_paths"].pop())
    case("direct_push_guard",lambda x:x.update(direct_push_forbidden=False))
    case("single_runner_guard",lambda x:x.update(single_shared_runner_only=False))
    case("new_runner",lambda x:x.update(create_new_runner=True))
    case("queue_submission",lambda x:x.update(queue_submission=True))
    case("auto_claim",lambda x:x.update(auto_claim=True))
    case("truth_fake",lambda x:x.update(fake_data=True))
    case("truth_db",lambda x:x.update(db_write=True))
    case("truth_migration",lambda x:x.update(migration=True))
    case("truth_deploy",lambda x:x.update(production_deploy=True))
    case("truth_final",lambda x:x.update(final_ready=True))
    case("few_rows",lambda x:x.update(locked_blobs=x["locked_blobs"][:2]))
    case("bad_sha",lambda x:x["locked_blobs"][0].update(git_blob_sha="bad"))
    case("duplicate",lambda x:x["locked_blobs"].append(copy.deepcopy(x["locked_blobs"][0])))
    case("unsafe_path",lambda x:x["locked_blobs"][0].update(path="../x"))
    case("outside_scope",lambda x:x["locked_blobs"][0].update(path="docs/other.py"))
    case("missing_role",lambda x:x["locked_blobs"][0].update(role=""))
    results.extend(cases)
    clean=module.validate_manifest(copy.deepcopy(base)); assert len(clean["locked_blobs"])==3; results.append("valid_manifest")
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":x,"state":"PASS"} for x in results]},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
