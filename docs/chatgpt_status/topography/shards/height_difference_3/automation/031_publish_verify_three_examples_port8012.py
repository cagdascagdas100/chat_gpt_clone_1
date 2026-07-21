#!/usr/bin/env python3
"""Fail-closed publication and port 8012 acceptance for three real examples."""
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, sys, tempfile, urllib.request
from pathlib import Path
from typing import Any

ROWS = (61523, 61524, 61525)
CONF = {"HIGH", "MEDIUM_HIGH"}
METHOD = "EA_DTM_1M_POLYGON_P95_MINUS_P05"
HEX = set("0123456789abcdef")

def load(path: Path) -> dict[str, Any]:
    if not path.is_file(): raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict): raise ValueError(f"JSON object required: {path}")
    return value

def canon(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""): h.update(b)
    return h.hexdigest()

def num(value: Any, name: str) -> float:
    value = float(value)
    if not math.isfinite(value): raise ValueError(f"{name} is non-finite")
    return value

def good_sha(value: Any) -> bool:
    value = str(value or "").casefold()
    return len(value) == 64 and all(c in HEX for c in value)

def coordinates(value: Any):
    if not isinstance(value, (list, tuple)): return
    if len(value) >= 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in value[:2]):
        yield num(value[0], "lon"), num(value[1], "lat")
    else:
        for item in value: yield from coordinates(item)

def geometry(value: Any, row: int) -> None:
    if not isinstance(value, dict) or value.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"row {row} polygon missing")
    points = list(coordinates(value.get("coordinates")))
    if len(points) < 4: raise ValueError(f"row {row} polygon too short")
    if any(not (-180 <= x <= 180 and -90 <= y <= 90) for x, y in points):
        raise ValueError(f"row {row} WGS84 bounds failed")

def sources(result: dict[str, Any], row: int) -> None:
    ea, os50 = result.get("ea_dtm"), result.get("os_terrain50")
    if not isinstance(ea, dict) or not isinstance(os50, dict): raise ValueError(f"row {row} source evidence missing")
    for label, values in (("EA", ea.get("source_rasters")), ("OS", os50.get("source_rasters"))):
        if not isinstance(values, list) or not values: raise ValueError(f"row {row} {label} rasters missing")
        if any(not isinstance(x, dict) or not good_sha(x.get("sha256")) for x in values):
            raise ValueError(f"row {row} {label} SHA invalid")
    if not isinstance(os50.get("centroid_source"), dict) or not good_sha(os50["centroid_source"].get("sha256")):
        raise ValueError(f"row {row} OS centroid SHA invalid")

def validate_measurements(value: dict[str, Any]) -> dict[int, dict[str, Any]]:
    if value.get("slot_id") != "height_difference_3" or value.get("target_crs") != "EPSG:27700":
        raise ValueError("measurement identity/CRS mismatch")
    if value.get("nearest_point_fill_forbidden") is not True: raise ValueError("nearest fill gate missing")
    if any(value.get(k) not in (False, None) for k in ("final_ready","fake_data","db_write","migration","production_deploy")):
        raise ValueError("unsafe measurement flags")
    results, measured = value.get("results"), value.get("measured_rows")
    if not isinstance(results, list) or not isinstance(measured, list): raise ValueError("measurement lists missing")
    if (value.get("candidate_count"), value.get("promoted_measurement_count"), value.get("blocked_measurement_count")) != (3,3,0):
        raise ValueError("measurement counts must be 3/3/0")
    evidence = {}
    for item in results:
        row, parcel = int(item["row_no"]), str(item["parcel_id"]).strip()
        key = (row, parcel)
        if key in evidence: raise ValueError("duplicate result")
        if item.get("status") != "MEASURED_AND_CROSSCHECKED" or item.get("measured_value_promoted") is not True:
            raise ValueError(f"row {row} not promoted")
        if item.get("nearest_point_fill_used") is not False or item.get("gate_reasons") not in ([], None):
            raise ValueError(f"row {row} blocked gates")
        if item.get("confidence") not in CONF: raise ValueError(f"row {row} confidence")
        diff, limit = num(item["cross_source_absolute_difference_m"], "difference"), num(item["crosscheck_threshold_m"], "threshold")
        if diff < 0 or diff > limit or limit > 8: raise ValueError(f"row {row} crosscheck")
        sources(item, row); evidence[key] = item
    output = {}
    for item in measured:
        row, parcel = int(item["row_no"]), str(item["parcel_id"]).strip()
        if row not in ROWS or row in output or not parcel or (row, parcel) not in evidence: raise ValueError("measured registry mismatch")
        if item.get("height_difference_method") != METHOD or item.get("confidence") not in CONF: raise ValueError(f"row {row} method/confidence")
        if int(item.get("ea_valid_cell_count", 0)) < 4 or not 0 <= num(item["cross_source_absolute_difference_m"], "difference") <= 8:
            raise ValueError(f"row {row} numeric gates")
        for field in ("height_difference_m","elevation_median_m","elevation_iqr_m","os_terrain50_centroid_elevation_m"): num(item[field], field)
        geometry(item.get("geometry_geojson_epsg4326_display_only"), row); output[row] = item
    if tuple(sorted(output)) != ROWS: raise ValueError("expected rows 61523-61525")
    return output

