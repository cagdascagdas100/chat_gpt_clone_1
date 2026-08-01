from __future__ import annotations
import argparse, hashlib, json, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID="parcel-label-3-historic-england-nhle-v1-20260801"
ENDPOINT="https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer/0/query"
CATALOGUE="https://www.api.gov.uk/he/national-heritage-list-for-england-nhle/"
LICENSE="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PROBE="england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS=("docs/chatgpt_status/_shared/slots_21/parcel_label_3/historic_england_nhle_result_latest.json","england_map_web/data/aays_21_slots/parcel_label_3/historic_england_nhle_latest.json")
IDS=("parcel_61523","parcel_61524","parcel_61525")
RADIUS=100
SPACING=1.2

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write_json(path,payload):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".part"); q.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); os.replace(q,p)

def load_points(repo):
    rows=json.loads((repo/PROBE).read_text(encoding="utf-8-sig")).get("canonical_points")
    if not isinstance(rows,list) or len(rows)!=3: raise ValueError("CANONICAL_POINT_COUNT_NOT_3")
    out=[]
    for row in rows:
        if row.get("parcel_id") not in IDS or row.get("geometry_type")!="Point" or not row.get("point_valid"):
            raise ValueError("INVALID_CANONICAL_POINT")
        out.append((row["parcel_id"],float(row["latitude"]),float(row["longitude"])))
    if tuple(x[0] for x in out)!=IDS: raise ValueError("CANONICAL_ID_ORDER_MISMATCH")
    return out

def url(lat,lon):
    params={"where":"1=1","geometry":f"{lon},{lat}","geometryType":"esriGeometryPoint","inSR":"4326",
      "spatialRel":"esriSpatialRelIntersects","distance":str(RADIUS),"units":"esriSRUnit_Meter",
      "outFields":"*","returnGeometry":"true","outSR":"4326","f":"json"}
    return ENDPOINT+"?"+urllib.parse.urlencode(params)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",default="."); ap.add_argument("--timeout",type=int,default=30); ap.add_argument("--validate-only",action="store_true")
    a=ap.parse_args(); repo=Path(a.repo_root); pts=load_points(repo)
    if a.validate_only:
        print(json.dumps({"state":"VALID","target_count":3,"resource_class":"network_fetch","radius_metres":RADIUS,"spacing_seconds":SPACING,"exact_write_paths":list(OUTPUTS)})); return
    evidence=[]; candidates=[]
    for i,(pid,lat,lon) in enumerate(pts):
        if i: time.sleep(SPACING)
        u=url(lat,lon); accessed=now(); qb=u.encode()
        try:
            req=urllib.request.Request(u,headers={"User-Agent":"TerraYield-AAYS/1.0 parcel-label research"})
            with urllib.request.urlopen(req,timeout=a.timeout) as r:
                raw=r.read(); status=getattr(r,"status",200)
            data=json.loads(raw)
            feats=data.get("features",[]) if isinstance(data,dict) else []
            for f in feats:
                attrs=f.get("attributes") if isinstance(f,dict) else None; geom=f.get("geometry") if isinstance(f,dict) else None
                if isinstance(attrs,dict) and isinstance(geom,dict):
                    candidates.append({"parcel_id":pid,"attributes":attrs,"geometry":geom,"candidate_only":True})
            ev={"parcel_id":pid,"source_url":u,"accessed_at":accessed,"query_sha256":sha(qb),"http_status":status,"content_sha256":sha(raw),"sha256_basis":"raw_response_bytes","relevant_record_ids_or_excerpt":f"{len(feats)} ArcGIS features","proven_fields":["raw NHLE attributes","ArcGIS point geometry"]}
        except Exception as e:
            bounded=f"HISTORIC_ENGLAND_NHLE_ERROR:{type(e).__name__}".encode()
            ev={"parcel_id":pid,"source_url":u,"accessed_at":accessed,"query_sha256":sha(qb),"http_status":None,"content_sha256":sha(bounded),"sha256_basis":"bounded_error_evidence_string","relevant_record_ids_or_excerpt":bounded.decode(),"proven_fields":["query URL","access time","query SHA-256","bounded error type"]}
        ev.update({"query_scope":{"radius_metres":RADIUS,"layer":"Listed Building points (0)"},"catalogue_url":CATALOGUE,"license_or_terms_url":LICENSE})
        evidence.append(ev)
    completed=len(evidence); target=len(pts); pct=completed/target*100 if target else 0
    state="CANDIDATES_PUBLISHED" if candidates else "NO_DATA_CONTINUE"
    payload={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":TASK_ID,"generated_at":now(),"state":state,"panel_status":"PUBLISHED","completed_count":completed,"target_count":target,"previous_percent":0.0,"progress_percent":pct,"percent_increase":pct,"produced_candidate_rows":len(candidates),"candidates":candidates,"source_evidence":evidence,"blocker":{"code":None if candidates else "HISTORIC_ENGLAND_NHLE_NO_USABLE_RESPONSE","state":state,"candidate_research_blocked":False,"manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_HISTORIC_ENGLAND_NHLE","inferred_values":0,"fake_data":False,"final_ready":False}
    for p in OUTPUTS: write_json(repo/p,payload)
    print(json.dumps({"state":state,"completed_count":completed,"target_count":target,"candidate_rows":len(candidates)}))
if __name__=="__main__": main()
