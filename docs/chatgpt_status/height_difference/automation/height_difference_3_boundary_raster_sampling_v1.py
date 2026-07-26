#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IDS=["parcel_61523","parcel_61524","parcel_61525"]
BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
RES={0.25,0.5,1.0,2.0}
MIN_CELLS=25; MIN_EDGE=8; MAX_PIXELS=1_000_000

class GateError(RuntimeError): pass
def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def read(p):
    try: x=json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError as e: raise GateError(f"INPUT_NOT_FOUND:{p}") from e
    except json.JSONDecodeError as e: raise GateError(f"INPUT_JSON_INVALID:{p}") from e
    if not isinstance(x,dict): raise GateError(f"INPUT_ROOT_NOT_OBJECT:{p}")
    return x
def write(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); os.replace(t,p)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        while b:=f.read(1<<20): h.update(b)
    return h.hexdigest()
def num(v,k):
    if isinstance(v,bool): raise GateError(k+"_NOT_NUMERIC")
    try: v=float(v)
    except Exception as e: raise GateError(k+"_NOT_NUMERIC") from e
    if not math.isfinite(v): raise GateError(k+"_NOT_FINITE")
    return v
def rows(x,k,field="rows"):
    r=x.get(field)
    if not isinstance(r,list) or len(r)!=3 or any(not isinstance(v,dict) for v in r): raise GateError(k+"_ROW_COUNT_NOT_3")
    if [v.get("parcel_id") for v in r]!=IDS: raise GateError(k+"_PARCEL_ORDER_INVALID")
    return r

def canonical(x):
    r=rows(x,"CANONICAL","canonical_point_rows")
    if (x.get("canonical_blob_sha") or x.get("source_blob_sha"))!=BLOB: raise GateError("CANONICAL_BLOB_SHA_MISMATCH")
    if x.get("feature_count") not in (None,92283): raise GateError("CANONICAL_FEATURE_COUNT_MISMATCH")
    for v in r:
        if v.get("geometry_type")!="Point": raise GateError("CANONICAL_GEOMETRY_NOT_POINT")
        lon,lat=num(v.get("longitude"),"LONGITUDE"),num(v.get("latitude"),"LATITUDE")
        if not(-180<=lon<=180 and -90<=lat<=90): raise GateError("CANONICAL_COORDINATE_RANGE")
    return r
def discovery(x):
    r=rows(x,"DISCOVERY","parcel_rows")
    if x.get("final_ready") is True: raise GateError("DISCOVERY_PREMATURE_FINAL_READY")
    for v in r:
        num(v.get("easting"),"EASTING"); num(v.get("northing"),"NORTHING")
        ev=json.dumps(v.get("transformation") or x.get("transformation") or {},sort_keys=True).upper()
        if "OSTN15" not in ev and "7953" not in ev: raise GateError("DISCOVERY_OSTN15_NOT_PROVEN")
        if "BALLPARK" in ev or "HELMERT" in ev: raise GateError("DISCOVERY_APPROX_TRANSFORM_REJECTED")
    return r
def boundaries(x,dr):
    from shapely.geometry import Point,shape
    r=rows(x,"BOUNDARY")
    rel=x.get("release")
    if not isinstance(rel,dict) or not rel.get("published_at") or not rel.get("manifest_sha256"): raise GateError("BOUNDARY_RELEASE_PROVENANCE_MISSING")
    seen={}
    for v,p in zip(r,dr):
        if v.get("source_crs_epsg")!=27700: raise GateError("BOUNDARY_CRS_NOT_27700")
        iid=str(v.get("inspire_id") or ""); gh=str(v.get("geometry_sha256") or "")
        if not iid or len(gh)!=64: raise GateError("BOUNDARY_ID_OR_SHA_MISSING")
        if iid in seen and seen[iid]!=gh: raise GateError("BOUNDARY_DUPLICATE_CONFLICT")
        seen[iid]=gh
        g=shape(v.get("polygon_geojson") or {})
        if g.geom_type not in {"Polygon","MultiPolygon"} or g.is_empty or not g.is_valid: raise GateError("BOUNDARY_GEOMETRY_INVALID")
        if not g.covers(Point(num(p.get("easting"),"EASTING"),num(p.get("northing"),"NORTHING"))): raise GateError("BOUNDARY_DOES_NOT_COVER_POINT")
        s=v.get("boundary_semantics")
        if s not in {"GENERAL_BOUNDARY","DETERMINED_BOUNDARY"}: raise GateError("BOUNDARY_SEMANTICS_INVALID")
        if s=="DETERMINED_BOUNDARY" and not v.get("determined_boundary_evidence"): raise GateError("DETERMINED_BOUNDARY_EVIDENCE_MISSING")
    return r
def values(ds,geom,buf):
    import numpy as np
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds
    from shapely.geometry import shape,mapping
    g=shape(geom).buffer(-buf)
    if g.is_empty: raise GateError("INTERIOR_BUFFER_EMPTY")
    w=from_bounds(*g.bounds,transform=ds.transform).round_offsets().round_lengths()
    if w.width<=0 or w.height<=0: raise GateError("INTERIOR_WINDOW_EMPTY")
    if int(w.width)*int(w.height)>MAX_PIXELS: raise GateError("INTERIOR_WINDOW_TOO_LARGE")
    a=ds.read(1,window=w,masked=False); m=geometry_mask([mapping(g)],a.shape,ds.window_transform(w),invert=True)
    good=m & np.isfinite(a)
    if ds.nodata is not None and math.isfinite(float(ds.nodata)): good &= a!=ds.nodata
    return a[good].astype("float64").tolist()
