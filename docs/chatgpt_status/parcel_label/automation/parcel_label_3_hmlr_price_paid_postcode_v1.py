from __future__ import annotations
import argparse, hashlib, json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID="parcel-label-3-hmlr-price-paid-postcode-v1-20260802"
PROBE="england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
INPUT="docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/ppd_postcode_input_20260802.json"
OUT=("docs/chatgpt_status/_shared/slots_21/parcel_label_3/hmlr_price_paid_postcode_result_latest.json","england_map_web/data/aays_21_slots/parcel_label_3/hmlr_price_paid_postcode_latest.json")
ENDPOINT="https://landregistry.data.gov.uk/landregistry/query"
GUIDANCE="https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads"
ABOUT="https://www.gov.uk/guidance/about-the-price-paid-data"
ONTOLOGY="https://landregistry.data.gov.uk/def/ppi/"
OGL="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
IDS=("parcel_61523","parcel_61524","parcel_61525"); MAX_BYTES=1_048_576; LIMIT=20

def now(): return datetime.now(timezone.utc).isoformat()
def sha(v): return hashlib.sha256(v.encode() if isinstance(v,str) else v).hexdigest()
def write(path,obj):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+".tmp"); t.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8"); os.replace(t,p)

def points():
 d=json.loads(Path(PROBE).read_text()); b={r["parcel_id"]:r for r in d["canonical_points"]}; out={}
 for pid in IDS:
  r=b.get(pid)
  if not r or r.get("geometry_type")!="Point" or r.get("point_valid") is not True: raise ValueError(f"invalid canonical point {pid}")
  x,y=float(r["longitude"]),float(r["latitude"])
  if not(-180<=x<=180 and -90<=y<=90): raise ValueError(f"invalid coordinate {pid}")
  out[pid]={"longitude":x,"latitude":y}
 return out

def rows():
 d=json.loads(Path(INPUT).read_text()); b={r.get("parcel_id"):r for r in d.get("parcel_postcodes",[])}; out=[]
 for pid in IDS:
  r=b.get(pid)
  if not r or r.get("exact_parcel_bound") is not False: raise ValueError(f"invalid postcode row {pid}")
  pc=" ".join(str(r.get("postcode","")).upper().split())
  if not re.fullmatch(r"[A-Z]{1,2}\d[A-Z\d]?\s+\d[A-Z]{2}",pc): raise ValueError(f"invalid postcode {pid}")
  out.append({"parcel_id":pid,"postcode":pc,"exact_parcel_bound":False})
 return out

def query(pc):
 pc=pc.replace("\\","\\\\").replace('"','\\"')
 return f'''PREFIX ppd: <http://landregistry.data.gov.uk/def/ppi/>
PREFIX lrcommon: <http://landregistry.data.gov.uk/def/common/>
SELECT ?transaction ?address ?price ?date ?propertyType ?estateType ?newBuild ?paon ?saon ?street ?locality ?town ?district ?county ?postcode WHERE {{
?transaction ppd:propertyAddress ?address; ppd:pricePaid ?price; ppd:transactionDate ?date.
?address lrcommon:postcode "{pc}".
OPTIONAL {{?transaction ppd:propertyType ?propertyType.}} OPTIONAL {{?transaction ppd:estateType ?estateType.}} OPTIONAL {{?transaction ppd:newBuild ?newBuild.}}
OPTIONAL {{?address lrcommon:paon ?paon.}} OPTIONAL {{?address lrcommon:saon ?saon.}} OPTIONAL {{?address lrcommon:street ?street.}}
OPTIONAL {{?address lrcommon:locality ?locality.}} OPTIONAL {{?address lrcommon:town ?town.}} OPTIONAL {{?address lrcommon:district ?district.}}
OPTIONAL {{?address lrcommon:county ?county.}} OPTIONAL {{?address lrcommon:postcode ?postcode.}}
}} ORDER BY DESC(?date) LIMIT {LIMIT}'''

def value(b,k):
 v=b.get(k); return str(v.get("value")) if isinstance(v,dict) and v.get("value") is not None else None

def candidate(pid,pc,b,url):
 return {"parcel_id":pid,"searched_postcode":pc,"transaction_uri":value(b,"transaction"),"address_uri":value(b,"address"),"price_paid":value(b,"price"),"transaction_date":value(b,"date"),"property_type_uri":value(b,"propertyType"),"estate_type_uri":value(b,"estateType"),"new_build":value(b,"newBuild"),"paon":value(b,"paon"),"saon":value(b,"saon"),"street":value(b,"street"),"locality":value(b,"locality"),"town":value(b,"town"),"district":value(b,"district"),"county":value(b,"county"),"postcode":value(b,"postcode"),"source_url":url,"candidate_only":True,"transaction_time_characteristic_only":True,"exact_parcel_binding_claimed":False,"current_property_type_binding_claimed":False}

