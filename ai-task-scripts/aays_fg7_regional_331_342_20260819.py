#!/usr/bin/env python3
import hashlib, html, json, re, subprocess, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANONICAL="codex/aays-single-runner-v5-20260706"
SLOT="future_growth_7"
CONT="future_growth_7_open_source_v2_20260813"
CP=Path("state/slots/future_growth_7/checkpoint_latest.json")
ST=Path("state/slots/future_growth_7/status_latest.json")
MF=Path("state/slots/future_growth_7/evidence_manifest_latest.json")
RP=Path("state/slots/future_growth_7/report_latest.json")
SHARD=Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")
F_PATH=r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md"
MATCHING="STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY"

SOURCES={
 "em":"https://nationalhighways.co.uk/roads-and-travel/road-projects/east-midlands/east-midlands-maintenance-schemes/",
 "se":"https://nationalhighways.co.uk/roads-and-travel/road-projects/south-east/south-east-maintenance-schemes/",
}
FAMILY="National Highways official East Midlands and South East maintenance entries - unused window set 28"

BATCHES=[
 (331,"em","national_highways_east_midlands_maintenance:a38_coxbench_nb_20260604_05_10_11_12","A38 Coxbench junction northbound slip-road surveys - 4, 5, 10, 11 and 12 June 2026","verified 2026 maintenance window",["Coxbench junction","4, 5, 10, 11 and 12 June","northbound exit and entry slip roads"]),
 (332,"em","national_highways_east_midlands_maintenance:a38_somercotes_sb_20260602_08_09_20260703","A38 Somercotes junction southbound slip-road surveys - 2, 8, 9 June and 3 July 2026","verified 2026 maintenance window",["Somercotes junction","2, 8, 9 June and 3 July","southbound exit and entry slip roads"]),
 (333,"em","national_highways_east_midlands_maintenance:a38_alfreton_sb_20260604_16","A38 Alfreton junction southbound slip-road surveys - 4 and 16 June 2026","verified 2026 maintenance window",["Alfreton junction","4 and 16 June","southbound exit and entry slip roads"]),
 (334,"em","national_highways_east_midlands_maintenance:a38_alfreton_nb_20260605_12_15","A38 Alfreton junction northbound slip-road surveys - 5, 12 and 15 June 2026","verified 2026 maintenance window",["Alfreton junction","5, 12 and 15 June","northbound exit and entry slip roads"]),
 (335,"em","national_highways_east_midlands_maintenance:a38_clovernook_sb_20260615_18_20260702","A38 Clovernook junction southbound slip-road surveys - 15, 18 June and 2 July 2026","verified 2026 maintenance window",["Clovernook junction","15, 18 June and 2 July","southbound exit and entry slip roads"]),
 (336,"em","national_highways_east_midlands_maintenance:a38_clovernook_nb_20260616_17_20260701","A38 Clovernook junction northbound slip-road surveys - 16, 17 June and 1 July 2026","verified 2026 maintenance window",["Clovernook junction","16, 17 June and 1 July","northbound exit and entry slip roads"]),
 (337,"em","national_highways_east_midlands_maintenance:a38_ripley_sb_20260625_26","A38 Ripley junction southbound slip-road surveys - 25 and 26 June 2026","verified 2026 maintenance window",["Ripley junction","25 and 26 June","southbound exit and entry slip roads"]),
 (338,"em","national_highways_east_midlands_maintenance:a5_clifton_upon_dunsmore_sb_20260518_20260626","A5 Clifton Upon Dunsmore southbound drainage closure - 18 May to 26 June 2026","verified 2026 maintenance window",["18 May","26 June","Rugby Road to Rugby Truckstop (southbound)","full closure"]),
 (339,"se","national_highways_se_maintenance:ash_m27_j1_a31_20260810_20260814","Ash dieback works - M27 westbound junction 1 to A31 Upper Canterton - 10 to 14 August 2026","recent 2026 maintenance window",["10 to 14 August","M27 westbound junction 1 to A31 Upper Canterton","Closed overnight"]),
 (340,"se","national_highways_se_maintenance:ash_a31_boundary_ashley_heath_20260814","Ash dieback works - A31 Boundary Lane to Ashley Heath - 14 August 2026","recent 2026 maintenance window",["14 August","A31 southbound from Boundary Lane roundabout to Ashley Heath roundabout","Closed overnight"]),
 (341,"se","national_highways_se_maintenance:ash_m3_j3_exit_20260821","Ash dieback works - M3 southbound junction 3 exit slip - 21 August 2026","forward 2026 maintenance window",["21 August","M3 southbound junction 3 exit slip","Closed overnight"]),
 (342,"se","national_highways_se_maintenance:a23_bolney_nb_20260803_20260808","A23 Bolney Flyover northbound closure - 3 to 8 August 2026","verified 2026 maintenance window",["3 to 8 August","A23 northbound carriageway","A2300 Hickstead Interchange to Bolney","Closed overnight"]),
]


