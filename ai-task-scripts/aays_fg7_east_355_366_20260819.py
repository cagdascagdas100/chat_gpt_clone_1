#!/usr/bin/env python3
import hashlib, html, json, re, subprocess, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANONICAL="codex/aays-single-runner-v5-20260706"
SLOT="future_growth_7"
CONT="future_growth_7_open_source_v2_20260813"
MATCHING="STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY"
SOURCE="https://nationalhighways.co.uk/roads-and-travel/road-projects/east/east-maintenance-schemes/"
F_PATH=r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md"
FAMILY="National Highways official East maintenance entries - unused window set 32"
CP=Path("state/slots/future_growth_7/checkpoint_latest.json")
ST=Path("state/slots/future_growth_7/status_latest.json")
MF=Path("state/slots/future_growth_7/evidence_manifest_latest.json")
RP=Path("state/slots/future_growth_7/report_latest.json")
SHARD=Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")

BATCHES=[
 (355,"national_highways_east_maintenance:a1_nb_j17_a47_20260803_28","A1 northbound junction 17 to A1/A47 drainage and resurfacing - 3 to 28 August 2026",["3 to 28 August","A1 northbound between junction 17 and the A1/A47 junction","Closed overnight"]),
 (356,"national_highways_east_maintenance:a1m_j9_nb_exit_power_20260817_20260922","A1(M) junction 9 northbound exit slip power cable replacement - 17 August to 22 September 2026",["Monday 17 August to Tuesday 22 September 2026","A1(M) junction 9 northbound exit slip","Hard shoulder and one lane northbound also closed"]),
 (357,"national_highways_east_maintenance:a120_dunmow_eb_lane_20260803_12_14_17","A120 Dunmow eastbound weather station lane closures - 3, 12-14 and 17 August 2026",["Monday 3 August","Wednesday 12 to Friday 14 August","Monday 17 August","A120 eastbound between Dunmow West Interchange and Dunmow South Interchange"]),
 (358,"national_highways_east_maintenance:a120_dunmow_eb_full_20260805_06","A120 Dunmow eastbound full closure - 5 and 6 August 2026",["Wednesday 5 August and Thursday 6 August","A120 eastbound between Dunmow West Interchange and Dunmow South Interchange","Closed overnight"]),
 (359,"national_highways_east_maintenance:a120_horsley_harwich_wb_20260807_09","A120 Horsley Cross to Harwich Road westbound closure - 7 to 9 August 2026",["Friday 7 August","Saturday 8 August","Sunday 9 August","A120 westbound between Horsley Cross Roundabout and Harwich Road Roundabout"]),
 (360,"national_highways_east_maintenance:a120_dunmow_south_wb_lane_20260817","A120 Dunmow South westbound lane closure - 17 August 2026",["Monday 17 August","A120 westbound at Dunmow South Interchange"]),
 (361,"national_highways_east_maintenance:a120_horsley_cross_wb_lane_20260827","A120 Horsley Cross westbound lane closure - 27 August 2026",["Thursday 27 August","A120 westbound at Horsley Cross Roundabout"]),
 (362,"national_highways_east_maintenance:a14_j21_j22_eb_weekend_20260807_10","A14 junction 21 to 22 eastbound weekend closure - 7 to 10 August 2026",["9pm Friday 7 August to 5am Monday 10 August","A14 eastbound between junctions 21 and 22"]),
 (363,"national_highways_east_maintenance:a14_j21_j22_eb_weekend_20260821_24","A14 junction 21 to 22 eastbound weekend closure - 21 to 24 August 2026",["9pm Friday 21 August to 5am Monday 24 August","A14 eastbound between junctions 21 and 22"]),
 (364,"national_highways_east_maintenance:a14_tollbar_wb_j22_j13_20260806_12","A14 Tollbar Lane westbound junction 22 to 13 maintenance - 6 to 12 August 2026",["Thursday 6 to Wednesday 12 August","A14 westbound between junctions 22 (Brampton) and junction 13 (Thrapston)","Closed overnight"]),
 (365,"national_highways_east_maintenance:a47_dogsthorpe_welland_both_20260810_28","A47 Dogsthorpe Interchange to Welland Roundabout both directions - 10 to 28 August 2026",["10 - 28 August","A47 both directions, between junction 20 (Dogsthorpe Interchange) and Welland Roundabout","Closed overnight"]),
 (366,"national_highways_east_maintenance:a47_j17_eye_green_20260706_20260807","A47 junction 17 to Eye Green Roundabout resurfacing - 6 July to 7 August 2026",["Work begins Monday 6 July","A47 between Soke Parkway Roundabout and Dogsthorpe Roundabout","Monday to Friday overnight"]),
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

def fetch_source():
 req=urllib.request.Request(SOURCE,headers={"User-Agent":"Mozilla/5.0 AAYS-FG7-East-355-366/2026-08-19","Accept":"text/html,application/xhtml+xml"})
 with urllib.request.urlopen(req,timeout=60) as r:
  raw=r.read(); final=r.geturl(); status=getattr(r,"status",200)
 if status!=200: raise RuntimeError(f"EAST_SOURCE_HTTP:{status}")
 if "/east/" not in final: raise RuntimeError(f"EAST_SOURCE_URL:{final}")
 txt=norm(raw.decode("utf-8","replace"))
 for b,k,n,toks in BATCHES:
  for tok in toks:
   if norm(tok) not in txt: raise RuntimeError(f"EAST_SOURCE_TOKEN_MISSING:{b}:{tok!r}:BYTES={len(raw)}:FINAL={final}")
 return {"url":SOURCE,"final_url":final,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"accessed_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}

def entry(w,src):
 b,k,n,t=w
 return {"batch":b,"window_key":k,"project_name":n,"project_stage":"verified 2026 maintenance window","source_ref":SOURCE,"source_fetch_ok":True,"source_http_status":200,"source_final_url":src["final_url"],"source_sha256_runtime":src["sha256"],"source_bytes_runtime":src["bytes"],"source_accessed_at":src["accessed_at"],"source_verification":f"official_national_highways_east_runtime_verified_{src['accessed_at'][:10]}","result":"ZERO_SAFE_CANONICAL_MATCHES","new_unique_evidenced_parcels":0,"reason":"Official National Highways East maintenance window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.","reason_code":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE"}

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
 if b==366:
  rp=remote(RP); assert rp.get("completed_new_bounded_batches")==12 and rp.get("counts",{}).get("before")==0 and rp.get("counts",{}).get("added")==0 and rp.get("counts",{}).get("after")==0
 print("READBACK_PASS",b,counts,"dup=0")

def main():
 if len({w[1] for w in BATCHES})!=12: raise RuntimeError("duplicate window key inside batch list")
 run("git","config","user.name","AAYS FG7 strict runner"); run("git","config","user.email","aays-fg7@users.noreply.github.com")
 if run("git","rev-parse","--is-shallow-repository").stdout.strip()=="true": run("git","fetch","--unshallow","origin")
 run("git","fetch","origin",CANONICAL); run("git","checkout","-B","fg7_east_exec",f"origin/{CANONICAL}")
 cp0,st0,mf0,sh0=load(CP),load(ST),load(MF),load(SHARD)
 assert cp0.get("slot_id")==st0.get("slot_id")==mf0.get("slot_id")==SLOT
 assert cp0.get("latest_batch")==354 and cp0.get("next_batch_index")==355
 assert cp0.get("artifact_feature_count")==18 and cp0.get("duplicate_count")==0 and len(sh0.get("features") or [])==18
 assert cp0.get("nearest_match_used") is False and cp0.get("fake_data") is False and st0.get("cross_slot_writes") is False
 src=fetch_source()
 contract={"existing_source_family":"Scottish Government NPF4 Annex B national developments","new_source_family":FAMILY,"project_index":[SOURCE],"canonical_target":"AAYS england_map_web future_growth parcel mirror","matching_rule":MATCHING,"nearest_match_allowed":False,"strict_join_input_status":"Official maintenance windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed; source-only evidence is not promoted to parcel evidence."}
 for idx,w in enumerate(BATCHES,start=1):
  b,k,n,t=w
  run("git","fetch","origin",CANONICAL)
  r=run("git","rebase",f"origin/{CANONICAL}",check=False)
  if r.returncode: run("git","rebase","--abort",check=False); raise RuntimeError("pre-batch rebase conflict")
  cp,st,mf=load(CP),load(ST),load(MF)
  assert cp.get("latest_batch")==b-1 and cp.get("next_batch_index")==b and st.get("latest_batch")==b-1
  hist=run("git","log","-S",k,"--format=%H","--","state/slots/future_growth_7",check=False).stdout.strip()
  if hist: raise RuntimeError(f"REUSED_WINDOW:{k}:{hist}")
  e=entry(w,src); prior=run("git","hash-object",str(CP)).stdout.strip(); final=b==366
  state="BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES" if final else "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES"
  cp.update({"state":state,"prior_checkpoint_blob_sha":prior,"used_window_keys_this_run":[x[1] for x in BATCHES[:idx]],"unique_evidenced_parcel_count_before":0,"unique_evidenced_parcel_count_after":0,"new_unique_evidenced_parcels":0,"mirror_feature_count":18,"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"duplicate_count":0,"latest_batch":b,"next_batch_index":b+1,"new_run_bounded_batches_completed":idx,"last_batch":e,"source_contract":contract,"blocker":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER","fake_data":False,"nearest_match_used":False,"demo_only":True,"final_ready":False,"production_merge":False})
  st.update({"state":state,"latest_batch":b,"bounded_batches_completed_this_run":idx,"artifact_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"final_ready":False,"production_merge":False,"last_window_key":k,"last_result":"ZERO_SAFE_CANONICAL_MATCHES"})
  mf.update({"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"new_source_family":FAMILY,"matching_rule":MATCHING,"nearest_match_allowed":False,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"processed_windows_this_run":[] if idx==1 else mf.get("processed_windows_this_run",[])})
  mf["processed_windows_this_run"].append(e)
  dump(CP,cp); dump(ST,st); dump(MF,mf); paths=[str(CP),str(ST),str(MF)]
  if final:
   report={"schema_version":1,"slot_id":SLOT,"continuation_key":CONT,"run_id":"common_continuation_20260819_batches_355_366_east_unused","requested_common_continuation_path":F_PATH,"requested_common_continuation_file_read":False,"requested_common_continuation_file_note":"The exact F: path is not mounted in the hosted session, is absent from /mnt/data, and no matching canonical repository file was found. The exact file is therefore not claimed as read; this run follows the current user instruction and canonical future_growth_7 state/source contract.","requested_new_bounded_batches":12,"completed_new_bounded_batches":12,"batch_range":{"first":355,"last":366},"counts":{"before":0,"added":0,"after":0,"before_unique_evidenced_parcels":0,"added_unique_evidenced_parcels":0,"after_unique_evidenced_parcels":0,"legacy_source_evidence_feature_count":18,"mirror_feature_count":18,"duplicate_count":0},"quality_gates":{"shard_checkpoint_status_manifest_count_equal_each_batch":True,"dup0_each_batch":True,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"own_slot_only":True,"reused_window_count":0,"final_ready":False,"production_merge":False,"all_zero_or_verification_failed_windows_checkpointed":True},"artifact_paths":{"shard":SHARD.as_posix(),"checkpoint":CP.as_posix(),"status":ST.as_posix(),"manifest":MF.as_posix(),"report":RP.as_posix()},"source_contract":contract,"source_refs":[SOURCE],"source_runtime":src,"source_window_keys":[x[1] for x in BATCHES],"source_windows":[entry(x,src) for x in BATCHES]}
   dump(RP,report); paths.append(str(RP))
  changed=set(run("git","diff","--name-only").stdout.splitlines()); allowed={CP.as_posix(),ST.as_posix(),MF.as_posix(),RP.as_posix()}
  if not changed or not changed.issubset(allowed): raise RuntimeError(f"CROSS_SLOT_OR_UNEXPECTED_CHANGE:{sorted(changed)}")
  run("git","add",*paths); run("git","commit","-m",f"FG7 strict batch {b}: {k}"); push(); verify(b)
 print("FINAL_REPORT",RP.as_posix()); print("BEFORE_ADDED_AFTER",0,0,0)

if __name__=="__main__": main()