def run(timeout):
 points(); evidence=[]; candidates=[]
 for r in rows():
  q=query(r["postcode"]); url=ENDPOINT+"?"+urllib.parse.urlencode({"query":q,"output":"json"}); at=now()
  try:
   req=urllib.request.Request(url,headers={"Accept":"application/sparql-results+json, application/json","User-Agent":"TerraYield-AAYS/1.0 bounded HMLR PPD research"})
   with urllib.request.urlopen(req,timeout=timeout) as resp:
    raw=resp.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise ValueError("response exceeded 1 MiB")
    data=json.loads(raw.decode()); bindings=data.get("results",{}).get("bindings",[])
    if not isinstance(bindings,list): raise ValueError("SPARQL bindings missing")
    bindings=bindings[:LIMIT]; candidates += [candidate(r["parcel_id"],r["postcode"],b,url) for b in bindings]
    evidence.append({"parcel_id":r["parcel_id"],"source_url":url,"endpoint_url":ENDPOINT,"accessed_at":at,"content_sha256":sha(raw),"sha256_basis":"bounded_raw_sparql_json_response_bytes","query_sha256":sha(q),"record_scope":"one official HMLR Price Paid Data exact-postcode SPARQL query; newest 20 transactions maximum; max 1 MiB","supports_fields":["transaction URI","address URI","price paid","transaction date","property type at transaction time","estate type","new-build flag","PAON","SAON","street","locality","town","district","county","postcode"],"relevant_record_ids_or_excerpt":{"searched_postcode":r["postcode"],"binding_count":len(bindings),"transaction_uris":[value(b,"transaction") for b in bindings]},"guidance_url":GUIDANCE,"about_url":ABOUT,"ontology_url":ONTOLOGY,"license_or_terms_url":OGL,"http_status":getattr(resp,"status",None)})
  except Exception as exc:
   msg=f"HMLR_PRICE_PAID_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
   evidence.append({"parcel_id":r["parcel_id"],"source_url":url,"endpoint_url":ENDPOINT,"accessed_at":at,"content_sha256":sha(msg),"sha256_basis":"bounded_error_evidence_string","query_sha256":sha(q),"record_scope":"one official HMLR Price Paid Data exact-postcode SPARQL query; no bulk download","supports_fields":["HMLR Price Paid Data SPARQL endpoint availability"],"relevant_record_ids_or_excerpt":msg[:512],"guidance_url":GUIDANCE,"about_url":ABOUT,"ontology_url":ONTOLOGY,"license_or_terms_url":OGL,"http_status":getattr(exc,"code",None)})
 state="PRICE_PAID_TRANSACTION_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
 out={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":TASK_ID,"generated_at":now(),"state":state,"panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":list(IDS),"produced_candidate_rows":len(candidates),"candidate_rows":candidates,"source_evidence":evidence,"blocker":{"code":"NONE" if candidates else "HMLR_PRICE_PAID_SPARQL_NO_USABLE_RESPONSE_OR_NO_POSTCODE_TRANSACTIONS","state":state,"manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"VALIDATE_HMLR_PRICE_PAID_TRANSACTION_CANDIDATES_WITHOUT_EXACT_PARCEL_OR_CURRENT_PROPERTY_TYPE_INFERENCE" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_HMLR_PRICE_PAID_POSTCODE","large_data_downloaded":False,"bulk_download_performed":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"current_property_type_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}
 for p in OUT: write(p,out)
 return out

def validate():
 points(); rows()
 for p in (PROBE,INPUT,*OUT):
  if Path(p).is_absolute(): raise ValueError("relative paths required")
 if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/") or not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"): raise ValueError("output boundary")
 print("PASS_TARGET_3_HMLR_PRICE_PAID_EXACT_POSTCODE_SPARQL_LIMIT20_MAX1MIB_TRANSACTION_CHARACTERISTICS_ONLY")

def main():
 p=argparse.ArgumentParser(); p.add_argument("--timeout",type=float,default=20); p.add_argument("--validate-only",action="store_true"); a=p.parse_args()
 if a.validate_only: validate(); return
 r=run(a.timeout); print(json.dumps({"state":r["state"],"completed_count":r["completed_count"],"target_count":r["target_count"],"produced_candidate_rows":r["produced_candidate_rows"],"evidence_records":len(r["source_evidence"])},separators=(",",":")))
if __name__=="__main__": main()
