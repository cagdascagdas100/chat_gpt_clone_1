from __future__ import annotations
import csv, datetime, importlib.util, json, shutil, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
TARGET=HERE/"security_public_safety_2_runner_pipeline_v9_parity.py"

def load():
    spec=importlib.util.spec_from_file_location("slot2_v9",TARGET)
    if spec is None or spec.loader is None: raise RuntimeError("IMPORT_FAILED")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def fixture(m,root):
    out=root/"docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    auto=root/"docs/chatgpt_status/aays1/shards/security_public_safety_2/automation"
    web=root/"england_map_web/data/aays_18_slots/security_public_safety_2"
    out.mkdir(parents=True);auto.mkdir(parents=True);web.mkdir(parents=True)
    rows=[{"parcel_id":f"parcel_{n}","candidate_status":"CANONICAL_API_IOD25_V2_MPS_LSOA_VERIFIED","accuracy_score_4":4,"lsoa_code":"E01000001","official_api_http_status":200,"official_api_sha256":"a"*64,"iod25_v2_join_pass":True,"mps_lsoa_join_pass":True,"output_semantics":"AREA_LEVEL_PROXY","parcel_measurement":False,"geometry":{"type":"Point","coordinates":[-0.1,51.5]}} for n in range(30762,31062)]
    headers=sorted({k for r in rows for k in r if k!="geometry"})
    cp=out/"security_public_safety_2_hydrated_300_latest.csv"
    with cp.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=headers);w.writeheader();w.writerows([{k:v for k,v in r.items() if k!="geometry"} for r in rows])
    gp=out/"security_public_safety_2_hydrated_300_latest.geojson"
    gp.write_text(json.dumps({"type":"FeatureCollection","features":[{"type":"Feature","geometry":r["geometry"],"properties":{k:v for k,v in r.items() if k!="geometry"}} for r in rows]},ensure_ascii=False,separators=(",",":"))+"\n")
    hp=web/"progress.html";hp.write_text('<body data-slot-id="security_public_safety_2" data-visible-row-count="300" data-final-ready="false"><table><tbody>'+''.join("<tr></tr>" for _ in rows)+"</tbody></table></body>")
    payload={"slot_id":m.SLOT_ID,"rows":rows,"canonical_rows":300,"accuracy_ge_3_count":300,"accuracy_4_count":300,"artifacts":{"csv_sha256":m.sha(cp),"geojson_sha256":m.sha(gp),"html_sha256":m.sha(hp),"parity_pass":True},"fake_data":False,"final_ready":False}
    jp=out/"security_public_safety_2_hydrated_300_latest.json";jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    wj=web/"hydrated_300_latest.json";wj.write_bytes(jp.read_bytes())
    return {"out":out,"web":web,"rows":rows,"headers":headers,"json":jp,"csv":cp,"geo":gp,"html":hp,"webjson":wj}

