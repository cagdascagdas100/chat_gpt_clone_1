from __future__ import annotations
import hashlib,io,json,math,os,subprocess,urllib.parse,urllib.request,xml.etree.ElementTree as ET,zipfile
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
SOURCE_WINDOW="hmlr_inspire_lambeth_direct_zip_sps5_61624_61673_v1"
HMLR_ZIP="https://data.inspire.landregistry.gov.uk/Lambeth.zip"
REPO=Path(os.environ.get("AAYS_REPO_ROOT",".")); OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
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


def git_show(ref,path):
    q=subprocess.run(["git","-C",str(REPO),"show",f"{ref}:{path}"],capture_output=True,check=False,timeout=180)
    if q.returncode!=0: raise RuntimeError(q.stderr.decode("utf-8","replace")[-500:])
    return q.stdout
def pin(x,y,ring):
    inside=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i];xj,yj=ring[j]
        if ((yi>y)!=(yj>y)):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside
def ident_of(el):
    return text_first(el,["localId","nationalCadastralReference","inspireId","identifier"]) or el.attrib.get("{http://www.opengis.net/gml/3.2}id") or el.attrib.get("{http://www.opengis.net/gml}id") or el.attrib.get("id")

RUNNER_COMMIT="a1a3e428882e653c32694d163e8a5f014d1580c9"
RUNNER_PATH="docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
FIELD_COMMIT="6342cc858dc07de5b050ec67e458b295cb0c1921"
FIELD_PATH="incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/mps_lsoa_recorded_crime_202108_202307_61624_61673_20260928T085212Z/records.geojson"
base={"schema_version":7,"slot_id":SLOT_ID,"owner":None,"partition":{"start":61524,"end":76903,"count":15380},"lineage_id":LINEAGE_ID,"generated_at":now(),"source_window_id":SOURCE_WINDOW,"first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","accepted_count_claimed":0,"final_package_written":False,"fake_data":False,"max_records":50}
try:
    prior=json.loads(git_show(RUNNER_COMMIT,RUNNER_PATH).decode("utf-8-sig"))
    fg=json.loads(git_show(FIELD_COMMIT,FIELD_PATH).decode("utf-8-sig"))
except Exception as ex:
    base.update(status="BLOCKED",blocker="PRIOR_READBACK_FAILED",error=str(ex),records=[],unmatched=[]);save(base);raise SystemExit(0)
pts=[]
for x in prior.get("rows",[]):
    n=x.get("parcel_number");g=x.get("canonical_geometry") or {}
    if isinstance(n,int) and 61624<=n<=61673 and g.get("type")=="Point":
        pts.append({"partition_record_id":x.get("parcel_id"),"parcel_number":n,"lon":float(g["coordinates"][0]),"lat":float(g["coordinates"][1])})
pts.sort(key=lambda z:z["parcel_number"])
fieldmap={}
for f in fg.get("features",[]):
    pp=f.get("properties") or {}
    if pp.get("parcel_id"): fieldmap[pp["parcel_id"]]=pp
if len(pts)!=50:
    base.update(status="BLOCKED",blocker="PRIOR_POINT_RANGE_INCOMPLETE",records=[],unmatched=[]);save(base);raise SystemExit(0)
req=urllib.request.Request(HMLR_ZIP,headers={"User-Agent":"AAYS-security-public-safety-5/HMLR-direct-zip-v1","Accept":"application/zip,*/*"})
try:
    with urllib.request.urlopen(req,timeout=240) as resp:
        body=resp.read(); status=int(resp.status); final_url=resp.geturl(); ctype=resp.headers.get("Content-Type")
    z=zipfile.ZipFile(io.BytesIO(body)); members=z.namelist(); gml_name=next(n for n in members if n.lower().endswith(".gml")); gml=z.read(gml_name)
    root=ET.fromstring(gml)
except Exception as ex:
    base.update(status="BLOCKED",blocker="HMLR_DIRECT_ZIP_OR_GML_FAILED",error=str(ex),records=[],unmatched=[]);save(base);raise SystemExit(0)
base["official_source"]={"publisher":"HM Land Registry","dataset":"INSPIRE Index Polygons","local_authority":"London Borough of Lambeth","source_url":HMLR_ZIP,"final_url":final_url,"http_status":status,"content_type":ctype,"zip_sha256":hashlib.sha256(body).hexdigest(),"zip_size_bytes":len(body),"gml_member":gml_name,"gml_sha256":hashlib.sha256(gml).hexdigest(),"published_window":"2026-09","data_window":"2026-08","public_no_login":True}
pbn=[]
for a in pts:
    E,N=wgs_to_bng(a["lon"],a["lat"]); pbn.append(dict(a,E=E,N=N))
