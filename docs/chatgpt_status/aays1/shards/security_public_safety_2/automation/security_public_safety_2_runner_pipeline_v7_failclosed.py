from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

SLOT_ID='security_public_safety_2'; BRANCH='codex/aays-single-runner-v5-20260706'
IDS=[f'parcel_{n}' for n in range(30762,31062)]
V6='security_public_safety_2_pipeline_v6_receipt_latest.json'; V7='security_public_safety_2_pipeline_v7_receipt_latest.json'
V6_STATE='PIPELINE_V6_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK'; V7_STATE='PIPELINE_V7_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK'

def utc(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def readj(p:Path)->dict[str,Any]: return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p:Path)->str:
 d=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''): d.update(c)
 return d.hexdigest()
def pt(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
 except Exception:return None

def repo_root(explicit:str|None)->Path:
 c=[Path(x).expanduser() for x in (explicit,os.environ.get('AAYS_REPO_ROOT')) if x]
 for p in (Path.cwd(),Path(__file__).resolve().parent):
  try:
   r=subprocess.run(['git','-C',str(p),'rev-parse','--show-toplevel'],capture_output=True,text=True)
   if r.returncode==0 and r.stdout.strip():c.append(Path(r.stdout.strip()))
  except Exception:pass
 c+=list(Path(__file__).resolve().parents); seen=set()
 for p in c:
  try:p=p.resolve()
  except Exception:p=p.absolute()
  k=os.path.normcase(str(p))
  if k in seen:continue
  seen.add(k)
  if (p/'docs/chatgpt_status/aays1/shards/security_public_safety_2/automation').is_dir() and (p/'england_map_web/data/aays_18_slots/security_public_safety_2').is_dir():return p
 raise RuntimeError('AAYS_REPO_ROOT_NOT_RESOLVED')

def cmd(a:list[str],cwd:Path,env:dict[str,str],timeout:int)->dict[str,Any]:
 try:
  r=subprocess.run(a,cwd=str(cwd),env=env,text=True,capture_output=True,timeout=timeout)
  return {'command':a,'returncode':r.returncode,'stdout_tail':r.stdout[-4000:],'stderr_tail':r.stderr[-4000:],'pass':r.returncode==0,'timed_out':False}
 except subprocess.TimeoutExpired as e:
  o=e.stdout.decode(errors='replace') if isinstance(e.stdout,bytes) else (e.stdout or ''); q=e.stderr.decode(errors='replace') if isinstance(e.stderr,bytes) else (e.stderr or '')
  return {'command':a,'returncode':None,'stdout_tail':o[-4000:],'stderr_tail':q[-4000:],'pass':False,'timed_out':True,'error':'TIMEOUT'}
 except Exception as e:return {'command':a,'returncode':None,'stdout_tail':'','stderr_tail':f'{type(e).__name__}:{e}','pass':False,'timed_out':False,'error':'EXECUTION_EXCEPTION'}

def receipt_ok(p:dict[str,Any],started:datetime)->dict[str,Any]:
 g,c=pt(p.get('generated_at')),pt(p.get('completed_at'))
 x={'slot':p.get('slot_id')==SLOT_ID,'state':p.get('state')==V6_STATE,'pass':p.get('pass') is True,'exit_present':'exit_code' in p,'exit_zero':p.get('exit_code')==0,'fresh_generated':bool(g and g>=started),'fresh_completed':bool(c and c>=started),'business_present':'actual_business_rows_written' in p,'business_zero':p.get('actual_business_rows_written')==0,'fake_false':p.get('fake_data') is False,'final_false':p.get('final_ready') is False}
 return {'pass':all(x.values()),'checks':x,'passed':sum(x.values()),'total':len(x),'blocker':None if all(x.values()) else 'PIPELINE_V6_RECEIPT_NOT_FRESH_OR_EXACT'}

def artifacts_ok(repo:Path)->dict[str,Any]:
 o=repo/'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs'; w=repo/'england_map_web/data/aays_18_slots/security_public_safety_2'
 p={'json':o/'security_public_safety_2_hydrated_300_latest.json','csv':o/'security_public_safety_2_hydrated_300_latest.csv','geo':o/'security_public_safety_2_hydrated_300_latest.geojson','webjson':w/'hydrated_300_latest.json','html':w/'progress.html','accept':o/'security_public_safety_2_acceptance_latest.json'}
 x={f'{k}_exists':v.is_file() for k,v in p.items()}; d={}
 try:d=readj(p['json']) if p['json'].is_file() else {}
 except Exception:pass
 rows=d.get('rows') or []; ids=[str(r.get('parcel_id') or '') for r in rows]
 x|={'slot':d.get('slot_id')==SLOT_ID,'rows_300':len(rows)==300,'ids':ids==IDS,'canonical_300':int(d.get('canonical_rows') or -1)==300,'no_missing':all(r.get('candidate_status')!='CANONICAL_FEATURE_NOT_FOUND' for r in rows),'parity':(d.get('artifacts') or {}).get('parity_pass') is True,'area_proxy':d.get('output_semantics')=='AREA_LEVEL_PROXY','fake_false':d.get('fake_data') is False,'final_false':d.get('final_ready') is False,'json_equal':p['json'].is_file() and p['webjson'].is_file() and p['json'].read_bytes()==p['webjson'].read_bytes()}
 return {'pass':all(x.values()),'checks':x,'passed':sum(x.values()),'total':len(x),'blocker':None if all(x.values()) else 'FINAL_ARTIFACT_SET_INCOMPLETE_OR_INVALID'}

def fallback(blocker:str,n:int)->str:
 cand=''.join(f'<tr><td>{escape(i)}</td><td>INVALIDATED_OR_PENDING</td><td>0/4</td></tr>' for i in IDS[:3])
 return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="20"><title>Security/Public Safety Slot 2</title></head><body data-slot-id="{SLOT_ID}" data-final-ready="false" data-real-row-count="0" data-runtime-fail-closed="true"><h1>Security / Public Safety — Slot 2</h1><p><b>Runtime fail-closed:</b> {escape(blocker)}. {n} kısmi/stale artifact temizlendi; geçersiz veri webde gerçek satır olarak gösterilmez.</p><table><tr><th>Parsel</th><th>Durum</th><th>Doğruluk</th></tr>{cand}</table><p>actual_business_rows_written=0; fake_data=false; final_ready=false.</p></body></html>'''

def cleanup(repo:Path,blocker:str)->list[dict[str,Any]]:
 o=repo/'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs'; w=repo/'england_map_web/data/aays_18_slots/security_public_safety_2'
 names=[o/'security_public_safety_2_sample_candidates_latest.json',o/'security_public_safety_2_hydrated_300_latest.json',o/'security_public_safety_2_hydrated_300_latest.csv',o/'security_public_safety_2_hydrated_300_latest.geojson',o/'security_public_safety_2_acceptance_latest.json',o/'security_public_safety_2_pipeline_receipt_latest.json',o/'security_public_safety_2_source_bound_resume_receipt_latest.json',w/'sample_candidates_latest.json',w/'hydrated_300_latest.json']
 removed=[]
 for p in names:
  if p.is_file():removed.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size});p.unlink()
 w.mkdir(parents=True,exist_ok=True);(w/'progress.html').write_text(fallback(blocker,len(removed)),encoding='utf-8');return removed

def run(a:argparse.Namespace)->dict[str,Any]:
 repo=repo_root(a.repo_root); slot=a.slot_id or os.environ.get('AAYS_SLOT_ID') or ''; branch=a.target_branch or os.environ.get('AAYS_TARGET_BRANCH') or ''
 out=repo/'docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs';out.mkdir(parents=True,exist_ok=True);op=out/V7;v6=out/V6
 r={'schema_version':1,'slot_id':SLOT_ID,'pipeline_version':'7.0-failclosed-web-and-partial-cleanup','generated_at':utc(),'actual_business_rows_written':0,'fake_data':False,'final_ready':False}
 def finish(state,blocker,code):r.update(state=state,blocker=blocker,exit_code=code,completed_at=utc(),**{'pass':code==0});op.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');return r
 if slot!=SLOT_ID or branch!=BRANCH:return finish('BLOCKED_CONTRACT',f'slot={slot};branch={branch}',2)
 if v6.is_file():r['stale_v6_receipt_removed']={'path':str(v6),'sha256':sha(v6),'bytes':v6.stat().st_size};v6.unlink()
 env=os.environ.copy();env|={'AAYS_REPO_ROOT':str(repo),'AAYS_SLOT_ID':SLOT_ID,'AAYS_TARGET_BRANCH':BRANCH};started=datetime.now(timezone.utc)
 script=repo/'docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/security_public_safety_2_runner_pipeline_v6.py'
 c=[sys.executable,str(script),'--repo-root',str(repo),'--slot-id',SLOT_ID,'--target-branch',BRANCH,'--source-timeout',str(a.source_timeout),'--pipeline-timeout',str(a.pipeline_timeout),'--port',str(a.port),'--sample-timeout',str(a.sample_timeout),'--batch-timeout',str(a.batch_timeout),'--acceptance-timeout',str(a.acceptance_timeout),'--http-wait-timeout',str(a.http_wait_timeout)]
 z=cmd(c,repo,env,a.outer_timeout);r['pipeline_v6_command']=z
 if not z['pass'] or not v6.is_file():b='PIPELINE_V6_TIMEOUT' if z.get('timed_out') else 'PIPELINE_V6_NONZERO_OR_RECEIPT_MISSING';r['removed_partial_artifacts']=cleanup(repo,b);return finish('BLOCKED_PIPELINE_V6_EXECUTION_FAILCLOSED',b,3)
 try:p=readj(v6)
 except Exception as e:b=f'PIPELINE_V6_RECEIPT_READ:{type(e).__name__}:{e}';r['removed_partial_artifacts']=cleanup(repo,b);return finish('BLOCKED_PIPELINE_V6_RECEIPT_FAILCLOSED',b,4)
 q=receipt_ok(p,started);r['pipeline_v6_receipt']=p;r['pipeline_v6_validation']=q
 if not q['pass']:r['removed_partial_artifacts']=cleanup(repo,q['blocker']);return finish('BLOCKED_PIPELINE_V6_GATE_FAILCLOSED',q['blocker'],5)
 q=artifacts_ok(repo);r['final_artifact_validation']=q
 if not q['pass']:r['removed_partial_artifacts']=cleanup(repo,q['blocker']);return finish('BLOCKED_FINAL_ARTIFACT_GATE_FAILCLOSED',q['blocker'],6)
 return finish(V7_STATE,None,0)

def args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root');p.add_argument('--slot-id');p.add_argument('--target-branch');p.add_argument('--source-timeout',type=int,default=180);p.add_argument('--pipeline-timeout',type=int,default=5700);p.add_argument('--outer-timeout',type=int,default=6600);p.add_argument('--port',type=int,default=8012);p.add_argument('--sample-timeout',type=int,default=900);p.add_argument('--batch-timeout',type=int,default=3600);p.add_argument('--acceptance-timeout',type=int,default=300);p.add_argument('--http-wait-timeout',type=int,default=30);return p.parse_args()
if __name__=='__main__':
 x=run(args());print(json.dumps({'slot_id':SLOT_ID,'pipeline_version':'7.0-failclosed-web-and-partial-cleanup','state':x.get('state'),'pass':x.get('pass'),'exit_code':x.get('exit_code'),'actual_business_rows_written':0,'final_ready':False}));raise SystemExit(int(x.get('exit_code') or 0))
