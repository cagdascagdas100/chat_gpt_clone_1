#!/usr/bin/env python3
import hashlib,json,re,subprocess,time,urllib.request
from datetime import datetime, timezone
from pathlib import Path
CANONICAL="codex/aays-single-runner-v5-20260706"; SLOT="future_growth_7"
CP=Path("state/slots/future_growth_7/checkpoint_latest.json"); ST=Path("state/slots/future_growth_7/status_latest.json"); MF=Path("state/slots/future_growth_7/evidence_manifest_latest.json"); RP=Path("state/slots/future_growth_7/report_latest.json"); SHARD=Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")
SOURCE="https://nationalhighways.co.uk/roads-and-travel/road-projects/yorkshire-and-north-east/yorkshire-and-north-east-maintenance-schemes/"
F_PATH=r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md"
FAMILY="National Highways official Yorkshire and North East maintenance scheme entries - unused window set 26"
MATCHING="STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY"
BATCHES=[
(319,"national_highways_yorkshire_ne_maintenance:a1_berwick_lighting_20260511_20261031","A1 Berwick upon Tweed lighting renewal - 11 May to end of October 2026","current/forward 2026 maintenance window",["A1 Berwick upon Tweed lighting renewal","11 May","end of October 2026"]),
(320,"national_highways_yorkshire_ne_maintenance:a1_ripon_leeming_20260526_20260706","A1 northbound Ripon to Leeming Bar - 26 May to 6 July 2026","official 2026 maintenance window",["26 May to 6 July","Ripon to Leeming Bar"]),
(321,"national_highways_yorkshire_ne_maintenance:a1_leeming_catterick_20260706_20260801","A1 northbound Leeming Bar to Catterick - 6 July to 1 August 2026","recent 2026 maintenance window",["6 July to 1 August","Leeming Bar to Catterick"]),
(322,"national_highways_yorkshire_ne_maintenance:a1_redhouse_barnsdale_20260801_20260802","A1 Redhouse to Barnsdale Bar northbound closure - 1 to 2 August 2026","recent 2026 maintenance window",["1 to 2 August","Redhouse","Barnsdale Bar"]),
(323,"national_highways_yorkshire_ne_maintenance:a1m_j48_j46_sb_20260605_20260607","A1(M) southbound junctions 48 to 46 - 5 to 7 June 2026","official 2026 maintenance window",["5, 6 and 7 June","junctions 48","46"]),
(324,"national_highways_yorkshire_ne_maintenance:a1m_j48_j46_sb_20260608_20260705","A1(M) southbound junctions 48 to 46 - 8 June to early July 2026","official 2026 maintenance window",["8 June","early July","junctions 48 and 46"]),
(325,"national_highways_yorkshire_ne_maintenance:a1m_j43_j44_m1_20260620_20260627","M1/A1(M) junction 43-44 widening closures - 20 and 27 June 2026","official 2026 maintenance window",["20 and 27 June","J42 Selby Fork","J44 Bramham"]),
(326,"national_highways_yorkshire_ne_maintenance:a1m_j43_j44_m1_20260706_20260731","M1/A1(M) junction 43-44 widening closures - 6 to 31 July 2026","recent 2026 maintenance window",["6–31 July 2026","J42 to J44"]),
(327,"national_highways_yorkshire_ne_maintenance:a1m_lumley_thicks_20260724_20270531","A1(M) Lumley Thicks/Chester-le-Street bridge works - 24 July 2026 to Spring 2027","current/forward bridge works",["Lumley Thicks/Chester-le-Street bridge works","24 July 2026","Spring 2027"]),
(328,"national_highways_yorkshire_ne_maintenance:a19_redhill_bridge_20260505_20261130","A19 southbound Redhill bridge repairs - 5 May to November 2026","current 2026 bridge works",["A19 southbound Redhill bridge repairs","5 May","November 2026"]),
(329,"national_highways_yorkshire_ne_maintenance:a628_woodhead_cascade_20260810_20260812","A628 Woodhead Cascade full closure - 10 to 12 August 2026","recent 2026 maintenance window",["Monday 10 August","Wednesday 12 August","Woodhead Cascade"]),
(330,"national_highways_yorkshire_ne_maintenance:a63_m62_j38_led_20260810_20260914","A63/M62 junction 38 LED lighting upgrade - 10 August to 14 September 2026","current/forward 2026 maintenance window",["A63/M62 J38","10 August","14 September 2026"])]

