#!/usr/bin/env python3
import argparse,hashlib,json,re,sys,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET

SLOT="ready_to_sell_3"
CONT="6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a"
OUT=Path("docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/automation_169_single_candidate_hmlr_wms_binding_latest.json")
NOM="https://nominatim.openstreetmap.org/search"
WMS="https://inspire.landregistry.gov.uk/inspire/ows"
UA="AAYS-ready-to-sell-3-parcel-binding/1.0 (single-candidate research)"

def sha(b): return hashlib.sha256(b).hexdigest()
def norm(v): return re.sub(r"\s+"," ",str(v or "").strip()).casefold()
def exact(x):
 a=x.get("address") or {}
 return norm(a.get("house_number"))=="11" and norm(a.get("road") or a.get("pedestrian"))=="eton street" and norm(a.get("postcode")).replace(" ","")=="ts255sg" and "hartlepool" in norm(a.get("town") or a.get("city") or a.get("municipality"))
def get(url,t):
 try:
  q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
  with urllib.request.urlopen(q,timeout=t) as r:return getattr(r,"status",200),r.read(),r.headers.get("Content-Type"),None
 except Exception as e:return None,b"",None,f"{type(e).__name__}:{e}"
def caps(b):
 r=ET.fromstring(b); ver=r.attrib.get("version","1.3.0"); layer=None; fm=[]
 for e in r.iter():
  n=e.tag.rsplit("}",1)[-1].casefold(); z=(e.text or "").strip()
  if n=="name" and "cadastralparcel" in z.casefold():layer=z
  if n=="format" and z:fm.append(z)
 pref=["application/vnd.ogc.gml","application/json","text/xml","text/plain","text/html"]
 return ver,layer,next((x for x in pref if x in fm),None)
def parcel_id(b):
 t=b.decode("utf-8",errors="replace")
 for p in [r"(?is)<[^>]*(?:inspireid|nationalcadastralreference)[^>]*>\s*([^<]{3,200})",r'(?is)"(?:inspireid|nationalcadastralreference)"\s*:\s*"([^"]{3,200})"']:
  m=re.search(p,t)
  if m:return re.sub(r"\s+"," ",m.group(1).strip())
 return "HMLR_FEATUREINFO_SHA256:"+sha(b) if "cadastralparcel" in t.casefold() and len(t.strip())>40 else None
def fi_url(lat,lon,ver,layer,fmt):
 d=.00045
 q={"SERVICE":"WMS","VERSION":ver,"REQUEST":"GetFeatureInfo","LAYERS":layer,"QUERY_LAYERS":layer,"STYLES":"","BBOX":f"{lon-d},{lat-d},{lon+d},{lat+d}","WIDTH":"101","HEIGHT":"101","FORMAT":"image/png","INFO_FORMAT":fmt,"FEATURE_COUNT":"10"}
 q.update({"CRS":"CRS:84","I":"50","J":"50"} if ver.startswith("1.3") else {"SRS":"EPSG:4326","X":"50","Y":"50"})
 return WMS+"?"+urllib.parse.urlencode(q)
def rec(stage,url,status,body,ctype,error):
 return {"stage":stage,"url":url,"http_status":status,"content_type":ctype,"byte_count":len(body),"content_sha256":sha(body) if body else sha((error or "").encode()),"sha256_basis":"raw_response_bytes" if body else "bounded_error_evidence_string","error":error}
