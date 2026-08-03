#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,pathlib,re,tempfile,urllib.parse,urllib.request
from datetime import datetime,timezone

INPUT=pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
MANIFEST=pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/gla_lbsm2_lambeth_exact_uprn_source_manifest_20260803.json")
OUTPUTS=[
 pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/gla_lbsm2_lambeth_exact_uprn_result_latest.json"),
 pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/gla_lbsm2_lambeth_exact_uprn_latest.json")]
MAX_META=8*1024*1024; MAX_CSV=128*1024*1024
HOSTS=(".london.gov.uk",".datapress.com",".amazonaws.com",".blob.core.windows.net")
KEEP=("uprn","address","postcode","propertytype","builtform","constructionage","floorarea","energyrating","heating","habitableroom","lodgement","inspection","source","model","confidence","tenure","localauthority")

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(s): return re.sub(r"[^a-z0-9]","",str(s).casefold())
def uprn(v):
 s=str(v or "").strip()
 if s.endswith(".0") and s[:-2].isdigit(): s=s[:-2]
 return re.sub(r"\D","",s)
def write(p,t):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=p.parent,delete=False) as f: f.write(t); q=pathlib.Path(f.name)
 q.replace(p)
def safe(url,meta=False):
 x=urllib.parse.urlsplit(url); h=(x.hostname or "").casefold()
 if x.scheme!="https" or x.username or x.password or x.fragment: raise RuntimeError("UNSAFE_URL:"+url)
 if meta and h!="data.london.gov.uk": raise RuntimeError("UNTRUSTED_METADATA_HOST:"+h)
 if not meta and h!="data.london.gov.uk" and not any(h.endswith(s) for s in HOSTS): raise RuntimeError("UNTRUSTED_RESOURCE_HOST:"+h)
 return url
def fetch(url,timeout,limit,meta=False):
 safe(url,meta); r=urllib.request.Request(url,headers={"User-Agent":"AAYS-parcel-label-3/1.0"})
 with urllib.request.urlopen(r,timeout=timeout) as z:
  final=z.geturl(); safe(final,meta and urllib.parse.urlsplit(final).hostname=="data.london.gov.uk")
  out=bytearray()
  while True:
   b=z.read(min(1024*1024,limit-len(out)+1))
   if not b: break
   out.extend(b)
   if len(out)>limit: raise RuntimeError(f"RESPONSE_TOO_LARGE:{len(out)}:{limit}")
  return bytes(out),final,int(getattr(z,"status",200))
def rows():
 p=json.loads(INPUT.read_text()); a=p.get("records",[])
 if len(a)!=3: raise RuntimeError(f"EXPECTED_3_INPUT_ROWS:{len(a)}")
 out=[]
 for x in a:
  req=("parcel_id","UPRN","FULLADDRESS","POSTCODE","longitude","latitude")
  if not x.get("exact_uprn_bound") or any(k not in x for k in req): raise RuntimeError("INVALID_INPUT_ROW")
  u=uprn(x["UPRN"])
  out.append({k:x[k] for k in req}|{"UPRN":u,"exact_uprn_bound":True})
 if len({x["UPRN"] for x in out})!=3: raise RuntimeError("INPUT_UPRNS_NOT_UNIQUE")
 return out
def manifest():
 p=json.loads(MANIFEST.read_text())
 if p.get("dataset_id")!="2k55d" or p.get("target_resource_name")!="London Building Stock Model 2 - Lambeth": raise RuntimeError("WRONG_MANIFEST_SCOPE")
 for s in p.get("sources",[]):
  e=s.get("retained_excerpt","")
  if not e or sha(e.encode())!=s.get("retained_excerpt_sha256"): raise RuntimeError("MANIFEST_EXCERPT_SHA_MISMATCH")
 if len(p.get("sources",[]))<4: raise RuntimeError("SOURCE_MANIFEST_INCOMPLETE")
 return p
def resources(p):
 for v in (p.get("resources"),(p.get("result") or {}).get("resources"),(p.get("dataset") or {}).get("resources"),(p.get("data") or {}).get("resources")):
  if isinstance(v,list): return [x for x in v if isinstance(x,dict)]
 raise RuntimeError("METADATA_RESOURCES_NOT_FOUND")
