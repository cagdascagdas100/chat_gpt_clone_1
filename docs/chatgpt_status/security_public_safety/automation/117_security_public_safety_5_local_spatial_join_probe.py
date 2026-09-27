import json, os, math
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
PARTITION_START=61524
PARTITION_END=76903
MAX_MATCHES=50
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
CANON=REPO/"docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson"
SOURCE=REPO/"incoming/source_area/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_barnet_ward_polygons_20260927T204546Z/records.geojson"
OUTDIR=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs"
STATUSDIR=REPO/"docs/chatgpt_status/security_public_safety/status"
REPORTDIR=REPO/"docs/chatgpt_status/security_public_safety/reports"
for d in (OUTDIR,STATUSDIR,REPORTDIR): d.mkdir(parents=True,exist_ok=True)

def polygons(g):
    if not g: return []
    t=g.get("type"); c=g.get("coordinates") or []
    if t=="Polygon": return [c]
    if t=="MultiPolygon": return c
    return []

def bbox_poly(poly):
    xs=[]; ys=[]
    for ring in poly:
        for pt in ring:
            if len(pt)>=2:
                xs.append(float(pt[0])); ys.append(float(pt[1]))
    return (min(xs),min(ys),max(xs),max(ys)) if xs else None

def bbox_overlap(a,b):
    return a and b and not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

def orient(a,b,c):
    v=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    if abs(v)<1e-12: return 0
    return 1 if v>0 else -1

def onseg(a,b,p):
    return (min(a[0],b[0])-1e-12 <= p[0] <= max(a[0],b[0])+1e-12 and
            min(a[1],b[1])-1e-12 <= p[1] <= max(a[1],b[1])+1e-12 and orient(a,b,p)==0)

def seg_inter(a,b,c,d):
    o1,o2,o3,o4=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    if o1!=o2 and o3!=o4: return True
    return (o1==0 and onseg(a,b,c)) or (o2==0 and onseg(a,b,d)) or (o3==0 and onseg(c,d,a)) or (o4==0 and onseg(c,d,b))

def point_in_ring(p, ring):
    inside=False
    n=len(ring)
    if n<3: return False
    j=n-1
    for i in range(n):
        a=ring[j]; b=ring[i]
        ax,ay=float(a[0]),float(a[1]); bx,by=float(b[0]),float(b[1])
        if onseg((ax,ay),(bx,by),p): return True
        if ((ay>p[1]) != (by>p[1])):
            xin=(bx-ax)*(p[1]-ay)/(by-ay)+ax
            if p[0] < xin: inside=not inside
        j=i
    return inside

def point_in_poly(p, poly):
    if not poly or not point_in_ring(p, poly[0]): return False
    for hole in poly[1:]:
        if point_in_ring(p,hole): return False
    return True

def rings_segments(poly):
    for ring in poly:
        if len(ring)<2: continue
        for i in range(len(ring)-1):
            yield (ring[i],ring[i+1])
        if ring[0]!=ring[-1]:
            yield (ring[-1],ring[0])

def poly_intersects(a,b):
    ba,bb=bbox_poly(a),bbox_poly(b)
    if not bbox_overlap(ba,bb): return False
    for s1,s2 in rings_segments(a):
        aa=(float(s1[0]),float(s1[1])); ab=(float(s2[0]),float(s2[1]))
        for t1,t2 in rings_segments(b):
            bb1=(float(t1[0]),float(t1[1])); bb2=(float(t2[0]),float(t2[1]))
            if seg_inter(aa,ab,bb1,bb2): return True
    if a and a[0]:
        p=(float(a[0][0][0]),float(a[0][0][1]))
        if point_in_poly(p,b): return True
    if b and b[0]:
        p=(float(b[0][0][0]),float(b[0][0][1]))
        if point_in_poly(p,a): return True
    return False

def geom_intersects(ga,gb):
    for a in polygons(ga):
        ba=bbox_poly(a)
        for b in polygons(gb):
            if bbox_overlap(ba,bbox_poly(b)) and poly_intersects(a,b): return True
    return False

ID_KEYS=["parcel_id","parcel_ref","id","site_id","row_id","reference","title_number","uprn","OBJECTID","objectid","fid","FID"]
INDEX_KEYS=["partition_index","canonical_index","global_index","source_index","row_index","index","OBJECTID","objectid","fid","FID"]

def first_value(props,keys):
    for k in keys:
        if k in props and props[k] not in (None,""):
            return k,props[k]
    return None,None

def as_int(v):
    if isinstance(v,bool): return None
    try:
        if isinstance(v,float) and not v.is_integer(): return None
        s=str(v).strip()
        if s.endswith(".0"): s=s[:-2]
        return int(s)
    except: return None

