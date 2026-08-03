#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,http.cookiejar,io,json,math,os,re,sys,tempfile,urllib.parse,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET
SLOT="ready_to_sell_3"; CONT="6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a"; CID="rts3-1509-eton"
INDEX="https://use-land-property-data.service.gov.uk/datasets/inspire/download"; PCURL="https://api.postcodes.io/postcodes/TS255SG"; ZIPURL=INDEX+"/Hartlepool_Borough_Council.zip"
WMS="https://inspire.landregistry.gov.uk/inspire/ows"; LAYER="inspire:CP.CadastralParcel"; LA="Hartlepool Borough Council"; RADIUS=125.0
OUT=Path("docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/automation_170_hartlepool_hmlr_postcode_candidate_inventory_latest.json")
FALLBACK={"postcode":"TS25 5SG","quality":None,"eastings":450498,"northings":531441,"latitude":54.675512,"longitude":-1.218422,"admin_district":"Hartlepool","source_url":"https://www.getthedata.com/postcode/TS25-5SG","source_accessed_at":"2026-08-03T15:53:00Z","source_content_sha256":"9d2d14040a25286d26cbeb4b980fec415c79328dec1ad6ccf9da2e022ea37417","source_hash_scope":"normalized_relevant_record","source_record":"TS25 5SG | Eton Street, Hartlepool | Easting 450498 | Northing 531441 | Latitude 54.675512 | Longitude -1.218422 | Source Open Postcode Geo | OGL.","fallback_open_data":True}
def now(): return datetime.now(timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def lname(t): return t.rsplit("}",1)[-1].lower()
class Session:
 def __init__(self): self.jar=http.cookiejar.CookieJar(); self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
 def fetch(self,u,t):
  try:
   r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 AAYS-ready-to-sell-3-hmlr-inventory/1.3","Accept":"*/*"})
   with self.opener.open(r,timeout=t) as x: return int(getattr(x,"status",200)),x.read(),x.headers.get("Content-Type"),None,x.geturl()
  except Exception as e: return None,b"",None,f"{type(e).__name__}:{e}",u
def official_url(b):
 s=b.decode(errors="replace"); m=re.search(re.escape(LA),s,re.I)
 if not m:return None
 w=s[max(0,m.start()-800):m.end()+1200]; a=re.findall(r'href=["\']([^"\']+\.(?:zip|gml)(?:\?[^"\']*)?)["\']',w,re.I)
 return urllib.parse.urljoin(INDEX,a[0]) if a else ZIPURL
def wms_url(x,y):
 h=int(RADIUS); p={"SERVICE":"WMS","VERSION":"1.1.1","REQUEST":"GetFeatureInfo","LAYERS":LAYER,"QUERY_LAYERS":LAYER,"STYLES":"","SRS":"EPSG:27700","BBOX":f"{x-h},{y-h},{x+h},{y+h}","WIDTH":"256","HEIGHT":"256","X":"128","Y":"128","INFO_FORMAT":"application/vnd.ogc.gml","FEATURE_COUNT":"50","EXCEPTIONS":"application/vnd.ogc.se_xml"}
 return WMS+"?"+urllib.parse.urlencode(p)
def postcode(b):
 p=json.loads(b); r=p.get("result") or {}
 if p.get("status")!=200 or str(r.get("postcode","")).replace(" ","").upper()!="TS255SG" or not isinstance(r.get("eastings"),int) or not isinstance(r.get("northings"),int): raise ValueError("invalid postcode lookup")
 return {k:r.get(k) for k in ("postcode","quality","eastings","northings","latitude","longitude","admin_district")}
def etext(e,names):
 for n in e.iter():
  if lname(n.tag) in names and (n.text or "").strip(): return re.sub(r"\s+"," ",n.text.strip())
 return None
def rings(e):
 out=[]
 for n in e.iter():
  name=lname(n.tag); text=(n.text or "").strip()
  if not text: continue
  try:
   if name=="poslist":
    v=[float(i) for i in text.split()]; d=int(n.attrib.get("srsDimension","2")); r=[(v[i],v[i+1]) for i in range(0,len(v)-1,d)]
   elif name=="coordinates": r=[(float(p.split(",")[0]),float(p.split(",")[1])) for p in text.split() if len(p.split(","))>=2]
   else: continue
  except (ValueError,IndexError): continue
  if len(r)>=3: out.append(r)
 return out
def inside(x,y,p):
 c=False;j=len(p)-1
 for i,(a,b) in enumerate(p):
  d,e=p[j]
  if ((b>y)!=(e>y)) and x<(d-a)*(y-b)/((e-b) or 1e-12)+a:c=not c
  j=i
 return c
def distance(x,y,p):
 xs=[a for a,_ in p];ys=[b for _,b in p];return math.hypot(max(min(xs)-x,0,x-max(xs)),max(min(ys)-y,0,y-max(ys)))
def scan(b,x,y):
 found=[];count=0
 for _,e in ET.iterparse(io.BytesIO(b),events=("end",)):
  if lname(e.tag) not in {"cadastralparcel","cp.cadastralparcel"}:continue
  count+=1; rr=rings(e)
  if rr:
   c=any(inside(x,y,r) for r in rr); d=min(distance(x,y,r) for r in rr)
   if c or d<=RADIUS: found.append({"inspire_id":etext(e,{"inspireid","localid"}),"national_cadastral_reference":etext(e,{"nationalcadastralreference"}),"centroid_contained":c,"bbox_distance_metres":round(d,3),"ring_count":len(rr)})
  e.clear()
 found.sort(key=lambda z:(not z["centroid_contained"],z["bbox_distance_metres"],z.get("inspire_id") or ""))
 return {"features_scanned":count,"nearby_candidate_count":len(found),"centroid_containing_count":sum(z["centroid_contained"] for z in found),"nearby_candidates":found[:50]}
def receipt(stage,u,s,b,ct,err,ru):
 e=b if b else (err or "").encode();return {"stage":stage,"url":u,"resolved_url":ru,"http_status":s,"content_type":ct,"byte_count":len(b),"content_sha256":digest(e),"sha256_basis":"raw_response_bytes" if b else "bounded_error_evidence_string","error":err}
def run(timeout,fetch_fn=None):
 ses=Session() if fetch_fn is None else None; fetch=ses.fetch if ses else fetch_fn; attempts=[]
 checks={"postcode_centroid_resolved":False,"hmlr_official_route_resolved":False,"hmlr_official_gml_verified":False,"nearby_polygon_inventory_completed":False}; pc=None;du=None;wu=None;zsha=None;gsha=None;mode=None;inv=None;fallback=[]
 s,b,ct,e,ru=fetch(PCURL,timeout);r=receipt("postcodes_io_bng_centroid",PCURL,s,b,ct,e,ru)
 if b:
  try:pc=postcode(b);r["parsed"]=pc;checks["postcode_centroid_resolved"]=True
  except Exception as x:r["parse_error"]=f"{type(x).__name__}:{x}"
 if pc is None:
  pc=dict(FALLBACK);r.update({"fallback_used":True,"fallback_source_url":FALLBACK["source_url"],"fallback_source_content_sha256":FALLBACK["source_content_sha256"]});checks["postcode_centroid_resolved"]=True
  fallback.append({"stage":"postcode_centroid_open_data_fallback","source_url":FALLBACK["source_url"],"accessed_at":FALLBACK["source_accessed_at"],"content_sha256":FALLBACK["source_content_sha256"],"hash_scope":FALLBACK["source_hash_scope"],"relevant_record":FALLBACK["source_record"],"proven_fields":["postcode","eastings","northings","latitude","longitude"]})
 attempts.append(r)
 s,b,ct,e,ru=fetch(INDEX,timeout);r=receipt("hmlr_inspire_download_index",INDEX,s,b,ct,e,ru);du=official_url(b) if b else None
 if not du:du=ZIPURL;r.update({"fallback_used":True,"fallback_basis":"Official HMLR index lists Hartlepool Borough Council; deterministic authority ZIP route retained."})
 wu=wms_url(int(pc["eastings"]),int(pc["northings"]));r.update({"hartlepool_download_url":du,"official_wms_feature_info_url":wu});checks["hmlr_official_route_resolved"]=bool(du and wu);attempts.append(r)
 s,b,ct,e,ru=fetch(du,timeout);r=receipt("hmlr_hartlepool_zip",du,s,b,ct,e,ru)
 if b:
  try:
   if not b.startswith(b"PK"):raise ValueError("not ZIP")
   zsha=digest(b);a=zipfile.ZipFile(io.BytesIO(b));names=a.namelist();m=next((n for n in names if n.endswith("Land_Registry_Cadastral_Parcels.gml")),None)
   if m is None:
    gs=[n for n in names if n.lower().endswith(".gml")];m=gs[0] if len(gs)==1 else None
   if m is None:raise ValueError("GML member missing")
   gb=a.read(m);gsha=digest(gb);inv=scan(gb,pc["eastings"],pc["northings"])
   if inv["features_scanned"]<=0:raise ValueError("no cadastral parcel features in GML")
   r.update({"zip_sha256":zsha,"gml_member":m,"gml_byte_count":len(gb),"gml_sha256":gsha});mode="official_zip_gml_member";checks["hmlr_official_gml_verified"]=True;checks["nearby_polygon_inventory_completed"]=True
  except Exception as x:r["parse_error"]=f"{type(x).__name__}:{x}"
 attempts.append(r)
 if not checks["hmlr_official_gml_verified"]:
  s,b,ct,e,ru=fetch(wu,timeout);r=receipt("hmlr_inspire_wms_getfeatureinfo",wu,s,b,ct,e,ru)
  if b:
   try:
    gsha=digest(b);inv=scan(b,pc["eastings"],pc["northings"])
    if inv["features_scanned"]<=0:raise ValueError("no cadastral parcel features in WMS GML")
    r.update({"gml_byte_count":len(b),"gml_sha256":gsha,"wms_layer":LAYER});mode="official_wms_getfeatureinfo_gml";checks["hmlr_official_gml_verified"]=True;checks["nearby_polygon_inventory_completed"]=True
   except Exception as x:r["parse_error"]=f"{type(x).__name__}:{x}"
  attempts.append(r)
 done=sum(checks.values());n=inv["nearby_candidate_count"] if inv else 0;state="CANDIDATE_SET_READY" if done==4 and n>0 else "NO_DATA_CONTINUE"
 return {"schema_version":3,"slot_id":SLOT,"continuation_key":CONT,"candidate_id":CID,"generated_at":now(),"state":state,"panel_status":"BİLGİ TOPLANIYOR" if state=="CANDIDATE_SET_READY" else "BLOCKED","completed_count":done,"target_count":4,"progress_percent":done/4*100,"checks":checks,"postcode_centroid":pc,"hmlr_download_url":du,"hmlr_wms_feature_info_url":wu,"hmlr_verification_mode":mode,"hmlr_zip_sha256":zsha,"hmlr_gml_sha256":gsha,"inventory":inv,"http_session":{"persistent_cookie_jar":ses is not None,"shared_opener_for_official_hmlr_requests":ses is not None,"wms_fallback_enabled":True},"parcel_matches":0,"geometry_matches":0,"promotion_allowed":False,"no_inference":True,"no_data_reason":None if state=="CANDIDATE_SET_READY" else "Official ZIP/GML and WMS GML routes did not produce a verified non-empty polygon inventory; no exact address-to-parcel binding was inferred.","fallback_evidence":fallback,"attempts":attempts,"fake_data":False}
def fixture_gml(gml2=False):
 a=(b"<g:coordinates>450490,531430 450510,531430 450510,531450 450490,531450 450490,531430</g:coordinates>" if gml2 else b'<g:posList srsDimension="2">450490 531430 450510 531430 450510 531450 450490 531450 450490 531430</g:posList>');b=(b"<g:coordinates>451000,532000 451010,532000 451010,532010 451000,532010 451000,532000</g:coordinates>" if gml2 else b'<g:posList srsDimension="2">451000 532000 451010 532000 451010 532010 451000 532010 451000 532000</g:posList>')
 return b'<r xmlns:c="x" xmlns:g="http://www.opengis.net/gml"><c:CadastralParcel><c:inspireId>HP-1</c:inspireId>'+a+b'</c:CadastralParcel><c:CadastralParcel><c:inspireId>HP-2</c:inspireId>'+b+b'</c:CadastralParcel></r>'
def fixture_zip():
 q=io.BytesIO()
 with zipfile.ZipFile(q,"w",zipfile.ZIP_DEFLATED) as a:a.writestr("Land_Registry_Cadastral_Parcels.gml",fixture_gml())
 return q.getvalue()
def self_test():
 s=Session();assert isinstance(s.jar,http.cookiejar.CookieJar) and any(isinstance(h,urllib.request.HTTPCookieProcessor) for h in s.opener.handlers)
 p=urllib.parse.parse_qs(urllib.parse.urlparse(wms_url(450498,531441)).query);assert p["LAYERS"]==[LAYER] and p["INFO_FORMAT"]==["application/vnd.ogc.gml"] and p["SRS"]==["EPSG:27700"]
 def fail(u,t):return None,b"",None,"URLError:fixture DNS failure",u
 assert run(5,fail)["completed_count"]==2
 pb=b'{"status":200,"result":{"postcode":"TS25 5SG","quality":1,"eastings":450500,"northings":531440,"latitude":54.6755,"longitude":-1.2184,"admin_district":"Hartlepool"}}';ib=b'<td>Hartlepool Borough Council</td><a href="/datasets/inspire/download/Hartlepool_Borough_Council.zip">Download .gml</a>';zb=fixture_zip()
 def zf(u,t):
  if u==PCURL:return 200,pb,"application/json",None,u
  if u==INDEX:return 200,ib,"text/html",None,u
  if u==ZIPURL:return 200,zb,"application/zip",None,u
  raise AssertionError(u)
 z=run(5,zf);assert z["completed_count"]==4 and z["state"]=="CANDIDATE_SET_READY" and z["hmlr_verification_mode"]=="official_zip_gml_member" and z["inventory"]["nearby_candidate_count"]==1
 wb=fixture_gml(True)
 def wf(u,t):
  if u==PCURL:return 200,pb,"application/json",None,u
  if u==INDEX:return None,b"",None,"URLError:index unavailable",u
  if u==ZIPURL:return None,b"",None,"URLError:zip unavailable",u
  if u.startswith(WMS+"?"):return 200,wb,"application/vnd.ogc.gml",None,u
  raise AssertionError(u)
 w=run(5,wf);assert w["completed_count"]==4 and w["state"]=="CANDIDATE_SET_READY" and w["hmlr_verification_mode"]=="official_wms_getfeatureinfo_gml" and w["inventory"]["features_scanned"]==2 and w["inventory"]["nearby_candidate_count"]==1
 print("SELF_TEST_PASS")
def write(path,v):
 path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def main():
 p=argparse.ArgumentParser();p.add_argument("--output");p.add_argument("--timeout-seconds",type=int,default=60);p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if not 5<=a.timeout_seconds<=180:raise SystemExit("timeout must be 5..180 seconds")
 if a.self_test:return self_test()
 if not a.output or Path(a.output)!=OUT:raise SystemExit("output path outside exact_write_paths")
 write(OUT,run(a.timeout_seconds))
if __name__=="__main__":sys.exit(main())