def main():
    m=load();root=Path(tempfile.mkdtemp(prefix="slot2_v9_"));cases=[]
    add=lambda n,v:cases.append({"name":n,"pass":bool(v)})
    try:
        f=fixture(m,root);add("integrity_valid",m.cross_format_integrity(root)["pass"]);add("integrity_check_count_ge_25",m.cross_format_integrity(root)["total"]>=25)
        oc=f["csv"].read_text();lines=oc.splitlines()
        csv_mut=[
            ("reject_csv_order","\n".join([lines[0],lines[2],lines[1],*lines[3:]])+"\n"),
            ("reject_csv_id",oc.replace("parcel_30762","parcel_bad",1)),
            ("reject_csv_value",oc.replace("CANONICAL_API_IOD25_V2_MPS_LSOA_VERIFIED","BAD",1)),
            ("reject_csv_header",oc.replace("accuracy_score_4,","",1)),
        ]
        for n,t in csv_mut:f["csv"].write_text(t);add(n,not m.cross_format_integrity(root)["pass"])
        f["csv"].write_text(oc)
        og=json.loads(f["geo"].read_text())
        def gm(name,fn):
            x=json.loads(json.dumps(og));fn(x);f["geo"].write_text(json.dumps(x));add(name,not m.cross_format_integrity(root)["pass"])
        gm("reject_geo_id",lambda x:x["features"][0]["properties"].update(parcel_id="bad"))
        gm("reject_geo_property",lambda x:x["features"][0]["properties"].update(candidate_status="BAD"))
        gm("reject_geo_geometry_mismatch",lambda x:x["features"][0]["geometry"].update(coordinates=[0,0]))
        gm("reject_geo_geometry_missing",lambda x:x["features"][0].update(geometry=None))
        gm("reject_geo_type",lambda x:x.update(type="NotFeatureCollection"))
        f["geo"].write_text(json.dumps(og,ensure_ascii=False,separators=(",",":"))+"\n")
        op=json.loads(f["json"].read_text())
        def jm(name,fn):
            x=json.loads(json.dumps(op));fn(x);f["json"].write_text(json.dumps(x));f["webjson"].write_bytes(f["json"].read_bytes());add(name,not m.cross_format_integrity(root)["pass"])
        jm("reject_json_id",lambda x:x["rows"][0].update(parcel_id="bad"))
        jm("reject_canonical_count",lambda x:x.update(canonical_rows=299))
        jm("reject_accuracy_ge3_count",lambda x:x.update(accuracy_ge_3_count=299))
        jm("reject_accuracy4_count",lambda x:x.update(accuracy_4_count=299))
        f["json"].write_text(json.dumps(op,ensure_ascii=False,indent=2)+"\n");f["webjson"].write_text("{}");add("reject_web_json_mismatch",not m.cross_format_integrity(root)["pass"]);f["webjson"].write_bytes(f["json"].read_bytes())
        oh=f["html"].read_text();f["html"].write_text(oh.replace('data-visible-row-count="300"','data-visible-row-count="299"'));add("reject_html_visible_count",not m.cross_format_integrity(root)["pass"])
        f["html"].write_text(oh.replace("<tr></tr>","",1));add("reject_html_tbody_count",not m.cross_format_integrity(root)["pass"]);f["html"].write_text(oh)
        for name,key in [("reject_csv_sha","csv_sha256"),("reject_geo_sha","geojson_sha256"),("reject_html_sha","html_sha256")]:
            jm(name,lambda x,k=key:x["artifacts"].update({k:"bad"}))
        jm("reject_legacy_parity_false",lambda x:x["artifacts"].update(parity_pass=False))
        now=datetime.datetime.now(datetime.timezone.utc);fresh=(now+datetime.timedelta(seconds=1)).isoformat().replace("+00:00","Z")
        receipt={"slot_id":m.SLOT_ID,"state":m.V8_STATE,"pass":True,"exit_code":0,"generated_at":fresh,"completed_at":fresh,"actual_business_rows_written":0,"fake_data":False,"final_ready":False}
        add("receipt_valid",m.receipt_ok(receipt,now)["pass"])
        for n,k,v in [("receipt_wrong_slot","slot_id","x"),("receipt_wrong_state","state","x"),("receipt_nonzero","exit_code",1),("receipt_business","actual_business_rows_written",1),("receipt_fake","fake_data",True),("receipt_final","final_ready",True),("receipt_stale","generated_at","2020-01-01T00:00:00Z")]:
            x=dict(receipt);x[k]=v;add(n,not m.receipt_ok(x,now)["pass"])
        for n in ["security_public_safety_2_pipeline_v6_receipt_latest.json","security_public_safety_2_pipeline_v7_receipt_latest.json","security_public_safety_2_pipeline_v8_receipt_latest.json"]:(f["out"]/n).write_text("x")
        removed=m.cleanup(root)
        for n in ["v6","v7","v8"]:add("cleanup_"+n,not (f["out"]/f"security_public_safety_2_pipeline_{n}_receipt_latest.json").exists())
        add("cleanup_count",len(removed)>=3);fb=m.failclosed_html("X",3);add("fallback_zero",'data-real-row-count="0"' in fb);add("fallback_core_rows","SHARED_RUNNER_PICKUP" in fb and "BROWSER_ACCEPTANCE" in fb);add("fallback_candidates","parcel_30762" in fb and "parcel_30764" in fb)
        src=TARGET.read_text();ps=(HERE/"security_public_safety_2_runner_pipeline_v9.ps1").read_text()
        static=[("static_wraps_v8","runner_pipeline_v8_integrity.py" in src),("static_csv_full_parity","csv_full_scalar_parity" in src),("static_geo_full_parity","geojson_full_property_geometry_parity" in src),("static_geometry_required","all_canonical_geometries_present" in src),("static_html_tbody","html_tbody_rows_300" in src),("static_accuracy_recompute","accuracy_4_recomputed" in src),("static_cleanup_v8","security_public_safety_2_pipeline_v8_receipt_latest.json" in src),("static_no_global","ai-tasks/current-task.json" not in src),("static_no_push","git push" not in src.lower()),("static_no_commit","git commit" not in src.lower()),("static_no_runner_start","start-process" not in ps.lower()),("static_ps_slot","WRONG_SLOT" in ps),("static_ps_branch","WRONG_BRANCH" in ps),("static_ps_root","AAYS_REPO_ROOT_NOT_RESOLVED" in ps)]
        for n,v in static:add(n,v)
    finally:shutil.rmtree(root,ignore_errors=True)
    passed=sum(c["pass"] for c in cases)
    return {"schema_version":1,"slot_id":"security_public_safety_2","test_type":"PIPELINE_V9_CROSS_FORMAT_CONTENT_PARITY_SELFTEST","cases":cases,"passed":passed,"total":len(cases),"pass":passed==len(cases),"actual_business_rows_written":0,"fake_data":False,"final_ready":False}

if __name__=="__main__":
    r=main();o=Path(__file__).resolve().parents[1]/"validation/security_public_safety_2_pipeline_v9_selftest_latest.json";o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n");print(json.dumps({"slot_id":r["slot_id"],"passed":r["passed"],"total":r["total"],"pass":r["pass"],"final_ready":False}));raise SystemExit(0 if r["pass"] else 1)