def edge(ds,geom):
    from shapely.geometry import shape
    b=shape(geom).boundary
    if b.is_empty or b.length<=0: raise GateError("BOUNDARY_LINE_EMPTY")
    out=[]
    for a in ds.sample([b.interpolate((i+.5)/MIN_EDGE,normalized=True).coords[0] for i in range(MIN_EDGE)],indexes=1,masked=False):
        v=float(a[0])
        if math.isfinite(v) and not(ds.nodata is not None and math.isfinite(float(ds.nodata)) and v==float(ds.nodata)): out.append(v)
    return out
def sample(v,b,p):
    import rasterio
    f=Path(str(v.get("dtm_path") or ""))
    if not f.is_file(): raise GateError("DTM_FILE_NOT_FOUND")
    hs=str(v.get("dtm_sha256") or "").lower()
    if len(hs)!=64 or sha(f)!=hs: raise GateError("DTM_SHA256_MISMATCH")
    if v.get("product")!="EA_LIDAR_DTM_TIME_STAMPED": raise GateError("DTM_PRODUCT_INVALID")
    if v.get("crs_epsg")!=27700 or v.get("vertical_datum")!="ODN": raise GateError("DTM_CRS_OR_DATUM_INVALID")
    if "OSGM15" not in str(v.get("geoid") or "").upper(): raise GateError("DTM_GEOID_NOT_OSGM15")
    z=num(v.get("resolution_m"),"DTM_RESOLUTION")
    if z not in RES: raise GateError("DTM_RESOLUTION_UNSUPPORTED")
    if not v.get("survey_date") or v.get("catalog_object_id") is None: raise GateError("DTM_SURVEY_PROVENANCE_MISSING")
    with rasterio.open(f) as ds:
        if ds.count!=1 or not ds.crs or ds.crs.to_epsg()!=27700: raise GateError("DTM_DATASET_STRUCTURE_INVALID")
        if abs(abs(ds.transform.a)-z)>1e-6 or abs(abs(ds.transform.e)-z)>1e-6: raise GateError("DTM_PIXEL_SIZE_MISMATCH")
        x,y=num(p.get("easting"),"EASTING"),num(p.get("northing"),"NORTHING")
        if not(ds.bounds.left<=x<=ds.bounds.right and ds.bounds.bottom<=y<=ds.bounds.top): raise GateError("DTM_POINT_OUTSIDE_BOUNDS")
        vv=values(ds,b["polygon_geojson"],max(2*z,1.0)); ee=edge(ds,b["polygon_geojson"])
    if len(vv)<MIN_CELLS: raise GateError("DTM_INSUFFICIENT_INTERIOR_CELLS")
    if len(ee)<MIN_EDGE: raise GateError("DTM_INSUFFICIENT_EDGE_SAMPLES")
    vv.sort()
    return {"parcel_id":v["parcel_id"],"dtm_sha256":hs,"resolution_m":z,"survey_date":v["survey_date"],"catalog_object_id":v["catalog_object_id"],
      "valid_interior_cell_count":len(vv),"edge_sample_count":len(ee),"interior_min_m":round(vv[0],4),"interior_max_m":round(vv[-1],4),
      "interior_height_difference_m":round(vv[-1]-vv[0],4),"interior_median_m":round(vv[len(vv)//2],4),
      "edge_min_m":round(min(ee),4),"edge_max_m":round(max(ee),4),"boundary_semantics":b["boundary_semantics"],"publishable":False}
def run(a):
    canonical(read(a.canonical_points)); d=discovery(read(a.official_discovery)); b=boundaries(read(a.boundary_manifest),d); r=rows(read(a.raster_manifest),"RASTER")
    pr=[sample(x,y,z) for x,y,z in zip(r,b,d)]
    return {"schema_version":1,"slot_id":"height_difference_3","task_id":"height-difference-3-boundary-raster-sampling-v1-20260722",
      "generated_at":now(),"state":"OFFICIAL_DTM_SAMPLED_NONFINAL","parcel_rows":pr,"canonical_point_rows":3,"transformed_point_rows":3,
      "exact_boundary_rows":sum(x["boundary_semantics"]=="DETERMINED_BOUNDARY" for x in b),"general_boundary_rows":sum(x["boundary_semantics"]=="GENERAL_BOUNDARY" for x in b),
      "numeric_elevation_rows":3,"actual_business_data_rows_written":0,"output_semantics":"OFFICIAL_DTM_SAMPLING_EVIDENCE_NONFINAL_NO_LEGAL_BOUNDARY_CLAIM",
      "fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
def main():
    q=argparse.ArgumentParser()
    for k in ["canonical-points","official-discovery","boundary-manifest","raster-manifest","output","website-output"]: q.add_argument("--"+k,required=True)
    q.add_argument("--expected-blob-sha",default=BLOB)
    a=q.parse_args()
    if a.expected_blob_sha!=BLOB: raise SystemExit("EXPECTED_BLOB_SHA_MISMATCH")
    try: x=run(a); code=0
    except Exception as e:
        x={"schema_version":1,"slot_id":"height_difference_3","task_id":"height-difference-3-boundary-raster-sampling-v1-20260722","generated_at":now(),
           "state":"BLOCKED_FAIL_CLOSED","error":type(e).__name__+":"+str(e),"parcel_rows":[],"canonical_point_rows":0,"transformed_point_rows":0,
           "exact_boundary_rows":0,"numeric_elevation_rows":0,"actual_business_data_rows_written":0,"fake_data":False,"final_ready":False}; code=2
    write(a.output,x); write(a.website_output,x); return code
if __name__=="__main__": raise SystemExit(main())