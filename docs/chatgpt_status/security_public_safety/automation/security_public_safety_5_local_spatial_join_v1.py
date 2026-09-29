from __future__ import annotations
import hashlib,json,os,re,subprocess,tempfile,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
PRIOR_BLOB="0f7053992b3d3f2bcd6f4783f332535577c610dc"
POINT_BRANCH="codex/aays-single-runner-v5-20260706"
POINT_REL="england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
POINT_BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
WMS="https://inspire.landregistry.gov.uk/inspire/ows"
LAYER="inspire:CP.CadastralParcel"
WINDOW="hmlr_inspire_wms_getfeatureinfo_epsg4326_sps5_9_v2"
REQ=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]
def sha(b):return hashlib.sha256(b).hexdigest()
def git(a,t=900,o=None):return subprocess.run(["git","-C",str(REPO),*a],stdout=o if o is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=t)
def gblob(p):r=git(["hash-object",str(p)],180);return r.stdout.decode().strip() if r.returncode==0 else None
def materialize():
 p=Path(tempfile.gettempdir())/"aays_sps5"/Path(POINT_REL).name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.is_file() and gblob(p)==POINT_BLOB:return p
 for ref in (f"origin/{POINT_BRANCH}",POINT_BRANCH):
  q=p.with_suffix(".part");q.unlink(missing_ok=True)
  with q.open("wb") as fh:r=git(["show",f"{ref}:{POINT_REL}"],o=fh)
  if r.returncode==0 and gblob(q)==POINT_BLOB:os.replace(q,p);return p
  q.unlink(missing_ok=True)
 r=git(["fetch","origin",POINT_BRANCH])
 if r.returncode==0:
  q=p.with_suffix(".part")
  with q.open("wb") as fh:s=git(["show",f"FETCH_HEAD:{POINT_REL}"],o=fh)
  if s.returncode==0 and gblob(q)==POINT_BLOB:os.replace(q,p);return p
  q.unlink(missing_ok=True)
 return None
def pointmap(fc):
 d={}
 for f in fc.get("features",[]):
  p=f.get("properties") or {};pid=p.get("security_parcel_id") or p.get("parcel_id");g=f.get("geometry") or {}
  if isinstance(pid,str) and pid.startswith("parcel_") and g.get("type")=="Point" and len(g.get("coordinates") or [])>=2:d[pid]=(float(g["coordinates"][0]),float(g["coordinates"][1]))
 return d
def ln(t):return t.rsplit("}",1)[-1] if "}" in t else t
def vals(s):
 z=[]
 for x in re.split(r"[\s,]+",(s or "").strip()):
  try:z.append(float(x))
  except:pass
 return z
def ring(e):
 for x in e.iter():
  if ln(x.tag)=="posList" and x.text:
   a=vals(x.text);dim=int(x.attrib.get("srsDimension") or 2);return [[a[i],a[i+1]] for i in range(0,len(a)-1,dim)]
  if ln(x.tag)=="coordinates" and x.text:
   q=[]
   for tok in x.text.split():
    p=tok.split(",")
    if len(p)>=2:
     try:q.append([float(p[0]),float(p[1])])
     except:pass
   if q:return q
 return []
def parse(body):
 root=ET.fromstring(body);members=[x for x in root.iter() if ln(x.tag) in ("featureMember","member")] or [root];out=[]
 for m in members:
  props={}
  for x in m.iter():
   if len(list(x))==0 and x.text and x.text.strip():props.setdefault(ln(x.tag),[]).append(x.text.strip())
  ids=[]
  for k,vs in props.items():
   kl=k.lower()
   if ("inspire" in kl and "id" in kl) or kl in ("inspireid","nationalcadastralreference","reference"):ids+=vs
  polys=[];srs=[]
  for p in m.iter():
   if ln(p.tag)!="Polygon":continue
   sr=next((x.attrib.get("srsName") for x in p.iter() if x.attrib.get("srsName")),None);srs.append(sr);outer=None;holes=[]
   for c in p:
    if ln(c.tag) in ("exterior","outerBoundaryIs"):outer=ring(c)
    elif ln(c.tag) in ("interior","innerBoundaryIs"):
     h=ring(c)
     if h:holes.append(h)
   if not outer:outer=ring(p)
   if outer:
    for r in [outer,*holes]:
     if r[0]!=r[-1]:r.append(r[0])
    polys.append([outer,*holes])
  g={"type":"Polygon","coordinates":polys[0]} if len(polys)==1 else ({"type":"MultiPolygon","coordinates":polys} if len(polys)>1 else None)
  if ids or g:out.append({"ids":list(dict.fromkeys(ids)),"props":props,"geometry":g,"srs":srs})
 return out