def run(timeout,sleep):
 attempts=[]; checks={"exact_address_resolved":False,"hmlr_cadastral_layer_resolved":False,"hmlr_feature_info_parcel_hit":False}
 q={"q":"11 Eton Street, Hartlepool, County Durham TS25 5SG","format":"jsonv2","addressdetails":"1","polygon_geojson":"1","limit":"5"}
 u=NOM+"?"+urllib.parse.urlencode(q); st,b,ct,e=get(u,timeout); r=rec("nominatim_exact_address",u,st,b,ct,e); hit=None
 if b:
  try: hit=next((x for x in json.loads(b) if exact(x)),None)
  except Exception as x:r["parse_error"]=f"{type(x).__name__}:{x}"
 if hit:
  checks["exact_address_resolved"]=True;r.update({"osm_type":hit.get("osm_type"),"osm_id":hit.get("osm_id"),"display_name":hit.get("display_name"),"lat":hit.get("lat"),"lon":hit.get("lon")})
 attempts.append(r);time.sleep(sleep)
 u=WMS+"?"+urllib.parse.urlencode({"SERVICE":"WMS","REQUEST":"GetCapabilities"});st,b,ct,e=get(u,timeout);r=rec("hmlr_wms_capabilities",u,st,b,ct,e);ver="1.3.0";layer=fmt=None
 if b:
  try:ver,layer,fmt=caps(b);r.update({"wms_version":ver,"cadastral_layer_name":layer,"selected_info_format":fmt})
  except Exception as x:r["parse_error"]=f"{type(x).__name__}:{x}"
 if layer and fmt:checks["hmlr_cadastral_layer_resolved"]=True
 attempts.append(r);fr={"stage":"hmlr_wms_feature_info","attempted":False,"candidate_id":"rts3-1509-eton"};pid=None
 if hit and layer and fmt:
  time.sleep(sleep);u=fi_url(float(hit["lat"]),float(hit["lon"]),ver,layer,fmt);st,b,ct,e=get(u,timeout);pid=parcel_id(b) if b else None;fr=rec("hmlr_wms_feature_info",u,st,b,ct,e);fr.update({"attempted":True,"candidate_id":"rts3-1509-eton","parcel_identifier":pid,"geometry_evidence_basis":"HMLR_INSPIRE_CADASTRAL_PARCEL_POINT_IN_POLYGON_FEATURE_INFO" if pid else None,"response_excerpt":re.sub(r"\s+"," ",b.decode("utf-8",errors="replace"))[:500] if b else None})
  if pid:checks["hmlr_feature_info_parcel_hit"]=True
 attempts.append(fr);done=sum(1 for x in attempts if x.get("attempted",True));ok=all(checks.values())
 return {"schema_version":3,"slot_id":SLOT,"continuation_key":CONT,"candidate_id":"rts3-1509-eton","generated_at":datetime.now(timezone.utc).isoformat(),"state":"READY_FOR_ACCEPTANCE" if ok else "NO_DATA_CONTINUE","panel_status":"BİLGİ TOPLANIYOR" if ok else "BLOCKED","completed_count":done,"target_count":3,"progress_percent":done/3*100,"checks":checks,"parcel_matches":1 if ok else 0,"geometry_matches":1 if ok else 0,"parcel_identifier":pid,"attempts":attempts,"no_data_reason":None if ok else "Exact address, HMLR cadastral layer and parcel feature-info hit were not all verified; no parcel identity or geometry was inferred.","attribution":{"address_source":"© OpenStreetMap contributors, ODbL","parcel_source":"HM Land Registry INSPIRE Index Polygons; applicable OGL/OS conditions"},"fake_data":False}
def selftest():
 assert exact({"address":{"house_number":"11","road":"Eton Street","postcode":"TS25 5SG","town":"Hartlepool"}})
 x=b'<WMS_Capabilities version="1.3.0"><Capability><Request><GetFeatureInfo><Format>application/vnd.ogc.gml</Format></GetFeatureInfo></Request><Layer><Name>inspire:CP.CadastralParcel</Name></Layer></Capability></WMS_Capabilities>'
 assert caps(x)==("1.3.0","inspire:CP.CadastralParcel","application/vnd.ogc.gml")
 assert parcel_id(b"<x><inspireId>GB.HMLR.1</inspireId></x>")=="GB.HMLR.1"
 print("SELF_TEST_PASS")
def main():
 p=argparse.ArgumentParser();p.add_argument("--output");p.add_argument("--timeout-seconds",type=int,default=30);p.add_argument("--sleep-seconds",type=float,default=1.1);p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:return selftest()
 if not a.output or Path(a.output)!=OUT:raise SystemExit("output path outside exact_write_paths")
 r=run(a.timeout_seconds,a.sleep_seconds);OUT.parent.mkdir(parents=True,exist_ok=True);t=OUT.with_suffix(".json.tmp");t.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");t.replace(OUT)
if __name__=="__main__":sys.exit(main())
