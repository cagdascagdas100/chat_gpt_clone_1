#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,sys,tempfile
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);return p.parse_args()
def mod():
 p=Path(__file__).resolve().parent/"093_runtime_watchdog_supervisor.py";s=importlib.util.spec_from_file_location("wd",p)
 if not s or not s.loader:raise ImportError(p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 w=mod();c=[]
 def ok(n,v):
  if not v:raise AssertionError(n)
  c.append(n)
 with tempfile.TemporaryDirectory() as td:
  r=Path(td);(r/"docs").mkdir();(r/"england_map_web").mkdir();h1=r/"docs/h.json";h2=r/"england_map_web/h.json"
  ok("utc_now_iso","+" in w.utc_now() or w.utc_now().endswith("Z"));ok("repo_root_explicit",w.repo_root(r)==r.resolve());ok("path_state_missing",not w.path_state(r/"x")["exists"])
  f=r/"a";f.write_bytes(b"abc");ok("path_state_file_size",w.path_state(f)["bytes"]==3)
  d=r/"d";d.mkdir();(d/"a").write_bytes(b"12");(d/"b").write_bytes(b"345");ok("path_state_directory_size",w.path_state(d)["bytes"]==5)
  ignored=d/"heartbeat.json";before=w.snapshot([d],[ignored]);w.atomic_json(ignored,{"x":1});after=w.snapshot([d],[ignored]);ok("heartbeat_replace_does_not_change_directory_snapshot",before==after)
  tmp=d/"heartbeat.json.any.tmp";tmp.write_bytes(b"ignored");ok("heartbeat_temp_file_ignored",w.snapshot([d],[ignored])==after);tmp.unlink()
  j=r/"j";w.atomic_json(j,{"ok":True});ok("atomic_json_roundtrip",json.loads(j.read_text())["ok"])
  fast=w.supervise(command=[sys.executable,"-S","-c","print('ok')"],cwd=r,step_name="fast",hard_timeout_seconds=30,stall_timeout_seconds=30,watch_paths=[],heartbeat_paths=[h1,h2],poll_seconds=.05,heartbeat_seconds=.05)
  ok("fast_process_passes",fast["state"]=="passed" and fast["exit_code"]==0);ok("heartbeat_written_twice",h1.exists() and h2.exists());ok("heartbeat_safety_flags",json.loads(h1.read_text())["final_ready"] is False);ok("stdout_tail_captured","ok" in fast["stdout_tail"]);ok("actual_heartbeat_cycles_recorded",fast["heartbeat_cycles_succeeded"]>=1);ok("heartbeat_path_write_count_recorded",fast["heartbeat_path_writes_succeeded"]>=2);ok("final_heartbeat_matches_return",json.loads(h1.read_text())["state"]==fast["state"])
  spam="import time\nend=time.time()+5\nwhile time.time()<end:\n print('spam',flush=True);time.sleep(.05)\n"
  hard=w.supervise(command=[sys.executable,"-S","-c",spam],cwd=r,step_name="log_spam",hard_timeout_seconds=5,stall_timeout_seconds=1,watch_paths=[],heartbeat_paths=[h1],poll_seconds=.05,heartbeat_seconds=.05)
  ok("log_spam_does_not_mask_stall",hard["state"]=="blocked" and hard["timeout_kind"]=="stall_timeout");ok("timeout_has_termination",isinstance(hard["termination"],dict))
  hbdir=r/"hbdir";hbdir.mkdir();hb=hbdir/"runtime_watchdog.json"
  selfmask=w.supervise(command=[sys.executable,"-S","-c","import time;time.sleep(5)"],cwd=r,step_name="selfmask",hard_timeout_seconds=5,stall_timeout_seconds=1,watch_paths=[hbdir],heartbeat_paths=[hb],poll_seconds=.05,heartbeat_seconds=.05)
  ok("heartbeat_self_write_does_not_mask_stall",selfmask["state"]=="blocked" and selfmask["timeout_kind"]=="stall_timeout")
  progress=r/"p";code=f"import pathlib,time\np=pathlib.Path({str(progress)!r})\nfor i in range(5):\n p.write_text(str(i));time.sleep(.2)\n"
  moving=w.supervise(command=[sys.executable,"-S","-c",code],cwd=r,step_name="moving",hard_timeout_seconds=45,stall_timeout_seconds=30,watch_paths=[progress],heartbeat_paths=[h1],poll_seconds=.05,heartbeat_seconds=.05)
  ok("watched_progress_prevents_stall",moving["state"]=="passed");ok("observed_path_reported",any(x["path"]==str(progress) for x in moving["observed_paths"]))
  bad=w.supervise(command=[sys.executable,"-S","-c","raise SystemExit(7)"],cwd=r,step_name="bad",hard_timeout_seconds=30,stall_timeout_seconds=30,watch_paths=[],heartbeat_paths=[h1],poll_seconds=.05,heartbeat_seconds=.05)
  ok("nonzero_exit_blocks",bad["state"]=="blocked" and bad["exit_code"]==7);ok("single_child_only_flag",bad["single_child_only"] and bad["parallel_runner"] is False)
  badparent=r/"not_a_directory";badparent.write_text("x");badheartbeat=badparent/"h.json"
  hb_fail=w.supervise(command=[sys.executable,"-S","-c","import time;time.sleep(5)"],cwd=r,step_name="heartbeat_fail",hard_timeout_seconds=5,stall_timeout_seconds=5,watch_paths=[],heartbeat_paths=[badheartbeat],poll_seconds=.05,heartbeat_seconds=.05)
  ok("heartbeat_failure_blocks_and_cleans_child",hb_fail["state"]=="blocked" and hb_fail["timeout_kind"]=="heartbeat_write_error" and isinstance(hb_fail["termination"],dict));ok("heartbeat_failure_recorded",len(hb_fail["heartbeat_write_errors"])>=1);ok("fallback_report_written",Path(hb_fail["fallback_report_path"]).exists())
  try:w.supervise(command=[],cwd=r,step_name="empty",hard_timeout_seconds=1,stall_timeout_seconds=1,watch_paths=[],heartbeat_paths=[h1])
  except ValueError:c.append("empty_command_rejected")
  else:raise AssertionError("empty")
  try:w.supervise(command=[sys.executable,"-S","-c","pass"],cwd=r,step_name="timeout",hard_timeout_seconds=0,stall_timeout_seconds=1,watch_paths=[],heartbeat_paths=[h1])
  except ValueError:c.append("nonpositive_timeout_rejected")
  else:raise AssertionError("timeout")
 e=27;z={"schema_version":3,"suite":"runtime_watchdog_supervisor","tests_expected":e,"tests_passed":len(c),"tests_failed":e-len(c),"checks":c,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};print(json.dumps(z,indent=2));return 0 if len(c)==e else 2
if __name__=="__main__":raise SystemExit(main())