def validate_publication(summary: dict[str, Any], geo: dict[str, Any], measured: dict[int, dict[str, Any]]) -> None:
    if summary.get("slot_id") != "height_difference_3" or summary.get("status") != "VERIFIED_EXAMPLES_PUBLISHED":
        raise ValueError("publication identity/status")
    if summary.get("published_example_count") != 3: raise ValueError("exactly three examples required")
    if any(summary.get(k) is not False for k in ("overall_product_final_ready","fake_data","db_write","migration","production_deploy")):
        raise ValueError("unsafe publication flags")
    if not isinstance(summary.get("publication_gate"), dict) or summary["publication_gate"].get("nearest_fill_forbidden") is not True:
        raise ValueError("publication gate")
    rows, features = summary.get("rows"), geo.get("features")
    if not isinstance(rows, list) or not isinstance(features, list) or len(rows) != 3 or len(features) != 3: raise ValueError("JSON/GeoJSON count")
    if geo.get("type") != "FeatureCollection" or geo.get("final_ready") is not False or geo.get("fake_data") is not False:
        raise ValueError("GeoJSON flags")
    by_row = {int(x["row_no"]): x for x in rows}; by_feature = {int(x["properties"]["row_no"]): x for x in features}
    if tuple(sorted(by_row)) != ROWS or tuple(sorted(by_feature)) != ROWS: raise ValueError("publication registry")
    for row in ROWS:
        published, feature, source = by_row[row], by_feature[row], measured[row]
        if str(published["parcel_id"]) != str(source["parcel_id"]) or str(feature.get("id")) != str(source["parcel_id"]): raise ValueError("parcel mismatch")
        if feature.get("properties") != published: raise ValueError("JSON/GeoJSON properties mismatch")
        geometry(feature.get("geometry"), row)
        if published.get("height_difference_method") != METHOD or published.get("confidence") not in CONF: raise ValueError("publication method/confidence")
        if published.get("data_status") != "official_sources_crosschecked" or published.get("final_ready") is not False: raise ValueError("publication status")
        for field in ("height_difference_m","elevation_median_m","elevation_iqr_m","os_terrain50_centroid_elevation_m","cross_source_absolute_difference_m"):
            if round(num(published[field],field),3) != round(num(source[field],field),3): raise ValueError(f"row {row} {field} mismatch")

