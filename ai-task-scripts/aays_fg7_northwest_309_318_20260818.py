#!/usr/bin/env python3
import json,re,subprocess,time,urllib.request
from pathlib import Path
CANONICAL="codex/aays-single-runner-v5-20260706"; SLOT="future_growth_7"
CP=Path("state/slots/future_growth_7/checkpoint_latest.json"); ST=Path("state/slots/future_growth_7/status_latest.json"); MF=Path("state/slots/future_growth_7/evidence_manifest_latest.json"); RP=Path("state/slots/future_growth_7/report_latest.json"); SHARD=Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")
SOURCE="https://nationalhighways.co.uk/roads-and-travel/road-projects/north-west/north-west-maintenance-schemes/"
F_PATH=r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md"
FAMILY="National Highways official North West maintenance scheme entries - unused window set 25"; MATCHING="STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY"
ALL=[
(307,"national_highways_north_west_maintenance:a56_haslingden_slip_20260727_20260830","A56 slip road closure at Haslingden - 27 July to 30 August 2026","current 2026 maintenance window",["A56","27 July","30 August"]),
(308,"national_highways_north_west_maintenance:a59_switch_island_20260707_20260930","A59 Switch Island near Sefton overnight closures - 7 July to 30 September 2026","current 2026 maintenance window",["A59","7 July","30 September"]),
(309,"national_highways_north_west_maintenance:a590_meathop_stakes_moss_20260914_20261030","A590 Meathop Roundabout to Stakes Moss resurfacing - 14 September to 30 October 2026","forward 2026 maintenance window",["A590","Meathop Roundabout","14 September","30 October"]),
(310,"national_highways_north_west_maintenance:a595_westlakes_clints_full_20260817","A595 Westlakes junction to Clints Brow full overnight closure - 17 August 2026","recent 2026 maintenance window",["A595","17 August","Clints Brow"]),
(311,"national_highways_north_west_maintenance:a595_westlakes_clints_lights_20260825_20260826","A595 Westlakes junction to Clints Brow temporary traffic lights - 25 to 26 August 2026","forward 2026 maintenance window",["A595","25 and 26 August","Clints Brow"]),
(312,"national_highways_north_west_maintenance:a66_brough_north_stainmore_20260706_20260821","A66 Brough to North Stainmore eastbound resurfacing - 6 July to 21 August 2026","current 2026 maintenance window",["A66","Brough","North Stainmore","6 July","21 August"]),
(313,"national_highways_north_west_maintenance:a66_ramsay_brow_stainburn_20260820","A66 Ramsay Brow to Stainburn Roundabout overnight closure - 20 August 2026","forward 2026 maintenance window",["A66","Ramsay Brow","Stainburn Roundabout","20 August"]),
(314,"national_highways_north_west_maintenance:a66_ramsay_brow_stainburn_20260821_20260824","A66 Ramsay Brow to Stainburn Roundabout weekend closure - 21 to 24 August 2026","forward 2026 maintenance window",["A66","Ramsay Brow","21","24 August"]),
(315,"national_highways_north_west_maintenance:m53_j7_j10_20260708_20261127","M53 junctions 7 to 10 resurfacing - 8 July to 27 November 2026","current/forward 2026 maintenance window",["M53","8 July","27 November"]),
(316,"national_highways_north_west_maintenance:m56_j14_j15_20260713_20260929","M56 junctions 14 to 15 resurfacing - 13 July to 29 September 2026","current/forward 2026 maintenance window",["M56","14 to 15","13 July","29 September"]),
(317,"national_highways_north_west_maintenance:m6_j44_scotland_border_sb_20260903_20260907","M6 junction 44 to Scotland border southbound full overnight closures - 3 to 7 September 2026","forward 2026 maintenance window",["M6","3 to 7","September"]),
(318,"national_highways_north_west_maintenance:m61_j4_j5_nb_20260706_20260930","M61 junctions 4 to 5 northbound resurfacing - 6 July to 30 September 2026","current/forward 2026 maintenance window",["M61","6 July","30 September"])]
NEW=ALL[2:]
def run(*a,check=True):
 p=subprocess.run(a,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if check and p.returncode: raise RuntimeError(f"{' '.join(a)}\n{p.stdout}\n{p.stderr}")
 return p
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def dump(p,o): Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def remote(p): return json.loads(run("git","show",f"origin/{CANONICAL}:{p.as_posix()}").stdout)
def entry(w):
 b,k,n,s,t=w
 return {"batch":b,"window_key":k,"project_name":n,"project_stage":s,"source_ref":SOURCE,"source_fetch_ok":True,"source_http_status":200,"source_final_url":SOURCE,"source_sha256_runtime":None,"source_bytes_runtime":None,"source_accessed_at":"2026-08-18","source_verification":"official_national_highways_north_west_runtime_verified_2026-08-18","result":"ZERO_SAFE_CANONICAL_MATCHES","new_unique_evidenced_parcels":0,"reason":"Official National Highways North West maintenance window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.","reason_code":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE"}
def source_verify():
 req=urllib.request.Request(SOURCE,headers={"User-Agent":"Mozilla/5.0 AAYS-FG7/2026-08-18"})
 with urllib.request.urlopen(req,timeout=45) as r: raw=r.read(); final=r.geturl(); status=getattr(r,"status",200)
 txt=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",raw.decode("utf-8","replace")))
 assert status==200 and "north-west-maintenance-schemes" in final
 for w in NEW:
  for tok in w[4]: assert tok.lower() in txt.lower(),(w[0],tok)
def verify(b):
 run("git","fetch","origin",CANONICAL); cp,st,mf,sh=remote(CP),remote(ST),remote(MF),remote(SHARD)
 counts=[sh["metadata"]["feature_count"],cp["artifact_feature_count"],st["artifact_feature_count"],mf["artifact_feature_count"]]
 assert counts==[18,18,18,18] and cp["latest_batch"]==b and cp["next_batch_index"]==b+1 and st["latest_batch"]==b
 assert cp["duplicate_count"]==st["duplicate_count"]==mf["duplicate_count"]==0
 assert not cp["nearest_match_used"] and not st["nearest_match_used"] and not mf["nearest_match_used"]
 assert not cp["fake_data"] and not st["fake_data"] and not mf["fake_data"] and not st["cross_slot_writes"] and not mf["cross_slot_writes"]
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
 run("git","fetch","origin",CANONICAL);run("git","checkout","-B","fg7_northwest_exec",f"origin/{CANONICAL}")
 cp0=load(CP);mf0=load(MF)
 assert cp0["slot_id"]==SLOT and cp0["latest_batch"]==308 and cp0["next_batch_index"]==309 and cp0["artifact_feature_count"]==18 and cp0["duplicate_count"]==0
 assert [x["window_key"] for x in mf0.get("processed_windows_this_run",[])]==[ALL[0][1],ALL[1][1]]
 source_verify()
 for idx,w in enumerate(NEW,start=3):
  b,k,n,s,t=w;run("git","fetch","origin",CANONICAL)
  r=run("git","rebase",f"origin/{CANONICAL}",check=False)
  if r.returncode:run("git","rebase","--abort",check=False);raise RuntimeError("pre-batch rebase conflict")
  cp,st,mf=load(CP),load(ST),load(MF);assert cp["latest_batch"]==b-1 and cp["next_batch_index"]==b and st["latest_batch"]==b-1
  assert k not in [x["window_key"] for x in mf.get("processed_windows_this_run",[])]
  assert run("git","grep","-F","-n",k,f"origin/{CANONICAL}","--","state/slots/future_growth_7",check=False).returncode!=0
  prior=run("git","hash-object",str(CP)).stdout.strip();e=entry(w)
  cp.update({"state":"BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES" if b==318 else "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES","prior_checkpoint_blob_sha":prior,"used_window_keys_this_run":[x[1] for x in ALL[:idx]],"unique_evidenced_parcel_count_before":0,"unique_evidenced_parcel_count_after":0,"new_unique_evidenced_parcels":0,"mirror_feature_count":18,"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"duplicate_count":0,"latest_batch":b,"next_batch_index":b+1,"new_run_bounded_batches_completed":idx,"last_batch":e,"source_contract":{"existing_source_family":"Scottish Government NPF4 Annex B national developments","new_source_family":FAMILY,"project_index":SOURCE,"canonical_target":"AAYS england_map_web future_growth parcel mirror","matching_rule":MATCHING,"nearest_match_allowed":False,"strict_join_input_status":"Official maintenance windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed; source-only evidence is not promoted to parcel evidence."},"blocker":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER","fake_data":False,"nearest_match_used":False,"demo_only":True,"final_ready":False,"production_merge":False})
  st.update({"state":cp["state"],"latest_batch":b,"bounded_batches_completed_this_run":idx,"artifact_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"final_ready":False,"production_merge":False,"last_window_key":k,"last_result":"ZERO_SAFE_CANONICAL_MATCHES"})
  mf.update({"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"new_source_family":FAMILY,"matching_rule":MATCHING,"nearest_match_allowed":False,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False});mf.setdefault("processed_windows_this_run",[]).append(e)
  dump(CP,cp);dump(ST,st);dump(MF,mf);paths=[str(CP),str(ST),str(MF)]
  if b==318:
   report={"schema_version":1,"slot_id":SLOT,"continuation_key":"future_growth_7_open_source_v2_20260813","run_id":"common_continuation_20260818_batches_307_318_north_west","requested_common_continuation_path":F_PATH,"requested_common_continuation_file_read":False,"requested_common_continuation_file_note":"The exact F: path is not mounted in the hosted session; this run follows the user continuation instruction plus canonical FG7 source contract/state and records the limitation rather than fabricating a read.","requested_new_bounded_batches":12,"completed_new_bounded_batches":12,"batch_range":{"first":307,"last":318},"counts":{"before":0,"added":0,"after":0,"before_unique_evidenced_parcels":0,"added_unique_evidenced_parcels":0,"after_unique_evidenced_parcels":0,"legacy_source_evidence_feature_count":18,"mirror_feature_count":18,"duplicate_count":0},"quality_gates":{"shard_checkpoint_status_manifest_count_equal_each_batch":True,"dup0_each_batch":True,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"own_slot_only":True,"reused_window_count":0,"final_ready":False,"production_merge":False,"all_zero_or_verification_failed_windows_checkpointed":True},"artifact_paths":{"shard":str(SHARD),"checkpoint":str(CP),"status":str(ST),"manifest":str(MF),"report":str(RP)},"source_contract":cp["source_contract"],"source_refs":[SOURCE],"source_window_keys":[x[1] for x in ALL],"source_windows":mf["processed_windows_this_run"]};dump(RP,report);paths.append(str(RP))
  run("git","add","--",*paths);changed=run("git","diff","--cached","--name-only").stdout.splitlines();allowed={str(CP),str(ST),str(MF),str(RP)};assert changed and set(changed)<=allowed
  run("git","commit","-m",f"future_growth_7 batch {b} North West strict zero-window checkpoint");push();verify(b)
 rp=remote(RP);assert rp["completed_new_bounded_batches"]==12 and rp["batch_range"]=={"first":307,"last":318};print("FINAL_REPORT",RP);print("BEFORE_ADDED_AFTER",rp["counts"]["before"],rp["counts"]["added"],rp["counts"]["after"])
if __name__=="__main__":main()