def iswgs(g):
 if not g:return False
 ps=[g["coordinates"]] if g["type"]=="Polygon" else g["coordinates"]
 return all(abs(p[0])<=180 and abs(p[1])<=90 for poly in ps for r in poly for p in r)
def pir(x,y,r):
 inside=False;j=len(r)-1
 for i in range(len(r)):
  xi,yi=r[i][:2];xj,yj=r[j][:2]
  if ((yi>y)!=(yj>y)) and yj!=yi and x<(xj-xi)*(y-yi)/(yj-yi)+xi:inside=not inside
  j=i
 return inside
def pig(x,y,g):
 ps=[g["coordinates"]] if g["type"]=="Polygon" else g["coordinates"]
 return any(poly and pir(x,y,poly[0]) and not any(pir(x,y,h) for h in poly[1:]) for poly in ps)
def sem(f):
 r=[];g=f.get("geometry") or {};p=f.get("properties") or {}
 if g.get("type") not in ("Polygon","MultiPolygon"):r.append("GEOMETRY_MUST_BE_POLYGON_OR_MULTIPOLYGON")
 for k in REQ:
  if p.get(k) in (None,"",[]):r.append("MISSING_"+k)
 for k in ("parcel_id","accepted_parcel"):
  if k in p:r.append("FORBIDDEN_"+k)
 return r