hits={a["partition_record_id"]:[] for a in pts};seen=set();scanned=0
for el in root.iter():
    tag=lname(el.tag).lower()
    if tag not in ("cadastralparcel","featuremember","member","lr_poly","landregistry"): continue
    ident=ident_of(el);rings=rings_from_feature(el)
    if not ident or not rings or ident in seen: continue
    seen.add(ident);scanned+=1
    outer=rings[0];holes=rings[1:];xs=[q[0] for q in outer];ys=[q[1] for q in outer]
    if not xs: continue
    bb=(min(xs),min(ys),max(xs),max(ys))
    matched=[]
    for a in pbn:
        if bb[0]<=a["E"]<=bb[2] and bb[1]<=a["N"]<=bb[3] and pin(a["E"],a["N"],outer) and not any(pin(a["E"],a["N"],h) for h in holes): matched.append(a)
    if not matched: continue
    geom={"type":"Polygon","coordinates":[[bng_to_wgs(x,y) for x,y in ring] for ring in [outer,*holes]]}
    for a in matched: hits[a["partition_record_id"]].append({"identifier":str(ident),"geometry":geom})
base["official_source"]["features_scanned_for_lookup"]=scanned

required=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]
records=[];unmatched=[];issues=[]
for i,a in enumerate(pts,1):
    fp=fieldmap.get(a["partition_record_id"]); hs={h["identifier"]:h for h in hits.get(a["partition_record_id"],[])}; reasons=[]
    if fp is None: reasons.append("MISSING_REUSED_MPS_FIELD_EVIDENCE")
    if len(hs)==0: reasons.append("NO_UNIQUE_HMLR_INSPIRE_POLYGON_CONTAINING_CANONICAL_POINT")
    if len(hs)>1: reasons.append("MULTIPLE_HMLR_INSPIRE_POLYGONS_CONTAIN_CANONICAL_POINT")
    if reasons:
        unmatched.append({"record_index":i,"partition_record_id":a["partition_record_id"],"cursor":SOURCE_WINDOW+f":record={i}","exact_reasons":reasons});continue
    h=next(iter(hs.values()));cid=h["identifier"]
    fe={"criterion":"security_public_safety","publisher":fp.get("official_source"),"source_url":fp.get("official_csv_url"),"official_csv_sha256":fp.get("official_csv_sha256"),"lsoa_code":fp.get("canonical_lsoa_code"),"official_lsoa_row_count":fp.get("official_lsoa_row_count"),"official_crime_value_sum":fp.get("official_crime_value_sum"),"official_numeric_cells":fp.get("official_numeric_cells"),"prior_verified_package_commit":FIELD_COMMIT}
    props={"evidence_scope":"coverage_area","coverage_area_id":fp.get("canonical_lsoa_code"),"source_resolution":"HMLR_INSPIRE_REGISTERED_FREEHOLD_POLYGON_PLUS_MPS_LSOA_MONTHLY_CRIME","time_window":"202108-202307","source_url":fp.get("official_csv_url"),"measurement_date":"2023-07-31","measurement_method":"official MPS LSOA recorded-crime exact-identifier aggregation with HMLR INSPIRE cadastral polygon readback","spatial_binding_method":"canonical partition point contained by exactly one HMLR INSPIRE polygon; field evidence bound by exact MPS LSOA identifier","confidence_score_0_100":90,"confidence_basis":"exact official identifiers; conservative reduction for published HMLR CRS reprojection uncertainty","evidence_grade":"A","field_evidence":fe,"canonical_parcel_id":cid,"canonical_parcel_id_namespace":"HM_LAND_REGISTRY_INSPIRE","partition_record_id":a["partition_record_id"],"canonical_geometry_source_url":HMLR_ZIP,"canonical_geometry_source_sha256":base["official_source"]["zip_sha256"],"source_window_id":SOURCE_WINDOW,"cursor":SOURCE_WINDOW+f":record={i}"}
    f={"type":"Feature","id":cid,"geometry":h["geometry"],"properties":props};bad=[]
    if f["geometry"]["type"] not in ("Polygon","MultiPolygon"): bad.append("invalid_geometry")
    for k in required:
        if k not in props or props[k] in (None,""): bad.append("missing:"+k)
    if "parcel_id" in props: bad.append("forbidden:parcel_id")
    if "accepted_parcel" in props: bad.append("forbidden:accepted_parcel")
    if bad: issues.append({"record_index":i,"partition_record_id":a["partition_record_id"],"exact_reasons":bad})
    else: records.append(f)
base.update(status="SEMANTIC_PRECHECK_COMPLETE",source_records_processed_count=50,schema_valid_count=len(records),schema_invalid_count=len(issues),unmatched_count=len(unmatched),records=records,unmatched=unmatched,schema_issues=issues,cursor=SOURCE_WINDOW+":record=50",semantic_precheck_passed=(len(records)>0 and len(issues)==0))
if not base["semantic_precheck_passed"]: base["blocker"]="PRODUCER_SCHEMA_INVALID"
save(base)
print(json.dumps({"valid":len(records),"unmatched":len(unmatched),"issues":len(issues),"zip_sha256":base["official_source"]["zip_sha256"]}))
raise SystemExit(0)
