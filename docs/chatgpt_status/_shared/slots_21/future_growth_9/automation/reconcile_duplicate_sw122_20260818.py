#!/usr/bin/env python3
import json, subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO=Path.cwd()/"canonical"
BRANCH="codex/aays-single-runner-v5-20260706"
BATCH_ROOT=Path("AAYS/england_map_web/data/future_growth/shards/future_growth_9_batches")
STATE=Path("docs/chatgpt_status/_shared/slots_21/future_growth_9")
CP=STATE/"checkpoint_latest.json"; ST=STATE/"status_latest.json"; MF=Path("state/slots/future_growth_9/evidence_manifest_latest.json")
TASK=STATE/"current_task_latest.json"; REC=STATE/"recovery_latest.json"
DUP_REF="SW/122"; DUP_ENTITY=1712272; KEEP_BATCH=37; DROP_BATCH=74
ALLOWED=("AAYS/england_map_web/data/future_growth/shards/future_growth_9_batches/","docs/chatgpt_status/_shared/slots_21/future_growth_9/","state/slots/future_growth_9/")

def run(*a,capture=False):
 p=subprocess.run(list(a),cwd=REPO,text=True,check=True,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None); return p.stdout if capture else ""
def load(p): return json.loads((REPO/p).read_text(encoding="utf-8"))
def dump(p,o):
 q=REPO/p; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(o,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
def scan():
 rec=[]
 latest=REPO/"AAYS/england_map_web/data/future_growth/shards/future_growth_9_latest.geojson"
 paths=sorted((REPO/BATCH_ROOT).glob("**/*.geojson"))+([latest] if latest.exists() else [])
 for p in paths:
  o=json.loads(p.read_text(encoding="utf-8"))
  for f in o.get("features",[]):
   pr=f.get("properties") or {}; rec.append((str(pr.get("source_feature_id")),str(pr.get("planning_data_entity")),str(p.relative_to(REPO))))
 return rec
def counts(rec): return len(rec),len({r for r,_,_ in rec if r not in ("None","")}),len({e for _,e,_ in rec if e not in ("None","")}),len({(r,e) for r,e,_ in rec})
def changed():
 out=run("git","status","--porcelain",capture=True); ps=[]
 for line in out.splitlines():
  if not line.strip(): continue
  p=line[3:]; ps.append(p)
  if not p.startswith(ALLOWED): raise RuntimeError("WRITE_OWNERSHIP_VIOLATION "+p)
 return ps

def main():
 run("git","config","user.name","github-actions[bot]"); run("git","config","user.email","41898282+github-actions[bot]@users.noreply.github.com")
 run("git","pull","--rebase","origin",BRANCH)
 rec=scan(); c=counts(rec)
 dup=[x for x in rec if x[0]==DUP_REF and x[1]==str(DUP_ENTITY)]
 if c!=(91,90,90,90) or len(dup)!=2 or not any("batch_37.geojson" in x[2] for x in dup) or not any("batch_74.geojson" in x[2] for x in dup):
  raise RuntimeError(f"RECONCILIATION_PRECONDITION_FAILED counts={c} dup={dup}")
 drop=None
 for p in sorted((REPO/BATCH_ROOT).glob("**/batch_74.geojson")):
  o=json.loads(p.read_text(encoding="utf-8")); fs=o.get("features",[])
  if len(fs)==1 and (fs[0].get("properties") or {}).get("source_feature_id")==DUP_REF and (fs[0].get("properties") or {}).get("planning_data_entity")==DUP_ENTITY: drop=p; break
 if drop is None: raise RuntimeError("DROP_BATCH_NOT_FOUND")
 for p in sorted((REPO/BATCH_ROOT).glob("**/*.geojson")):
  o=json.loads(p.read_text(encoding="utf-8")); m=o.get("metadata") or {}; bi=int(m.get("batch_index",-1))
  if bi<74: continue
  if bi==74:
   o["features"]=[]; m["feature_count_added"]=0; m["feature_count_after"]=int(m["feature_count_before"]); m["source_result"]="DUPLICATE_CANDIDATE_SKIPPED_NOT_EMITTED"; m["duplicate_candidate_skipped"]=True; m["historical_duplicate_reconciled"]=True
  else:
   if "feature_count_before" in m: m["feature_count_before"]=int(m["feature_count_before"])-1
   if "feature_count_after" in m: m["feature_count_after"]=int(m["feature_count_after"])-1
   m["count_reconciled_after_historical_duplicate_batch_74"]=True
  m["duplicate_count"]=0; o["metadata"]=m; p.write_text(json.dumps(o,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
 now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
 for path in (CP,ST,MF,REC,TASK):
  o=load(path)
  if "feature_count_before" in o and int(o["feature_count_before"])>=74: o["feature_count_before"]=int(o["feature_count_before"])-1
  if "feature_count_after" in o: o["feature_count_after"]=int(o["feature_count_after"])-1
  if "logical_mirror_feature_count" in o: o["logical_mirror_feature_count"]=int(o["logical_mirror_feature_count"])-1
  if "already_processed_ids_count" in o: o["already_processed_ids_count"]=int(o["already_processed_ids_count"])-1
  if path==TASK and "new_records_added" in o: o["new_records_added"]=max(0,int(o["new_records_added"])-1)
  dist=o.get("evidence_distribution")
  if isinstance(dist,dict) and "direct_project_or_site" in dist: dist["direct_project_or_site"]=int(dist["direct_project_or_site"])-1
  cls=o.get("classification_counts")
  if isinstance(cls,dict) and "direct_project_or_site" in cls: cls["direct_project_or_site"]=int(cls["direct_project_or_site"])-1
  if isinstance(o.get("readback_expected"),dict): o["readback_expected"]={"shard":90,"checkpoint":90,"status":90,"manifest":90,"dup":0}
  o["duplicate_count"]=0; o["updated_at"]=now; o["identity_reconciliation"]={"reference":DUP_REF,"entity":DUP_ENTITY,"kept_batch":KEEP_BATCH,"emptied_duplicate_batch":DROP_BATCH,"logical_feature_count_before":91,"unique_count_before":90,"feature_count_after_reconciliation":90,"nearest_match_used":False,"fake_data":False}
  dump(path,o)
 report=STATE/"reports"/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_identity_reconciliation.json")
 dump(report,{"slot_id":"future_growth_9","state":"HISTORICAL_EXACT_DUPLICATE_RECONCILED","duplicate":{"reference":DUP_REF,"entity":DUP_ENTITY,"kept_batch":37,"emptied_batch":74},"counts":{"logical_before":91,"unique_before":90,"after":90},"processed_windows_changed":False,"next_unused_window":91,"nearest_match_used":False,"fake_data":False,"duplicate_count_after":0,"finished_at":now})
 ps=changed(); run("git","add","--",*ps); run("git","commit","-m","aays: reconcile FG9 historical duplicate SW/122 batch 74")
 run("git","push","origin",f"HEAD:{BRANCH}")
 run("git","fetch","origin",BRANCH)
 rec2=scan(); c2=counts(rec2)
 if c2!=(90,90,90,90): raise RuntimeError(f"RECONCILIATION_READBACK_FAILED counts={c2}")
 cp=load(CP); st=load(ST); mf=load(MF)
 vals=(cp.get("feature_count_after"),st.get("feature_count_after"),mf.get("feature_count_after"),cp.get("duplicate_count"),st.get("duplicate_count"),mf.get("duplicate_count"))
 if vals!=(90,90,90,0,0,0): raise RuntimeError(f"STATE_READBACK_FAILED {vals}")
 print(json.dumps({"ok":True,"reconciled":DUP_REF,"entity":DUP_ENTITY,"before_logical":91,"before_unique":90,"after":90,"next_window":cp.get("next_unused_window")},ensure_ascii=False))
if __name__=="__main__": main()