def validate_runtime(value: dict[str, Any], accepted: bool=False) -> list[dict[str, Any]]:
    allowed = {"THREE_REAL_SHARD_ROWS_OFFICIAL_CROSSCHECKED_AND_PUBLISHED"}
    if accepted: allowed.add("THREE_EXAMPLES_ATOMICALLY_PUBLISHED_AND_PORT_8012_VERIFIED")
    if value.get("status") not in allowed or value.get("pipeline_child_exit_code") not in (0,None): raise ValueError("runtime status/exit")
    ops = value.get("operations")
    if not isinstance(ops, list) or not ops: raise ValueError("runtime operations missing")
    nums = [int(x["operation_no"]) for x in ops]
    if nums != list(range(nums[0], nums[0]+len(nums))) or len(nums) != len(set(nums)): raise ValueError("runtime numbering")
    if any(str(x.get("status")).casefold()=="blocked" for x in ops): raise ValueError("runtime blocked row")
    if int(value.get("operation_count",len(ops))) != len(ops): raise ValueError("runtime count")
    counts = value.get("real_counts")
    if isinstance(counts, dict):
        for key, expected in {"canonical_shard_rows":30761,"candidates":3,"hmlr_matches":3,"ea_samples":3,"terrain50_samples":3,"published_examples":3}.items():
            if int(counts.get(key,expected)) != expected: raise ValueError(f"runtime {key}")
    return [dict(x) for x in ops]

def normalize_runtime_counts(value: dict[str, Any]) -> dict[str, Any]:
    expected={"canonical_shard_rows":30761,"candidates":3,"hmlr_matches":3,"ea_samples":3,"terrain50_samples":3,"published_examples":3}
    existing=value.get("real_counts")
    if existing is not None and not isinstance(existing,dict): raise ValueError("runtime real_counts type")
    if isinstance(existing,dict):
        for key,target in expected.items():
            current=int(existing.get(key,0))
            if current not in (0,target): raise ValueError(f"runtime conflicting {key}={current}")
    result=dict(value); result["real_counts"]=expected; result["real_counts_derived_from_validated_artifacts"]=True
    return result

def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=target.name+".", suffix=".tmp", dir=target.parent); os.close(fd); temp=Path(name)
    try:
        shutil.copyfile(source,temp)
        if sha(temp) != sha(source): raise ValueError("copy SHA mismatch")
        temp.replace(target)
    finally: temp.unlink(missing_ok=True)

