from __future__ import annotations
import copy, importlib.util, json, socket, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,filename):
 spec=importlib.util.spec_from_file_location(name,HERE/filename);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
resume=load("resume","security_public_safety_2_runner_pipeline_v3_resume_hardened.py")
pipeline_text=(HERE/"security_public_safety_2_runner_pipeline_v5.py").read_text()
ps_text=(HERE/"security_public_safety_2_runner_pipeline_v5.ps1").read_text()
cases=[]
def add(name,value):cases.append({"name":name,"pass":bool(value)})
with socket.socket() as sock:
 sock.bind(("127.0.0.1",0));busy=sock.getsockname()[1];chosen=resume.choose_port(busy);add("busy_port_fallback",chosen!=busy)
with socket.socket() as sock:
 sock.bind(("127.0.0.1",0));free=sock.getsockname()[1]
add("free_port_selected",resume.choose_port(free)==free)
timeout=resume.run_command([sys.executable,"-c","import time;time.sleep(2)"],Path.cwd(),dict(__import__("os").environ),1)
add("timeout_caught",timeout.get("timed_out") is True and timeout.get("pass") is False)
success=resume.run_command([sys.executable,"-c","print('ok')"],Path.cwd(),dict(__import__("os").environ),20)
add("success_command",success.get("pass") is True and success.get("returncode")==0)
start=datetime.now(timezone.utc)-timedelta(seconds=1)
valid={"slot_id":resume.SLOT_ID,"state":"PIPELINE_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK","exit_code":0,"generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"completed_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"steps":[{"name":"ACCEPTANCE_GATE","pass":True}],"actual_business_rows_written":0,"fake_data":False,"final_ready":False}
matrix=resume.validate_pipeline_receipt(valid,start)
for name,value in matrix["checks"].items():add("valid_"+name,value)
mutations=[
("wrong_slot","slot_id","other"),("wrong_state","state","BLOCKED"),("nonzero","exit_code",3),("fake","fake_data",True),("final","final_ready",True),("business","actual_business_rows_written",1)]
for name,key,value in mutations:
 payload=copy.deepcopy(valid);payload[key]=value;add(name+"_rejected",not resume.validate_pipeline_receipt(payload,start)["pass"])
old=copy.deepcopy(valid);old["generated_at"]=(start-timedelta(seconds=1)).isoformat().replace("+00:00","Z");add("stale_generated_rejected",not resume.validate_pipeline_receipt(old,start)["pass"])
old=copy.deepcopy(valid);old["completed_at"]=(start-timedelta(seconds=1)).isoformat().replace("+00:00","Z");add("stale_completed_rejected",not resume.validate_pipeline_receipt(old,start)["pass"])
missing=copy.deepcopy(valid);missing["steps"]=[];add("missing_acceptance_rejected",not resume.validate_pipeline_receipt(missing,start)["pass"])
failed=copy.deepcopy(valid);failed["steps"][0]["pass"]=False;add("failed_acceptance_rejected",not resume.validate_pipeline_receipt(failed,start)["pass"])
static={
"attestation_first":pipeline_text.find("LIVE_SOURCE_ATTESTATION")<pipeline_text.find("HARDENED_RESUME_PIPELINE"),
"attestation_gate":"LIVE_SOURCE_ATTESTATION_PASSED" in pipeline_text,
"resume_gate":"HARDENED_RESUME_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_READBACK" in pipeline_text,
"resolved_env_gate":"RESOLVED_ENV_MISSING" in pipeline_text,
"pipeline_receipt":"security_public_safety_2_pipeline_v5_receipt_latest.json" in pipeline_text,
"timeout_caught":"subprocess.TimeoutExpired" in pipeline_text,
"ps_slot_guard":"WRONG_SLOT" in ps_text,
"ps_branch_guard":"WRONG_BRANCH" in ps_text,
"ps_repo_root":"REPO_ROOT_NOT_RESOLVED" in ps_text,
"ps_no_git_push":"git push" not in ps_text.lower(),
"ps_no_git_commit":"git commit" not in ps_text.lower(),
"ps_no_runner_start":"start-process" not in ps_text.lower() and "new runner" not in ps_text.lower(),
}
for name,value in static.items():add("static_"+name,value)
payload={"schema_version":1,"slot_id":resume.SLOT_ID,"test_type":"PIPELINE_V5_TIMEOUT_SAFE_SELFTEST","cases":cases,"passed":sum(x["pass"] for x in cases),"total":len(cases),"pass":all(x["pass"] for x in cases),"actual_business_rows_written":0,"fake_data":False,"final_ready":False}
out=HERE.parent/"validation/security_public_safety_2_pipeline_v5_selftest_latest.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"passed":payload["passed"],"total":payload["total"],"pass":payload["pass"]}))
raise SystemExit(0 if payload["pass"] else 1)