def pick(rs,target):
 m=[]
 for x in rs:
  n=str(x.get("name") or x.get("title") or x.get("label") or x.get("filename") or x.get("fileName") or "")
  u=str(x.get("url") or x.get("download_url") or x.get("downloadUrl") or x.get("href") or "")
  f=str(x.get("format") or x.get("file_type") or x.get("mimetype") or "")
  if u and "londonbuildingstockmodel2lambeth" in norm(n) and ("csv" in f.casefold() or u.split("?",1)[0].casefold().endswith(".csv")):
   safe(u); m.append((x,n,u))
 if len(m)!=1: raise RuntimeError(f"LAMBETH_RESOURCE_AMBIGUOUS_OR_MISSING:{len(m)}")
 return m[0]
def decode(b):
 for e in ("utf-8-sig","utf-8","cp1252"):
  try:return b.decode(e),e
  except UnicodeDecodeError: pass
 raise RuntimeError("CSV_DECODE_FAILED")
def scan(b,targets):
 t,e=decode(b); r=csv.DictReader(io.StringIO(t)); fs=list(r.fieldnames or [])
 if not fs: raise RuntimeError("CSV_HEADER_MISSING")
 col=next((f for f in fs if norm(f) in {"uprn","uniquepropertyreferencenumber","uprnnumber"}),None) or next((f for f in fs if "uprn" in norm(f)),None)
 if not col: raise RuntimeError("UPRN_COLUMN_NOT_FOUND")
 hit={u:[] for u in targets}; count=0
 for row in r:
  count+=1; u=uprn(row.get(col))
  if u in hit and len(hit[u])<3:
   raw=json.dumps({str(k):str(v) for k,v in row.items()},ensure_ascii=False,separators=(",",":"),sort_keys=True)
   kept={k:str(v).strip()[:500] for k,v in row.items() if str(v or "").strip() and any(q in norm(k) for q in KEEP)}
   hit[u].append({"raw_row_sha256":sha(raw.encode()),"retained_fields":dict(list(kept.items())[:40])})
 return hit,{"encoding":e,"rows_scanned":count,"field_count":len(fs),"field_names":fs[:200],"uprn_column":col}
def synthetic(a):
 meta={"success":True,"result":{"resources":[{"name":"London Building Stock Model 2 - Lambeth","format":"CSV","url":"https://data.london.gov.uk/download/test/lbsm2.csv"}]}}
 s=io.StringIO(); w=csv.DictWriter(s,fieldnames=["UPRN","Address","Postcode","Property Type","Property Type Source","Property Type Modelled"]); w.writeheader()
 for i,x in enumerate(a): w.writerow({"UPRN":x["UPRN"],"Address":x["FULLADDRESS"],"Postcode":x["POSTCODE"],"Property Type":"Flat" if i==0 else "House","Property Type Source":"Synthetic","Property Type Modelled":"False"})
 return json.dumps(meta).encode(),s.getvalue().encode()