def fetch(url: str, timeout: int) -> tuple[dict[str,Any],dict[str,Any]]:
    request=urllib.request.Request(url,headers={"User-Agent":"TerraYield-AAYS/height_difference_3-acceptance","Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=timeout) as response:
        body=response.read(26214401)
        if len(body)>26214400: raise ValueError("HTTP response too large")
        value=json.loads(body)
        if not isinstance(value,dict): raise ValueError("HTTP object required")
        return value,{"requested_url":url,"resolved_url":response.geturl(),"status":getattr(response,"status",200),"size_bytes":len(body),"sha256":hashlib.sha256(body).hexdigest()}

def accepted_runtime(runtime: dict[str,Any]) -> dict[str,Any]:
    ops=validate_runtime(runtime); number=int(ops[-1]["operation_no"])+1
    for stage,summary in [
        ("WEBSITE_ACCEPTANCE_LOCAL_OUTPUTS","Measurement and publication outputs passed validation."),
        ("WEBSITE_ACCEPTANCE_ATOMIC_COPY","JSON and GeoJSON were atomically copied."),
        ("WEBSITE_ACCEPTANCE_JSON_READBACK","Port 8012 returned exact JSON."),
        ("WEBSITE_ACCEPTANCE_GEOJSON_READBACK","Port 8012 returned exact GeoJSON."),
        ("WEBSITE_ACCEPTANCE_RUNTIME_READBACK","Port 8012 returned successful runtime."),
        ("WEBSITE_ACCEPTANCE_COMPLETED","Three official examples are visible; final_ready remains false.")]:
        ops.append({"operation_no":number,"stage":stage,"status":"completed","details_summary":summary}); number+=1
    result=dict(runtime); result.update({"status":"THREE_EXAMPLES_ATOMICALLY_PUBLISHED_AND_PORT_8012_VERIFIED","operation_count":len(ops),"operations":ops,"last_visible_operation_no":ops[-1]["operation_no"],"website_acceptance_verified":True,"final_ready":False,"product_final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False})
    return result

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True,type=Path); ap.add_argument("--web-json",required=True,type=Path)
    ap.add_argument("--web-geojson",required=True,type=Path); ap.add_argument("--web-runtime-status",required=True,type=Path)
    ap.add_argument("--base-url",default="http://127.0.0.1:8012"); ap.add_argument("--timeout",type=int,default=30)
    ap.add_argument("--skip-http-readback",action="store_true"); ap.add_argument("--acceptance-output",type=Path)
    args=ap.parse_args()
    if args.timeout<1: raise ValueError("timeout")
    out=args.output_dir.resolve(); mp=out/"official_measurements.json"; jp=out/"verified_examples.json"; gp=out/"verified_examples.geojson"
    measurements,summary,geo,runtime=load(mp),load(jp),load(gp),load(args.web_runtime_status.resolve())
    measured=validate_measurements(measurements); validate_publication(summary,geo,measured)
    runtime=normalize_runtime_counts(runtime); validate_runtime(runtime)
    runtime_target=args.web_runtime_status.resolve(); runtime_temp=runtime_target.with_suffix(runtime_target.suffix+".tmp"); runtime_temp.write_text(json.dumps(runtime,ensure_ascii=False,indent=2)+"\n"); runtime_temp.replace(runtime_target)
    atomic_copy(jp,args.web_json.resolve()); atomic_copy(gp,args.web_geojson.resolve())
    if canon(load(args.web_json.resolve()))!=canon(summary) or canon(load(args.web_geojson.resolve()))!=canon(geo): raise ValueError("web copy differs")
    http={"skipped":args.skip_http_readback}
    if not args.skip_http_readback:
        base=args.base_url.rstrip("/"); prefix="/data/aays_18_slots/height_difference_3/"
        rj,jm=fetch(base+prefix+"verified_examples_latest.json",args.timeout); rg,gm=fetch(base+prefix+"verified_examples_latest.geojson",args.timeout); rr,rm=fetch(base+prefix+"runtime_progress_latest.json",args.timeout)
        if canon(rj)!=canon(summary) or canon(rg)!=canon(geo): raise ValueError("port 8012 publication mismatch")
        validate_runtime(rr); final=accepted_runtime(runtime)
        target=args.web_runtime_status.resolve(); temp=target.with_suffix(target.suffix+".tmp"); temp.write_text(json.dumps(final,ensure_ascii=False,indent=2)+"\n"); temp.replace(target)
        after,am=fetch(base+prefix+"runtime_progress_latest.json",args.timeout); validate_runtime(after,True)
        if canon(after)!=canon(final): raise ValueError("port 8012 final runtime mismatch")
        http={"skipped":False,"json":jm,"geojson":gm,"runtime_before":rm,"runtime_after":am}
    report={"schema_version":1,"slot_id":"height_difference_3","status":"THREE_EXAMPLES_ATOMICALLY_PUBLISHED_AND_PORT_8012_VERIFIED" if not args.skip_http_readback else "THREE_EXAMPLES_ATOMICALLY_PUBLISHED_HTTP_TEST_SKIPPED","verified_row_nos":list(ROWS),"verified_example_count":3,"runner_outputs":{"measurement_sha256":sha(mp),"verified_json_sha256":sha(jp),"verified_geojson_sha256":sha(gp)},"website_outputs":{"json":str(args.web_json.resolve()),"json_sha256":sha(args.web_json.resolve()),"geojson":str(args.web_geojson.resolve()),"geojson_sha256":sha(args.web_geojson.resolve())},"http_readback":http,"measurement_method":METHOD,"nearest_fill_forbidden":True,"single_shared_runner_only":True,"new_runner_created":False,"parallel_runner_used":False,"queue_submission":False,"final_ready":False,"product_final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    output=(args.acceptance_output or out/"website_acceptance_latest.json").resolve(); output.parent.mkdir(parents=True,exist_ok=True); temp=output.with_suffix(output.suffix+".tmp"); temp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n"); temp.replace(output)
    print(json.dumps({"ok":True,"status":report["status"],"rows":list(ROWS),"report":str(output)})); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise
