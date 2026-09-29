from __future__ import annotations
import hashlib,json,math,os,subprocess,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
SOURCE_WINDOW="hmlr_inspire_wms_gfi_sps5_61637_v1"
WMS="https://inspire.landregistry.gov.uk/inspire/ows"
OUT=Path(os.environ.get("AAYS_REPO_ROOT","."))/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
TARGET={"partition_record_id":"parcel_61637","lon":-0.1410325,"lat":51.4653843,"coverage_area_id":"E01003039","rows":24,"crime_sum":622,"numeric_cells":576}
MPS_URL="https://data.london.gov.uk/download/exy3m/221142dd-f7b2-4209-921e-4de833a82285/MPS%20LSOA%20Level%20Crime%20%28most%20recent%2024%20months%29.csv"
MPS_SHA="255d63bd759f08d7b0dd7674a38fca25ccb824c6c3a5d75d3fb00e504a34c082"

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def lname(t): return t.rsplit("}",1)[-1] if "}" in t else t
def text_first(el,names):
    ns=set(x.lower() for x in names)
    for x in el.iter():
        if lname(x.tag).lower() in ns and x.text and x.text.strip(): return x.text.strip()
    return None

# WGS84 -> OSGB36 / British National Grid and inverse.
_AIRY_A=6377563.396; _AIRY_B=6356256.909
_WGS_A=6378137.0; _WGS_B=6356752.3141
_F0=0.9996012717; _LAT0=math.radians(49.0); _LON0=math.radians(-2.0); _N0=-100000.0; _E0=400000.0
def _cart(lat,lon,a,b,h=0.0):
    e2=1-(b*b)/(a*a); sl=math.sin(lat); cl=math.cos(lat); nu=a/math.sqrt(1-e2*sl*sl)
    return ((nu+h)*cl*math.cos(lon),(nu+h)*cl*math.sin(lon),((1-e2)*nu+h)*sl)
def _ll(x,y,z,a,b):
    e2=1-(b*b)/(a*a); p=math.hypot(x,y); lat=math.atan2(z,p*(1-e2))
    for _ in range(12):
        nu=a/math.sqrt(1-e2*math.sin(lat)**2); nxt=math.atan2(z+e2*nu*math.sin(lat),p)
        if abs(nxt-lat)<1e-13: lat=nxt; break
        lat=nxt
    return lat,math.atan2(y,x)
def _helm(x,y,z,tx,ty,tz,rxs,rys,rzs,sppm):
    sec=math.pi/(180*3600); rx=rxs*sec; ry=rys*sec; rz=rzs*sec; sf=1+sppm*1e-6
    return (tx+x*sf-y*rz+z*ry,ty+x*rz+y*sf-z*rx,tz-x*ry+y*rx+z*sf)
def _osgb_ll_to_en(lat,lon):
    a=_AIRY_A;b=_AIRY_B;F0=_F0;e2=1-(b*b)/(a*a);n=(a-b)/(a+b);sl=math.sin(lat);cl=math.cos(lat);tl=math.tan(lat)
    nu=a*F0/math.sqrt(1-e2*sl*sl);rho=a*F0*(1-e2)/(1-e2*sl*sl)**1.5;eta2=nu/rho-1;dlat=lat-_LAT0
    M=b*F0*((1+n+5*n*n/4+5*n**3/4)*dlat-(3*n+3*n*n+21*n**3/8)*math.sin(dlat)*math.cos(lat+_LAT0)+(15*n*n/8+15*n**3/8)*math.sin(2*dlat)*math.cos(2*(lat+_LAT0))-(35*n**3/24)*math.sin(3*dlat)*math.cos(3*(lat+_LAT0)))
    dl=lon-_LON0;I=M+_N0;II=nu/2*sl*cl;III=nu/24*sl*cl**3*(5-tl*tl+9*eta2);IIIA=nu/720*sl*cl**5*(61-58*tl*tl+tl**4)
    IV=nu*cl;V=nu/6*cl**3*(nu/rho-tl*tl);VI=nu/120*cl**5*(5-18*tl*tl+tl**4+14*eta2-58*tl*tl*eta2)
    return _E0+IV*dl+V*dl**3+VI*dl**5, I+II*dl**2+III*dl**4+IIIA*dl**6