def run(*a,check=True):
 p=subprocess.run(a,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if check and p.returncode: raise RuntimeError(f"{' '.join(a)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
 return p

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def dump(p,o): Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def remote(p): return json.loads(run("git","show",f"origin/{CANONICAL}:{p.as_posix()}").stdout)

def norm(s):
 s=html.unescape(s)
 s=re.sub(r"<script\b[^>]*>.*?</script>"," ",s,flags=re.I|re.S)
 s=re.sub(r"<style\b[^>]*>.*?</style>"," ",s,flags=re.I|re.S)
 s=re.sub(r"<[^>]+>"," ",s)
 s=s.replace("–","-").replace("—","-").replace("‑","-")
 return re.sub(r"\s+"," ",s).strip().lower()

def fetch_source(code):
 url=SOURCES[code]
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 AAYS-FG7-Regional/2026-08-18","Accept":"text/html,application/xhtml+xml"})
 with urllib.request.urlopen(req,timeout=60) as r:
  raw=r.read(); final=r.geturl(); status=getattr(r,"status",200)
 if status!=200: raise RuntimeError(f"SOURCE_HTTP:{code}:{status}")
 if f"/{'east-midlands' if code=='em' else 'south-east'}/" not in final: raise RuntimeError(f"SOURCE_URL:{code}:{final}")
 txt=norm(raw.decode("utf-8","replace"))
 for b,c,k,n,s,toks in BATCHES:
  if c!=code: continue
  for tok in toks:
   if norm(tok) not in txt: raise RuntimeError(f"SOURCE_TOKEN_MISSING:{code}:{b}:{tok!r}:BYTES={len(raw)}:FINAL={final}")
 return {"url":url,"final_url":final,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"accessed_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}

def entry(w,src):
 b,c,k,n,s,t=w
 return {"batch":b,"window_key":k,"project_name":n,"project_stage":s,"source_ref":src["url"],"source_fetch_ok":True,"source_http_status":200,"source_final_url":src["final_url"],"source_sha256_runtime":src["sha256"],"source_bytes_runtime":src["bytes"],"source_accessed_at":src["accessed_at"],"source_verification":f"official_national_highways_{c}_runtime_verified_2026-08-18","result":"ZERO_SAFE_CANONICAL_MATCHES","new_unique_evidenced_parcels":0,"reason":"Official National Highways maintenance window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.","reason_code":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE"}

def verify(b):
 run("git","fetch","origin",CANONICAL)
 cp,st,mf,sh=remote(CP),remote(ST),remote(MF),remote(SHARD)
 sc=len(sh.get("features") or []); mc=(sh.get("metadata") or {}).get("feature_count")
 counts=[sc,cp.get("artifact_feature_count"),st.get("artifact_feature_count"),mf.get("artifact_feature_count")]
 assert sc==mc==18 and counts==[18,18,18,18],counts
 assert cp.get("latest_batch")==b and cp.get("next_batch_index")==b+1 and st.get("latest_batch")==b
 assert cp.get("duplicate_count")==st.get("duplicate_count")==mf.get("duplicate_count")==0
 assert cp.get("unique_evidenced_parcel_count_after")==st.get("unique_evidenced_parcel_count")==mf.get("unique_evidenced_parcel_count")==0
 assert cp.get("nearest_match_used") is False and st.get("nearest_match_used") is False and mf.get("nearest_match_used") is False
 assert cp.get("fake_data") is False and st.get("fake_data") is False and mf.get("fake_data") is False
 assert st.get("cross_slot_writes") is False and mf.get("cross_slot_writes") is False
 print("READBACK_PASS",b,counts,"dup=0")

def push():
 for _ in range(30):
  p=run("git","push","origin",f"HEAD:{CANONICAL}",check=False)
  if p.returncode==0:return
  run("git","fetch","origin",CANONICAL)
  r=run("git","rebase",f"origin/{CANONICAL}",check=False)
  if r.returncode:
   run("git","rebase","--abort",check=False); raise RuntimeError("overlapping/FG7 rebase conflict; fail closed")
  time.sleep(1)
 raise RuntimeError("push retry limit")

def main():
 run("git","config","user.name","AAYS FG7 strict runner");run("git","config","user.email","aays-fg7@users.noreply.github.com")
 if run("git","rev-parse","--is-shallow-repository").stdout.strip()=="true":run("git","fetch","--unshallow","origin")
 run("git","fetch","origin",CANONICAL);run("git","checkout","-B","fg7_regional_exec",f"origin/{CANONICAL}")
 cp0,st0,mf0,sh0=load(CP),load(ST),load(MF),load(SHARD)
 assert cp0.get("slot_id")==st0.get("slot_id")==mf0.get("slot_id")==SLOT
 assert cp0.get("latest_batch")==330 and cp0.get("next_batch_index")==331 and cp0.get("artifact_feature_count")==18 and cp0.get("duplicate_count")==0
 assert len(sh0.get("features") or [])==18 and cp0.get("nearest_match_used") is False and cp0.get("fake_data") is False
 sources={code:fetch_source(code) for code in SOURCES}
 source_contract={"existing_source_family":"Scottish Government NPF4 Annex B national developments","new_source_family":FAMILY,"project_index":[SOURCES["em"],SOURCES["se"]],"canonical_target":"AAYS england_map_web future_growth parcel mirror","matching_rule":MATCHING,"nearest_match_allowed":False,"strict_join_input_status":"Official maintenance windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed; source-only evidence is not promoted to parcel evidence."}
 for idx,w in enumerate(BATCHES,start=1):
  b,c,k,n,s,t=w
  run("git","fetch","origin",CANONICAL)
  r=run("git","rebase",f"origin/{CANONICAL}",check=False)
  if r.returncode:run("git","rebase","--abort",check=False);raise RuntimeError("pre-batch rebase conflict")
  cp,st,mf=load(CP),load(ST),load(MF)
  assert cp.get("latest_batch")==b-1 and cp.get("next_batch_index")==b and st.get("latest_batch")==b-1
  hist=run("git","log","-S",k,"--format=%H","--","state/slots/future_growth_7",check=False).stdout.strip()
  assert not hist,("reused window",k,hist)
  e=entry(w,sources[c]);prior=run("git","hash-object",str(CP)).stdout.strip()
  cp.update({"state":"BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES" if b==342 else "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES","prior_checkpoint_blob_sha":prior,"used_window_keys_this_run":[x[2] for x in BATCHES[:idx]],"unique_evidenced_parcel_count_before":0,"unique_evidenced_parcel_count_after":0,"new_unique_evidenced_parcels":0,"mirror_feature_count":18,"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"duplicate_count":0,"latest_batch":b,"next_batch_index":b+1,"new_run_bounded_batches_completed":idx,"last_batch":e,"source_contract":source_contract,"blocker":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER","fake_data":False,"nearest_match_used":False,"demo_only":True,"final_ready":False,"production_merge":False})
  st.update({"state":cp["state"],"latest_batch":b,"bounded_batches_completed_this_run":idx,"artifact_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"final_ready":False,"production_merge":False,"last_window_key":k,"last_result":"ZERO_SAFE_CANONICAL_MATCHES"})
  mf.update({"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"new_source_family":FAMILY,"matching_rule":MATCHING,"nearest_match_allowed":False,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"processed_windows_this_run":([] if idx==1 else mf.get("processed_windows_this_run",[]))})
  mf["processed_windows_this_run"].append(e)
  dump(CP,cp);dump(ST,st);dump(MF,mf);paths=[str(CP),str(ST),str(MF)]
  if b==342:
   report={"schema_version":1,"slot_id":SLOT,"continuation_key":CONT,"run_id":"common_continuation_20260819_batches_331_342_regional_unused","requested_common_continuation_path":F_PATH,"requested_common_continuation_file_read":False,"requested_common_continuation_file_note":"The exact F: path is not mounted in the hosted session, is absent from /mnt/data, and no matching canonical repository file was found. The exact file is therefore not claimed as read; this run follows the current user instruction and canonical future_growth_7 state/source contract.","requested_new_bounded_batches":12,"completed_new_bounded_batches":12,"batch_range":{"first":331,"last":342},"counts":{"before":0,"added":0,"after":0,"before_unique_evidenced_parcels":0,"added_unique_evidenced_parcels":0,"after_unique_evidenced_parcels":0,"legacy_source_evidence_feature_count":18,"mirror_feature_count":18,"duplicate_count":0},"quality_gates":{"shard_checkpoint_status_manifest_count_equal_each_batch":True,"dup0_each_batch":True,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"own_slot_only":True,"reused_window_count":0,"final_ready":False,"production_merge":False,"all_zero_or_verification_failed_windows_checkpointed":True},"artifact_paths":{"shard":str(SHARD),"checkpoint":str(CP),"status":str(ST),"manifest":str(MF),"report":str(RP)},"source_contract":source_contract,"source_refs":[SOURCES["em"],SOURCES["se"]],"source_runtime":sources,"source_window_keys":[x[2] for x in BATCHES],"source_windows":mf["processed_windows_this_run"],"next_batch_index":343,"blocker":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER"}
   dump(RP,report);paths.append(str(RP))
  run("git","add","--",*paths)
  changed=run("git","diff","--cached","--name-only").stdout.splitlines();allowed={str(CP),str(ST),str(MF),str(RP)}
  assert changed and set(changed)<=allowed,changed
  run("git","commit","-m",f"future_growth_7 batch {b} regional strict zero-window checkpoint")
  push();verify(b)
 rp=remote(RP);assert rp.get("completed_new_bounded_batches")==12 and rp.get("batch_range")=={"first":331,"last":342} and rp.get("quality_gates",{}).get("reused_window_count")==0
 print("FINAL_REPORT",RP);print("BEFORE_ADDED_AFTER",rp["counts"]["before"],rp["counts"]["added"],rp["counts"]["after"])

if __name__=="__main__":main()
