from __future__ import annotations
import argparse,hashlib,json,os,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
TASK_ID="parcel-label-3-wikidata-nearby-entities-v1-20260802"
PROBE="england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT=("docs/chatgpt_status/_shared/slots_21/parcel_label_3/wikidata_nearby_entities_result_latest.json","england_map_web/data/aays_21_slots/parcel_label_3/wikidata_nearby_entities_latest.json")
ENDPOINT="https://query.wikidata.org/sparql"
HELP="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service"
ACCESS="https://www.wikidata.org/wiki/Help:Data_access"
EXAMPLES="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples"
LICENSE="https://www.wikidata.org/wiki/Wikidata:Licensing"
IDS=("parcel_61523","parcel_61524","parcel_61525"); RADIUS=0.1; LIMIT=20; MAX_BYTES=1_048_576
def now(): return datetime.now(timezone.utc).isoformat()
def sha(v): return hashlib.sha256(v.encode() if isinstance(v,str) else v).hexdigest()
def write(path,obj):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+".tmp"); t.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8"); os.replace(t,p)
def points():
 d=json.loads(Path(PROBE).read_text()); b={r["parcel_id"]:r for r in d["canonical_points"]}; out=[]
 for pid in IDS:
  r=b.get(pid)
  if not r or r.get("geometry_type")!="Point" or r.get("point_valid") is not True: raise ValueError(f"invalid canonical point {pid}")
  x,y=float(r["longitude"]),float(r["latitude"])
  if not(-180<=x<=180 and -90<=y<=90): raise ValueError(f"invalid coordinate {pid}")
  out.append({"parcel_id":pid,"longitude":x,"latitude":y})
 return out
def query(x,y):
 return f'''SELECT ?item ?itemLabel ?location ?instance ?instanceLabel WHERE {{
 SERVICE wikibase:around {{
  ?item wdt:P625 ?location .
  bd:serviceParam wikibase:center "Point({x} {y})"^^geo:wktLiteral .
  bd:serviceParam wikibase:radius "{RADIUS}" .
 }}
 OPTIONAL {{ ?item wdt:P31 ?instance . }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} LIMIT {LIMIT}'''
def val(b,k):
 v=b.get(k); return str(v.get("value")) if isinstance(v,dict) and v.get("value") is not None else None
def candidate(pid,b,url):
 return {"parcel_id":pid,"item_uri":val(b,"item"),"item_label":val(b,"itemLabel"),"location_wkt":val(b,"location"),"instance_uri":val(b,"instance"),"instance_label":val(b,"instanceLabel"),"source_url":url,"candidate_only":True,"exact_parcel_binding_claimed":False,"property_type_binding_claimed":False}
def run(timeout):
 evidence=[]; candidates=[]
 for p in points():
  q=query(p["longitude"],p["latitude"]); url=ENDPOINT+"?"+urllib.parse.urlencode({"query":q,"format":"json"}); at=now()
  try:
   req=urllib.request.Request(url,headers={"Accept":"application/sparql-results+json, application/json","User-Agent":"TerraYield-AAYS/1.0 bounded Wikidata nearby research"})
   with urllib.request.urlopen(req,timeout=timeout) as resp:
    raw=resp.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise ValueError("response exceeded 1 MiB")
    bindings=json.loads(raw.decode()).get("results",{}).get("bindings",[])
    if not isinstance(bindings,list): raise ValueError("SPARQL bindings missing")
    bindings=bindings[:LIMIT]; candidates += [candidate(p["parcel_id"],b,url) for b in bindings]
    evidence.append({"parcel_id":p["parcel_id"],"source_url":url,"endpoint_url":ENDPOINT,"accessed_at":at,"content_sha256":sha(raw),"sha256_basis":"bounded_raw_sparql_json_response_bytes","query_sha256":sha(q),"record_scope":"one official Wikidata geospatial around query; radius 0.1 km; maximum 20 bindings; maximum 1 MiB","supports_fields":["Wikidata item URI","English label","coordinate location","instance-of URI","instance-of label"],"relevant_record_ids_or_excerpt":{"binding_count":len(bindings),"item_uris":[val(b,"item") for b in bindings]},"help_url":HELP,"data_access_url":ACCESS,"geospatial_example_url":EXAMPLES,"license_or_terms_url":LICENSE,"http_status":getattr(resp,"status",None)})
  except Exception as exc:
   msg=f"WIKIDATA_NEARBY_ENTITIES_ERROR:{type(exc).__name__}:{exc}"
   evidence.append({"parcel_id":p["parcel_id"],"source_url":url,"endpoint_url":ENDPOINT,"accessed_at":at,"content_sha256":sha(msg),"sha256_basis":"bounded_error_evidence_string","query_sha256":sha(q),"record_scope":"one official Wikidata geospatial around query; radius 0.1 km; maximum 20 bindings; no dump download","supports_fields":["Wikidata Query Service endpoint availability"],"relevant_record_ids_or_excerpt":msg[:512],"help_url":HELP,"data_access_url":ACCESS,"geospatial_example_url":EXAMPLES,"license_or_terms_url":LICENSE,"http_status":getattr(exc,"code",None)})
 state="WIKIDATA_NEARBY_ENTITY_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
 out={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":TASK_ID,"generated_at":now(),"state":state,"panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":list(IDS),"produced_candidate_rows":len(candidates),"candidate_rows":candidates,"source_evidence":evidence,"blocker":{"code":"NONE" if candidates else "WIKIDATA_QUERY_SERVICE_NO_USABLE_RESPONSE_OR_NO_NEARBY_ITEMS","state":state,"manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"VALIDATE_WIKIDATA_NEARBY_ENTITY_CANDIDATES_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_WIKIDATA_NEARBY_ENTITIES","large_data_downloaded":False,"dump_downloaded":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}
 for path in OUT: write(path,out)
 return out
def validate():
 ps=points()
 if len(ps)!=3: raise ValueError("target count")
 for path in (PROBE,*OUT):
  if Path(path).is_absolute(): raise ValueError("relative paths")
 if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/") or not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"): raise ValueError("output boundary")
 for p in ps:
  q=query(p["longitude"],p["latitude"])
  if 'wikibase:radius "0.1"' not in q or "LIMIT 20" not in q: raise ValueError("bounded query guard")
 print("PASS_TARGET_3_WIKIDATA_AROUND_100M_LIMIT20_MAX1MIB_CANDIDATE_ONLY")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--timeout",type=float,default=20); p.add_argument("--validate-only",action="store_true"); a=p.parse_args()
 if a.validate_only: validate(); return
 r=run(a.timeout); print(json.dumps({"state":r["state"],"completed_count":r["completed_count"],"target_count":r["target_count"],"produced_candidate_rows":r["produced_candidate_rows"],"evidence_records":len(r["source_evidence"])},separators=(",",":")))
if __name__=="__main__": main()