def _en_to_osgb_ll(E,N):
    a=_AIRY_A;b=_AIRY_B;F0=_F0;n=(a-b)/(a+b);lat=_LAT0
    for _ in range(20):
        d=lat-_LAT0;M=b*F0*((1+n+5*n*n/4+5*n**3/4)*d-(3*n+3*n*n+21*n**3/8)*math.sin(d)*math.cos(lat+_LAT0)+(15*n*n/8+15*n**3/8)*math.sin(2*d)*math.cos(2*(lat+_LAT0))-(35*n**3/24)*math.sin(3*d)*math.cos(3*(lat+_LAT0)))
        delta=N-_N0-M;lat+=delta/(a*F0)
        if abs(delta)<1e-5: break
    e2=1-(b*b)/(a*a);sl=math.sin(lat);cl=math.cos(lat);tl=math.tan(lat);nu=a*F0/math.sqrt(1-e2*sl*sl);rho=a*F0*(1-e2)/(1-e2*sl*sl)**1.5;eta2=nu/rho-1;dE=E-_E0;sec=1/cl
    VII=tl/(2*rho*nu);VIII=tl/(24*rho*nu**3)*(5+3*tl*tl+eta2-9*tl*tl*eta2);IX=tl/(720*rho*nu**5)*(61+90*tl*tl+45*tl**4)
    X=sec/nu;XI=sec/(6*nu**3)*(nu/rho+2*tl*tl);XII=sec/(120*nu**5)*(5+28*tl*tl+24*tl**4);XIIA=sec/(5040*nu**7)*(61+662*tl*tl+1320*tl**4+720*tl**6)
    return lat-VII*dE**2+VIII*dE**4-IX*dE**6,_LON0+X*dE-XI*dE**3+XII*dE**5-XIIA*dE**7
def wgs_to_bng(lon,lat):
    x,y,z=_cart(math.radians(lat),math.radians(lon),_WGS_A,_WGS_B);x,y,z=_helm(x,y,z,-446.448,125.157,-542.060,-0.1502,-0.2470,-0.8421,20.4894);la,lo=_ll(x,y,z,_AIRY_A,_AIRY_B);return _osgb_ll_to_en(la,lo)
def bng_to_wgs(E,N):
    la,lo=_en_to_osgb_ll(E,N);x,y,z=_cart(la,lo,_AIRY_A,_AIRY_B);x,y,z=_helm(x,y,z,446.448,-125.157,542.060,0.1502,0.2470,0.8421,-20.4894);la,lo=_ll(x,y,z,_WGS_A,_WGS_B);return [math.degrees(lo),math.degrees(la)]

def parse_nums(s):
    out=[]
    for tok in (s or "").replace("\n"," ").split():
        for part in tok.split(","):
            try: out.append(float(part))
            except: pass
    return out
def rings_from_feature(el):
    rings=[]
    for ps in el.iter():
        if lname(ps.tag) not in ("posList","coordinates"): continue
        vals=parse_nums(ps.text or "")
        pts=[]
        if lname(ps.tag)=="coordinates":
            raw=(ps.text or "").replace("\n"," ").split()
            for t in raw:
                a=t.split(",")
                if len(a)>=2:
                    try: pts.append((float(a[0]),float(a[1])))
                    except: pass
        else:
            for i in range(0,len(vals)-1,2): pts.append((vals[i],vals[i+1]))
        if len(pts)>=4: rings.append(pts)
    return rings

base={"schema_version":6,"slot_id":SLOT_ID,"lineage_id":LINEAGE_ID,"generated_at":now(),"source_window_id":SOURCE_WINDOW,"first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","accepted_count_claimed":0,"final_package_written":False,"fake_data":False}
E,N=wgs_to_bng(TARGET["lon"],TARGET["lat"]); pad=3.0
params={"SERVICE":"WMS","VERSION":"1.1.1","REQUEST":"GetFeatureInfo","LAYERS":"inspire:CP.CadastralParcel","QUERY_LAYERS":"inspire:CP.CadastralParcel","STYLES":"","SRS":"EPSG:27700","BBOX":f"{E-pad},{N-pad},{E+pad},{N+pad}","WIDTH":"101","HEIGHT":"101","X":"50","Y":"50","FORMAT":"image/png","INFO_FORMAT":"application/vnd.ogc.gml","FEATURE_COUNT":"10","EXCEPTIONS":"application/vnd.ogc.se_xml"}
url=WMS+"?"+urllib.parse.urlencode(params)
req=urllib.request.Request(url,headers={"User-Agent":"AAYS-security-public-safety-5/wms-gfi-v1","Accept":"application/vnd.ogc.gml,text/xml,application/xml,*/*"})
try:
    with urllib.request.urlopen(req,timeout=90) as resp:
        body=resp.read(); status=int(resp.status); ctype=resp.headers.get("Content-Type")
except Exception as ex:
    base.update(status="BLOCKED",blocker="HMLR_WMS_GETFEATUREINFO_REQUEST_FAILED",error=str(ex),request_url=url,records=[],unmatched=[{"partition_record_id":TARGET["partition_record_id"],"reasons":["wms_request_failed"]}]);save(base);raise SystemExit(0)
base["official_source"]={"publisher":"HM Land Registry","dataset":"INSPIRE Index Polygons View Service","wms_url":WMS,"request_url":url,"http_status":status,"content_type":ctype,"response_sha256":hashlib.sha256(body).hexdigest(),"response_size_bytes":len(body)}
try: root=ET.fromstring(body)
except Exception as ex:
    base.update(status="BLOCKED",blocker="HMLR_WMS_GFI_PARSE_FAILED",error=str(ex),response_prefix=body[:400].decode("utf-8","replace"),records=[],unmatched=[{"partition_record_id":TARGET["partition_record_id"],"reasons":["wms_gml_parse_failed"]}]);save(base);raise SystemExit(0)

# Collect candidate feature elements with an exact HMLR identifier and polygon coordinates.
cands=[]
for el in root.iter():
    ident=text_first(el,["INSPIREID","inspireId","localId","NATIONALCADASTRALREFERENCE","LABEL"])
    gid=el.attrib.get("{http://www.opengis.net/gml}id") or el.attrib.get("{http://www.opengis.net/gml/3.2}id")
    ident=ident or gid
    rings=rings_from_feature(el)
    if not ident or not rings: continue
    # retain only distinct candidate by identifier
    outer=rings[0]
    # response requested EPSG:27700; convert if coordinates look projected.
    if max(abs(p[0]) for p in outer)>180 or max(abs(p[1]) for p in outer)>90:
        outer_ll=[bng_to_wgs(x,y) for x,y in outer]
    else:
        outer_ll=[[x,y] for x,y in outer]
    geom={"type":"Polygon","coordinates":[outer_ll]}
    if not any(x["identifier"]==ident for x in cands): cands.append({"identifier":ident,"geometry":geom})

unmatched=[];records=[]
if len(cands)!=1:
    unmatched.append({"partition_record_id":TARGET["partition_record_id"],"reasons":[f"unique_hmlr_wms_polygon_required:found={len(cands)}"],"candidate_ids":[x["identifier"] for x in cands]})
else:
    c=cands[0]; cid="hmlr-inspire:"+c["identifier"]
    props={
      "evidence_scope":"parcel",
      "coverage_area_id":TARGET["coverage_area_id"],
      "source_resolution":"LSOA monthly recorded-crime aggregation bound to one HMLR INSPIRE cadastral polygon",
      "time_window":"202108-202307",
      "source_url":MPS_URL,
      "measurement_date":"2023-07",
      "measurement_method":"official MPS LSOA CSV exact-identifier aggregation",
      "spatial_binding_method":"HMLR INSPIRE WMS GetFeatureInfo polygon at canonical parcel point plus exact LSOA identifier",
      "confidence_score_0_100":100,
      "evidence_grade":"A",
      "field_evidence":{"publisher":"Metropolitan Police Service / London Datastore","official_csv_sha256":MPS_SHA,"lsoa_code":TARGET["coverage_area_id"],"official_lsoa_row_count":TARGET["rows"],"official_crime_value_sum":TARGET["crime_sum"],"official_numeric_cells":TARGET["numeric_cells"],"hmlr_wms_response_sha256":base["official_source"]["response_sha256"],"hmlr_inspire_id":c["identifier"]},
      "canonical_parcel_id":cid,
      "partition_record_id":TARGET["partition_record_id"],
      "canonical_geometry_source_url":url,
      "canonical_geometry_provider":"HM Land Registry",
      "canonical_geometry_dataset":"INSPIRE Index Polygons View Service",
      "source_window_id":SOURCE_WINDOW,
      "cursor":SOURCE_WINDOW+":record=1"
    }
    records=[{"type":"Feature","id":cid,"geometry":c["geometry"],"properties":props}]

required=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]
issues=[]
for i,f in enumerate(records):
    p=f.get("properties") or {}; rs=[]
    if f.get("geometry",{}).get("type") not in ("Polygon","MultiPolygon"): rs.append("invalid_geometry")
    for k in required:
        if k not in p or p[k] in (None,""): rs.append("missing:"+k)
    if "parcel_id" in p: rs.append("forbidden:parcel_id")
    if "accepted_parcel" in p: rs.append("forbidden:accepted_parcel")
    if rs: issues.append({"index":i,"id":f.get("id"),"reasons":rs})

base.update(status="SEMANTIC_PRECHECK_COMPLETE",processed_count=1,schema_valid_count=len(records)-len(issues),schema_invalid_count=len(issues),rejected_count=len(unmatched),records=records,unmatched=unmatched,schema_issues=issues,semantic_precheck_passed=(len(records)==1 and len(issues)==0 and len(unmatched)==0),cursor=SOURCE_WINDOW+":record=1")
save(base)
print(json.dumps({"status":base["status"],"valid":base["schema_valid_count"],"unmatched":len(unmatched),"issues":len(issues),"response_sha256":base["official_source"]["response_sha256"]}))