def run(a,m,timeout,synth=False):
 ev={"dataset_page_url":m["sources"][0]["url"],"metadata_api_urls":m["metadata_api_urls"],"target_resource_name":m["target_resource_name"],"dataset_reference_date":m["dataset_reference_date"],"accessed_at":now(),"metadata_attempts":[],"network_requests":0}
 if synth:
  mb,cb=synthetic(a); mf=m["metadata_api_urls"][0]; ms=200; x,n,cu=pick(resources(json.loads(mb)),m["target_resource_name"]); cf=cu; cs=200
 else:
  last=None
  for api in m["metadata_api_urls"]:
   try:
    ev["network_requests"]+=1; mb,mf,ms=fetch(api,timeout,MAX_META,True)
    ev["metadata_attempts"].append({"url":api,"final_url":mf,"http_status":ms,"bytes":len(mb),"content_sha256":sha(mb),"state":"RESPONSE"})
    x,n,cu=pick(resources(json.loads(mb)),m["target_resource_name"]); break
   except Exception as z: last=z; ev["metadata_attempts"].append({"url":api,"state":"ERROR","error":f"{type(z).__name__}:{z}"})
  else: raise RuntimeError(f"ALL_METADATA_ENDPOINTS_FAILED:{type(last).__name__}:{last}")
  ev["selected_resource_record"]=x; ev["network_requests"]+=1; cb,cf,cs=fetch(cu,timeout,MAX_CSV)
 hit,st=scan(cb,{x["UPRN"] for x in a})
 ev|={"metadata_final_url":mf,"metadata_http_status":ms,"metadata_bytes":len(mb),"metadata_content_sha256":sha(mb),"csv_final_url":cf,"csv_http_status":cs,"csv_bytes":len(cb),"csv_content_sha256":sha(cb),"scan_stats":st}
 out=[]; matched=0
 for x in a:
  c=hit[x["UPRN"]]; z=x|{"source_url":cf,"candidate_count":len(c),"inferred":False,"modelled_values_verified":False}
  if len(c)==1: z|={"state":"MATCHED_EXACT_UPRN"}|c[0]; matched+=1
  elif len(c)>1: z|={"state":"NO_DATA","reason":"AMBIGUOUS_DUPLICATE_EXACT_UPRN_ROWS","candidate_row_sha256":[q["raw_row_sha256"] for q in c]}
  else: z|={"state":"NO_DATA","reason":"EXACT_UPRN_NOT_FOUND"}
  out.append(z)
 return ev,out,matched
def main():
 p=argparse.ArgumentParser(); p.add_argument("--timeout",type=int,default=30); p.add_argument("--validate-only",action="store_true"); p.add_argument("--synthetic-test",action="store_true"); q=p.parse_args()
 if not 1<=q.timeout<=300: raise RuntimeError("INVALID_TIMEOUT")
 a=rows(); m=manifest()
 if q.validate_only:
  print(json.dumps({"valid":True,"input_count":3,"target_uprns":[x["UPRN"] for x in a],"dataset_id":"2k55d","target_resource_name":m["target_resource_name"],"resource_class":"network","max_metadata_bytes":MAX_META,"max_csv_bytes":MAX_CSV,"write_paths":[str(x) for x in OUTPUTS]},sort_keys=True)); return 0
 if q.synthetic_test:
  ev,o,n=run(a,m,q.timeout,True)
  if n!=3: raise RuntimeError("SYNTHETIC_MATCH_COUNT")
  print(json.dumps({"valid":True,"matched_exact_uprn_rows":3,"candidate_counts":[x["candidate_count"] for x in o],"metadata_sha256":ev["metadata_content_sha256"],"csv_sha256":ev["csv_content_sha256"],"uprn_column":ev["scan_stats"]["uprn_column"]},sort_keys=True)); return 0
 try: ev,o,n=run(a,m,q.timeout)
 except Exception as z:
  ev={"dataset_page_url":m["sources"][0]["url"],"metadata_api_urls":m["metadata_api_urls"],"target_resource_name":m["target_resource_name"],"dataset_reference_date":m["dataset_reference_date"],"accessed_at":now(),"error":f"{type(z).__name__}:{z}"}
  o=[x|{"source_url":m["sources"][0]["url"],"candidate_count":0,"state":"NO_DATA","reason":ev["error"],"inferred":False,"modelled_values_verified":False} for x in a]; n=0
 state="PUBLISHED" if n else "NO_DATA_CONTINUE"
 d={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":"parcel-label-3-gla-lbsm2-lambeth-exact-uprn-v1-20260803","state":state,"panel_status":"PUBLISHED","completed_count":len(o),"target_count":3,"previous_percent":0.0,"progress_percent":round(len(o)/3*100,6),"percent_increase":round(len(o)/3*100,6),"matched_exact_uprn_rows":n,"evidence_records":len(o),"source_evidence":ev,"records":o,"modelled_values_promoted_as_verified":False,"large_raw_files_committed":False,"fake_data":False,"generated_at":now()}
 t=json.dumps(d,ensure_ascii=False,separators=(",",":"),sort_keys=True)+"\n"
 for x in OUTPUTS: write(x,t)
 print(json.dumps({"completed_count":len(o),"target_count":3,"matched_exact_uprn_rows":n,"state":state,"output_sha256":sha(t.encode())},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
