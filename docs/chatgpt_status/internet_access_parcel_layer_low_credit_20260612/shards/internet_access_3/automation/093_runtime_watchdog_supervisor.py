#!/usr/bin/env python3
"""Sequential watchdog for one child step of the existing canonical runner."""
from __future__ import annotations
import argparse,json,os,signal,subprocess,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Iterable
SLOT_ID="internet_access_3"
DEFAULT_RUNNER_OUTPUT="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/058_runtime_watchdog_latest.json"
DEFAULT_WEB_OUTPUT="england_map_web/data/aays_21_slots/internet_access_3/runtime_watchdog_latest.json"
def utc_now():return datetime.now(timezone.utc).isoformat()
def repo_root(x):
 if x:
  r=x.expanduser().resolve()
  if not (r/"docs").exists() or not (r/"england_map_web").exists():raise FileNotFoundError(r)
  return r
 for r in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (r/"docs").exists() and (r/"england_map_web").exists():return r
 raise FileNotFoundError("repository root")
def atomic_json(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=p.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def tail_text(p,n=12000):
 if not p.exists():return ""
 with p.open("rb") as h:s=h.seek(0,2);h.seek(max(0,s-n));return h.read().decode("utf-8",errors="replace")
def path_state(p):
 try:
  if p.is_file():
   s=p.stat();return {"path":str(p),"exists":True,"kind":"file","bytes":s.st_size,"mtime_ns":s.st_mtime_ns}
  if p.is_dir():
   total=count=0;newest=p.stat().st_mtime_ns
   for x in p.rglob("*"):
    try:
     if x.is_file():s=x.stat();total+=s.st_size;count+=1;newest=max(newest,s.st_mtime_ns)
    except (OSError,PermissionError):pass
   return {"path":str(p),"exists":True,"kind":"directory","bytes":total,"files":count,"mtime_ns":newest}
 except (OSError,PermissionError):pass
 return {"path":str(p),"exists":False,"kind":"missing","bytes":0,"mtime_ns":0}
def snapshot(ps:Iterable[Path]):return [path_state(p) for p in ps]
def terminate_tree(p,grace_seconds=10):
 a=[]
 if p.poll() is not None:return {"already_exited":True,"actions":a,"returncode":p.returncode}
 if os.name=="nt":
  try:r=subprocess.run(["taskkill","/PID",str(p.pid),"/T","/F"],capture_output=True,text=True,timeout=30,check=False);a.append("taskkill:"+str(r.returncode))
  except Exception as e:
   a.append("taskkill_error:"+type(e).__name__)
   try:p.kill();a.append("process_kill")
   except Exception as k:a.append("kill_error:"+type(k).__name__)
 else:
  try:os.killpg(p.pid,signal.SIGTERM);a.append("sigterm_process_group")
  except Exception as e:
   a.append("sigterm_error:"+type(e).__name__)
   try:p.terminate();a.append("process_terminate")
   except Exception:pass
  d=time.monotonic()+grace_seconds
  while p.poll() is None and time.monotonic()<d:time.sleep(.1)
  if p.poll() is None:
   try:os.killpg(p.pid,signal.SIGKILL);a.append("sigkill_process_group")
   except Exception:
    try:p.kill();a.append("process_kill")
    except Exception:pass
 try:p.wait(timeout=30)
 except Exception as e:a.append("wait_error:"+type(e).__name__)
 return {"already_exited":False,"actions":a,"returncode":p.returncode}
def _payload(name,cmd,pid,state,start,sm,last,lm,hard,stall,seen,index,total):
 n=time.monotonic()
 return {"schema_version":1,"slot_id":SLOT_ID,"state":state,"updated_at":utc_now(),"step_name":name,"step_index":index,"step_total":total,"pid":pid,"command":cmd,"started_at":start,"elapsed_seconds":round(n-sm,3),"last_progress_at":last,"seconds_since_progress":round(n-lm,3),"hard_timeout_seconds":hard,"stall_timeout_seconds":stall,"observed_paths":seen,"single_child_only":True,"new_runner":False,"parallel_runner":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
def supervise(*,command,cwd,step_name,hard_timeout_seconds,stall_timeout_seconds,watch_paths,heartbeat_paths,poll_seconds=5.,heartbeat_seconds=30.,step_index=None,step_total=None,environment=None):
 if not command or not all(isinstance(x,str) and x for x in command):raise ValueError("command")
 if hard_timeout_seconds<=0 or stall_timeout_seconds<=0:raise ValueError("timeout")
 stall_timeout_seconds=min(stall_timeout_seconds,hard_timeout_seconds)
 d=Path(tempfile.gettempdir())/"aays_internet_access_3_watchdog_logs";d.mkdir(parents=True,exist_ok=True)
 safe="".join(c if c.isalnum() or c in "._-" else "_" for c in step_name)[:100] or "step";out=d/(safe+".stdout.log");err=d/(safe+".stderr.log")
 kw={"cwd":cwd,"stdin":subprocess.DEVNULL,"text":False,"env":environment or os.environ.copy()}
 if os.name=="nt":kw["creationflags"]=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
 else:kw["start_new_session"]=True
 start=utc_now();sm=lm=time.monotonic();last=start;kind=term=None
 with out.open("wb") as oh,err.open("wb") as eh:
  p=subprocess.Popen(command,stdout=oh,stderr=eh,**kw);paths=[*watch_paths,out,err];prev=snapshot(paths);beat=sm
  while True:
   now=time.monotonic();cur=snapshot(paths)
   if cur!=prev:prev=cur;lm=now;last=utc_now()
   if now>=beat:
    x=_payload(step_name,command,p.pid,"running",start,sm,last,lm,hard_timeout_seconds,stall_timeout_seconds,cur,step_index,step_total)
    for hp in heartbeat_paths:atomic_json(hp,x)
    beat=now+max(1.,heartbeat_seconds)
   if p.poll() is not None:break
   if now-sm>hard_timeout_seconds:kind="hard_timeout";term=terminate_tree(p);break
   if now-lm>stall_timeout_seconds:kind="stall_timeout";term=terminate_tree(p);break
   time.sleep(max(.05,poll_seconds))
 end=utc_now();code=p.returncode if p.returncode is not None else -999;state="passed" if kind is None and code==0 else "blocked"
 r={"schema_version":1,"slot_id":SLOT_ID,"state":state,"step_name":step_name,"step_index":step_index,"step_total":step_total,"command":command,"pid":p.pid,"started_at":start,"ended_at":end,"elapsed_seconds":round(time.monotonic()-sm,3),"exit_code":code,"timeout_kind":kind,"hard_timeout_seconds":hard_timeout_seconds,"stall_timeout_seconds":stall_timeout_seconds,"last_progress_at":last,"seconds_since_progress_at_end":round(time.monotonic()-lm,3),"termination":term,"observed_paths":snapshot([*watch_paths,out,err]),"stdout_tail":tail_text(out),"stderr_tail":tail_text(err),"single_child_only":True,"new_runner":False,"parallel_runner":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 for hp in heartbeat_paths:atomic_json(hp,r)
 return r
def parse_args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--step-name",required=True);p.add_argument("--hard-timeout-seconds",type=int,required=True);p.add_argument("--stall-timeout-seconds",type=int,required=True);p.add_argument("--watch-path",action="append",default=[]);p.add_argument("--runner-output",default=DEFAULT_RUNNER_OUTPUT);p.add_argument("--web-output",default=DEFAULT_WEB_OUTPUT);p.add_argument("command",nargs=argparse.REMAINDER);return p.parse_args()
def main():
 o=parse_args();r=repo_root(o.repo_root);cmd=list(o.command)
 if cmd and cmd[0]=="--":cmd=cmd[1:]
 x=supervise(command=cmd,cwd=r,step_name=o.step_name,hard_timeout_seconds=o.hard_timeout_seconds,stall_timeout_seconds=o.stall_timeout_seconds,watch_paths=[(r/v).resolve() if not Path(v).is_absolute() else Path(v) for v in o.watch_path],heartbeat_paths=[r/o.runner_output,r/o.web_output]);print(json.dumps(x,ensure_ascii=False,indent=2));return 0 if x["state"]=="passed" else 2
if __name__=="__main__":raise SystemExit(main())