def run(*a,check=True):
    p=subprocess.run(a,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and p.returncode: raise RuntimeError(f"{' '.join(a)}\n{p.stdout}\n{p.stderr}")
    return p

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def dump(p,o): Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def remote(p): return json.loads(run("git","show",f"origin/{CANONICAL}:{p.as_posix()}").stdout)

def source_verify():
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"Mozilla/5.0 AAYS-FG7/2026-08-18"})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read(); final=r.geturl(); status=getattr(r,"status",200)
    txt=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",raw.decode("utf-8","replace")))
    assert status==200 and "yorkshire-and-north-east-maintenance-schemes" in final
    low=txt.lower()
    for b,k,n,s,toks in BATCHES:
        for tok in toks: assert tok.lower() in low,(b,tok)
    return hashlib.sha256(raw).hexdigest(),len(raw),datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def entry(w,sha,nbytes,accessed):
    b,k,n,s,t=w
    return {"batch":b,"window_key":k,"project_name":n,"project_stage":s,"source_ref":SOURCE,"source_fetch_ok":True,"source_http_status":200,"source_final_url":SOURCE,"source_sha256_runtime":sha,"source_bytes_runtime":nbytes,"source_accessed_at":accessed,"source_verification":"official_national_highways_yorkshire_ne_runtime_verified_2026-08-18","result":"ZERO_SAFE_CANONICAL_MATCHES","new_unique_evidenced_parcels":0,"reason":"Official National Highways Yorkshire and North East maintenance window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.","reason_code":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE"}

def verify(b):
    run("git","fetch","origin",CANONICAL)
    cp,st,mf,sh=remote(CP),remote(ST),remote(MF),remote(SHARD)
    counts=[sh["metadata"]["feature_count"],cp["artifact_feature_count"],st["artifact_feature_count"],mf["artifact_feature_count"]]
    assert counts==[18,18,18,18]
    assert cp["latest_batch"]==b and cp["next_batch_index"]==b+1 and st["latest_batch"]==b
    assert cp["duplicate_count"]==st["duplicate_count"]==mf["duplicate_count"]==0
    assert not cp["nearest_match_used"] and not st["nearest_match_used"] and not mf["nearest_match_used"]
    assert not cp["fake_data"] and not st["fake_data"] and not mf["fake_data"]
    assert not st["cross_slot_writes"] and not mf["cross_slot_writes"]
    print("READBACK_PASS",b,counts,"dup=0")

def push():
    for _ in range(30):
        p=run("git","push","origin",f"HEAD:{CANONICAL}",check=False)
        if p.returncode==0:return
        run("git","fetch","origin",CANONICAL)
        r=run("git","rebase",f"origin/{CANONICAL}",check=False)
        if r.returncode:
            run("git","rebase","--abort",check=False)
            raise RuntimeError("overlapping/FG7 rebase conflict; fail closed")
        time.sleep(1)
    raise RuntimeError("push retry limit")

def main():
    run("git","config","user.name","AAYS FG7 strict runner"); run("git","config","user.email","aays-fg7@users.noreply.github.com")
    if run("git","rev-parse","--is-shallow-repository").stdout.strip()=="true": run("git","fetch","--unshallow","origin")
    run("git","fetch","origin",CANONICAL); run("git","checkout","-B","fg7_yne_exec",f"origin/{CANONICAL}")
    cp0=load(CP)
    assert cp0["slot_id"]==SLOT and cp0["latest_batch"]==318 and cp0["next_batch_index"]==319 and cp0["artifact_feature_count"]==18 and cp0["duplicate_count"]==0
    sha,nbytes,accessed=source_verify()
    for idx,w in enumerate(BATCHES,start=1):
        b,k,n,s,t=w
        run("git","fetch","origin",CANONICAL)
        r=run("git","rebase",f"origin/{CANONICAL}",check=False)
        if r.returncode:
            run("git","rebase","--abort",check=False); raise RuntimeError("pre-batch rebase conflict")
        cp,st,mf=load(CP),load(ST),load(MF)
        assert cp["latest_batch"]==b-1 and cp["next_batch_index"]==b and st["latest_batch"]==b-1
        hist=run("git","log","-S",k,"--format=%H","--","state/slots/future_growth_7",check=False).stdout.strip()
        assert not hist,("reused window",k,hist)
        e=entry(w,sha,nbytes,accessed); prior=run("git","hash-object",str(CP)).stdout.strip()
        cp.update({"state":"BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES" if b==330 else "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES","prior_checkpoint_blob_sha":prior,"used_window_keys_this_run":[x[1] for x in BATCHES[:idx]],"unique_evidenced_parcel_count_before":0,"unique_evidenced_parcel_count_after":0,"new_unique_evidenced_parcels":0,"mirror_feature_count":18,"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"duplicate_count":0,"latest_batch":b,"next_batch_index":b+1,"new_run_bounded_batches_completed":idx,"last_batch":e,"source_contract":{"existing_source_family":"Scottish Government NPF4 Annex B national developments","new_source_family":FAMILY,"project_index":SOURCE,"canonical_target":"AAYS england_map_web future_growth parcel mirror","matching_rule":MATCHING,"nearest_match_allowed":False,"strict_join_input_status":"Official maintenance windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed; source-only evidence is not promoted to parcel evidence."},"blocker":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER","fake_data":False,"nearest_match_used":False,"demo_only":True,"final_ready":False,"production_merge":False})
        st.update({"state":cp["state"],"latest_batch":b,"bounded_batches_completed_this_run":idx,"artifact_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"final_ready":False,"production_merge":False,"last_window_key":k,"last_result":"ZERO_SAFE_CANONICAL_MATCHES"})
        mf.update({"artifact_feature_count":18,"legacy_source_evidence_feature_count":18,"unique_evidenced_parcel_count":0,"duplicate_count":0,"new_source_family":FAMILY,"matching_rule":MATCHING,"nearest_match_allowed":False,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"processed_windows_this_run":([] if idx==1 else mf.get("processed_windows_this_run",[]))})
        mf["processed_windows_this_run"].append(e)
        dump(CP,cp); dump(ST,st); dump(MF,mf); paths=[str(CP),str(ST),str(MF)]
        if b==330:
            report={"schema_version":1,"slot_id":SLOT,"continuation_key":"future_growth_7_open_source_v2_20260813","run_id":"common_continuation_20260818_batches_319_330_yorkshire_ne","requested_common_continuation_path":F_PATH,"requested_common_continuation_file_read":False,"requested_common_continuation_file_note":"The exact F: path is not mounted in the hosted session and is absent from /mnt/data. The exact file is therefore not claimed as read; this run follows the current user instruction and canonical future_growth_7 state/source contract.","requested_new_bounded_batches":12,"completed_new_bounded_batches":12,"batch_range":{"first":319,"last":330},"counts":{"before":0,"added":0,"after":0,"before_unique_evidenced_parcels":0,"added_unique_evidenced_parcels":0,"after_unique_evidenced_parcels":0,"legacy_source_evidence_feature_count":18,"mirror_feature_count":18,"duplicate_count":0},"quality_gates":{"shard_checkpoint_status_manifest_count_equal_each_batch":True,"dup0_each_batch":True,"nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"own_slot_only":True,"reused_window_count":0,"final_ready":False,"production_merge":False,"all_zero_or_verification_failed_windows_checkpointed":True},"artifact_paths":{"shard":str(SHARD),"checkpoint":str(CP),"status":str(ST),"manifest":str(MF),"report":str(RP)},"source_contract":cp["source_contract"],"source_refs":[SOURCE],"source_runtime":{"sha256":sha,"bytes":nbytes,"accessed_at":accessed},"source_window_keys":[x[1] for x in BATCHES],"source_windows":mf["processed_windows_this_run"]}
            dump(RP,report); paths.append(str(RP))
        run("git","add","--",*paths)
        changed=run("git","diff","--cached","--name-only").stdout.splitlines(); allowed={str(CP),str(ST),str(MF),str(RP)}
        assert changed and set(changed)<=allowed
        run("git","commit","-m",f"future_growth_7 batch {b} Yorkshire NE strict zero-window checkpoint")
        push(); verify(b)
    rp=remote(RP); assert rp["completed_new_bounded_batches"]==12 and rp["batch_range"]=={"first":319,"last":330}
    print("FINAL_REPORT",RP); print("BEFORE_ADDED_AFTER",rp["counts"]["before"],rp["counts"]["added"],rp["counts"]["after"])
if __name__=="__main__": main()