with CANON.open("r",encoding="utf-8-sig") as f:
    canon=json.load(f)
with SOURCE.open("r",encoding="utf-8-sig") as f:
    src=json.load(f)
source_features=[f for f in src.get("features",[]) if f.get("geometry")]
matches=[]
scanned=0
union_keys=set()
partition_eligible=0
identity_ok=0
for idx,f in enumerate(canon.get("features",[]),start=1):
    scanned=idx
    props=f.get("properties") or {}
    union_keys.update(props.keys())
    hit_ids=[]
    for sf in source_features:
        if geom_intersects(f.get("geometry"),sf.get("geometry")):
            hit_ids.append(sf.get("id") or (sf.get("properties") or {}).get("coverage_area_id"))
    if not hit_ids: continue
    id_key,cid=first_value(props,ID_KEYS)
    ix_key,ix_val=first_value(props,INDEX_KEYS)
    ix=as_int(ix_val)
    idok=cid not in (None,"")
    pok=ix is not None and PARTITION_START <= ix <= PARTITION_END
    identity_ok += 1 if idok else 0
    partition_eligible += 1 if pok else 0
    matches.append({
        "scan_feature_ordinal":idx,
        "canonical_id_key":id_key,
        "canonical_id":cid,
        "partition_index_key":ix_key,
        "partition_index":ix,
        "partition_eligible":pok,
        "source_area_ids":hit_ids,
        "feature":{"type":"Feature","id":f.get("id"),"geometry":f.get("geometry"),"properties":props}
    })
    if len(matches)>=MAX_MATCHES: break

result={
 "slot_id":SLOT_ID,
 "lineage_id":LINEAGE_ID,
 "partition":[PARTITION_START,PARTITION_END],
 "category_target":"AAYS_LAYER24_EVIDENCE_V1",
 "probe_kind":"LOCAL_SPATIAL_JOIN_CANONICAL_READBACK_FAIL_CLOSED",
 "canonical_path":str(CANON.relative_to(REPO)).replace("\\","/"),
 "source_path":str(SOURCE.relative_to(REPO)).replace("\\","/"),
 "source_geometry_count":len(source_features),
 "source_area_ids":[f.get("id") or (f.get("properties") or {}).get("coverage_area_id") for f in source_features],
 "canonical_feature_count":len(canon.get("features",[])),
 "canonical_features_scanned":scanned,
 "matched_returned_count":len(matches),
 "max_records":MAX_MATCHES,
 "scan_stopped_at_limit":len(matches)>=MAX_MATCHES,
 "canonical_identity_ok_count":identity_ok,
 "partition_eligible_count":partition_eligible,
 "accepted_count":0,
 "source_area_count":0,
 "local_spatial_join_readback":len(matches)>0,
 "security_semantic_acceptance":False,
 "first_missing_criterion":"LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED",
 "next_blocker":("SECURITY_COVERAGE_POLYGON_FIELD_EVIDENCE_REQUIRED" if len(matches)>0 else "CANONICAL_BARNET_INTERSECTION_NOT_FOUND"),
 "property_keys":sorted(union_keys),
 "matches":matches,
 "notes":[
   "No parcel is accepted by this probe.",
   "ONS ward geometry is used only to prove local spatial join/canonical readback mechanics; it is not asserted to equal Metropolitan Police neighbourhood coverage.",
   "A later accepted Layer24 package requires canonical identity, partition eligibility, exact security coverage/identifier evidence, and field evidence together."
 ]
}
out=OUTDIR/"117_security_public_safety_5_local_spatial_join_probe.json"
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
status={
 "slot_id":SLOT_ID,"lineage_id":LINEAGE_ID,"status":"LOCAL_SPATIAL_JOIN_PROBE_COMPLETE",
 "matched_returned_count":len(matches),"partition_eligible_count":partition_eligible,
 "accepted_count":0,"final_ready":False,"fake_data":False,
 "first_missing_criterion":"LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED",
 "next_blocker":result["next_blocker"]
}
(STATUSDIR/"117_security_public_safety_5_local_spatial_join_probe.status.json").write_text(json.dumps(status,indent=2)+"\n",encoding="utf-8")
(REPORTDIR/"117_security_public_safety_5_local_spatial_join_probe.md").write_text(
 f"# security_public_safety_5 local spatial join probe\n\nmatched_returned_count={len(matches)}\npartition_eligible_count={partition_eligible}\naccepted_count=0\nfirst_missing_criterion=LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED\nnext_blocker={result['next_blocker']}\n",encoding="utf-8")
print(json.dumps(status))