def save(o):OUT.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
 base={"schema_version":8,"slot_id":"security_public_safety_5","lineage_id":"86b5e932de484ad26133fa8c","source_window_id":WINDOW,"first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","accepted_count_claimed":0,"final_package_written":False,"fake_data":False}
 if not OUT.is_file() or gblob(OUT)!=PRIOR_BLOB:
  base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=0,valid_count=0,rejected_count=0,semantic_precheck_passed=False,delivery_blocked="PRODUCER_SCHEMA_INVALID",error="PRIOR_OUTPUT_BLOB_MISMATCH",records_geojson={"type":"FeatureCollection","features":[]},rejections=[]);save(base);return 0
 prior=json.loads(OUT.read_text(encoding="utf-8-sig"));fs=(prior.get("records_geojson") or {}).get("features") or []
 targets=[]
 for f in fs:
  p=f.get("properties") or {};ref=str(p.get("canonical_parcel_reference") or "");pid=str(p.get("partition_record_id") or "")
  if ref and pid:targets.append((ref,pid,p))
 pf=materialize()
 if len(targets)!=9 or not pf:
  base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=len(targets),valid_count=0,rejected_count=len(targets),semantic_precheck_passed=False,delivery_blocked="PRODUCER_SCHEMA_INVALID",error="TARGET_OR_POINT_PREFLIGHT_FAILED",records_geojson={"type":"FeatureCollection","features":[]},rejections=[]);save(base);return 0
 pts=pointmap(json.loads(pf.read_text(encoding="utf-8-sig")));features=[];reject=[];requests=[]
 for i,(ref,pid,pp) in enumerate(targets,1):
  pt=pts.get(pid);reasons=[];chosen=None;ev={"http_status":None}
  if not pt:reasons.append("CANONICAL_POINT_NOT_FOUND")
  else:
   dx,dy=.00035,.00025
   q={"SERVICE":"WMS","VERSION":"1.1.1","REQUEST":"GetFeatureInfo","LAYERS":LAYER,"QUERY_LAYERS":LAYER,"STYLES":"","SRS":"EPSG:4326","BBOX":f"{pt[0]-dx:.8f},{pt[1]-dy:.8f},{pt[0]+dx:.8f},{pt[1]+dy:.8f}","WIDTH":"101","HEIGHT":"101","X":"50","Y":"50","INFO_FORMAT":"application/vnd.ogc.gml","FEATURE_COUNT":"20","EXCEPTIONS":"application/vnd.ogc.se_xml"}
   url=WMS+"?"+urllib.parse.urlencode(q)
   try:
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-SPS5/HMLR-WMS-EPSG4326-v2","Accept":"application/vnd.ogc.gml,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(req,timeout=90) as resp:body=resp.read();ev={"url":resp.geturl(),"http_status":int(resp.status),"content_type":resp.headers.get("Content-Type"),"sha256":sha(body),"size_bytes":len(body)}
    cs=parse(body)
   except Exception as e:ev={"url":url,"http_status":None,"error":str(e)};cs=[]
   exact=[c for c in cs if ref in {str(v).strip() for v in c["ids"]} and c.get("geometry")]
   if len(exact)!=1:reasons.append("EXACT_INSPIRE_ID_WITH_GEOMETRY_COUNT_"+str(len(exact)))
   else:
    chosen=exact[0]
    if not iswgs(chosen["geometry"]):reasons.append("WMS_GEOMETRY_NOT_WGS84")
    elif not pig(pt[0],pt[1],chosen["geometry"]):reasons.append("CANONICAL_POINT_NOT_INSIDE_WMS_POLYGON")
  requests.append({"partition_record_id":pid,"target_reference":ref,**ev})
  fe=pp.get("field_evidence") or {};sec={k:v for k,v in fe.items() if k in ("security_source","official_csv_sha256","lsoa_code","official_lsoa_row_count","official_crime_value_sum","official_numeric_cells")}
  if not sec.get("official_csv_sha256") or not sec.get("lsoa_code"):reasons.append("PRIOR_FIELD_EVIDENCE_INCOMPLETE")
  if not reasons and chosen:
   p={"evidence_scope":"parcel","coverage_area_id":pp.get("coverage_area_id"),"source_resolution":"HMLR_INSPIRE_WMS_GetFeatureInfo_with_MPS_LSOA_recorded_crime","time_window":pp.get("time_window"),"source_url":pp.get("source_url"),"measurement_date":pp.get("measurement_date"),"measurement_method":"official_MPS_LSOA_CSV_exact_identifier_join","spatial_binding_method":"local_canonical_point_inside_exact_HMLR_WMS_GML_polygon","confidence_score_0_100":100,"evidence_grade":"A","field_evidence":{**sec,"hmlr_inspire_id":ref,"hmlr_wms_service":WMS,"hmlr_wms_layer":LAYER,"hmlr_getfeatureinfo_url":ev.get("url"),"hmlr_getfeatureinfo_sha256":ev.get("sha256"),"hmlr_returned_srs_names":chosen["srs"],"hmlr_feature_properties":chosen["props"],"canonical_point_wgs84":{"type":"Point","coordinates":[pt[0],pt[1]]}},"canonical_parcel_id":"hmlr-inspire:"+ref,"canonical_parcel_reference":ref,"partition_record_id":pid,"canonical_geometry_source_url":ev.get("url"),"canonical_geometry_provider":"HM Land Registry","canonical_geometry_dataset":"INSPIRE Index Polygons WMS","source_window_id":WINDOW,"cursor":f"{WINDOW}:record={i}"}
   f={"type":"Feature","id":"hmlr-inspire:"+ref,"geometry":chosen["geometry"],"properties":p};reasons+=sem(f)
   if not reasons:features.append(f)
  if reasons:reject.append({"record_index":i,"cursor":f"{WINDOW}:record={i}","partition_record_id":pid,"hmlr_inspire_id":ref,"reasons":reasons,"request":ev})
 ok=len(features)==9 and not reject
 base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=9,valid_count=len(features),rejected_count=len(reject),semantic_precheck_passed=ok,delivery_blocked=None if ok else "PRODUCER_SCHEMA_INVALID",records_geojson={"type":"FeatureCollection","features":features},rejections=reject,requests=requests,cursor=f"{WINDOW}:record=9")
 save(base);print("VALID_COUNT="+str(len(features)));print("REJECTED_COUNT="+str(len(reject)));print("SEMANTIC_PRECHECK_PASSED="+str(ok).lower());return 0
if __name__=="__main__":raise SystemExit(main())
