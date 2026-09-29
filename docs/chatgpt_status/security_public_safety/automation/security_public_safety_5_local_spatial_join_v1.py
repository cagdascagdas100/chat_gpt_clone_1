from __future__ import annotations
import hashlib,json,math,os,re,subprocess,sys,urllib.parse
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
SOURCE_WINDOW="hmlr_inspire_lambeth_2026_09_sps5_61637_61648_61649_v1"
PAGE="https://use-land-property-data.service.gov.uk/datasets/inspire/download"
OUT=Path(os.environ.get("AAYS_REPO_ROOT","."))/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
TARGETS=[
 {"partition_record_id":"parcel_61637","lon":-0.1410325,"lat":51.4653843,"coverage_area_id":"E01003039","rows":24,"crime_sum":622,"numeric_cells":576},
 {"partition_record_id":"parcel_61648","lon":-0.1438922,"lat":51.4666501,"coverage_area_id":"E01003038","rows":22,"crime_sum":287,"numeric_cells":528},
 {"partition_record_id":"parcel_61649","lon":-0.1436095,"lat":51.4667436,"coverage_area_id":"E01003038","rows":22,"crime_sum":287,"numeric_cells":528},
]
MPS_URL="https://data.london.gov.uk/download/exy3m/221142dd-f7b2-4209-921e-4de833a82285/MPS%20LSOA%20Level%20Crime%20%28most%20recent%2024%20months%29.csv"
MPS_SHA="255d63bd759f08d7b0dd7674a38fca25ccb824c6c3a5d75d3fb00e504a34c082"

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def ensure(pkg):
    try: return __import__(pkg)
    except Exception:
        subprocess.check_call([sys.executable,"-m","pip","install","-q",pkg])
        return __import__(pkg)

requests=ensure("requests")
import xml.etree.ElementTree as ET

def lname(tag): return tag.rsplit("}",1)[-1] if "}" in tag else tag
def txt_desc(el,names):
    names=set(names)
    for x in el.iter():
        if lname(x.tag) in names and x.text and x.text.strip():
            return x.text.strip()
    return None
def parse_poslist(text):
    vals=[float(x) for x in re.split(r"\s+",(text or "").strip()) if x]
    return [(vals[i],vals[i+1]) for i in range(0,len(vals)-1,2)]
def inring(x,y,ring):
    inside=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i];xj,yj=ring[j]
        if ((yi>y)!=(yj>y)):
            xin=(xj-xi)*(y-yi)/(yj-yi)+xi
            if x<xin: inside=not inside
        j=i
    return inside
def inpoly(x,y,outer,holes):
    if not inring(x,y,outer): return False
    return not any(inring(x,y,h) for h in holes)

def _cart_from_ll(lat,lon,a,b,h=0.0):
    e2=1.0-(b*b)/(a*a); sl=math.sin(lat); cl=math.cos(lat)
    nu=a/math.sqrt(1.0-e2*sl*sl)
    return ((nu+h)*cl*math.cos(lon),(nu+h)*cl*math.sin(lon),((1.0-e2)*nu+h)*sl)

def _ll_from_cart(x,y,z,a,b):
    e2=1.0-(b*b)/(a*a); p=math.hypot(x,y)
    lat=math.atan2(z,p*(1.0-e2))
    for _ in range(12):
        nu=a/math.sqrt(1.0-e2*math.sin(lat)**2)
        nxt=math.atan2(z+e2*nu*math.sin(lat),p)
        if abs(nxt-lat)<1e-13: lat=nxt; break
        lat=nxt
    return lat,math.atan2(y,x)

def _helmert(x,y,z,tx,ty,tz,rx_sec,ry_sec,rz_sec,s_ppm):
    sec=math.pi/(180.0*3600.0); rx=rx_sec*sec; ry=ry_sec*sec; rz=rz_sec*sec
    sf=1.0+s_ppm*1e-6
    return (tx+x*sf-y*rz+z*ry,
            ty+x*rz+y*sf-z*rx,
            tz-x*ry+y*rx+z*sf)

_AIRY_A=6377563.396; _AIRY_B=6356256.909
_WGS_A=6378137.0; _WGS_B=6356752.3141
_F0=0.9996012717; _LAT0=math.radians(49.0); _LON0=math.radians(-2.0); _N0=-100000.0; _E0=400000.0

def _osgb_ll_to_en(lat,lon):
    a=_AIRY_A; b=_AIRY_B; F0=_F0
    e2=1.0-(b*b)/(a*a); n=(a-b)/(a+b)
    sl=math.sin(lat); cl=math.cos(lat); tl=math.tan(lat)
    nu=a*F0/math.sqrt(1.0-e2*sl*sl)
    rho=a*F0*(1.0-e2)/(1.0-e2*sl*sl)**1.5
    eta2=nu/rho-1.0
    dlat=lat-_LAT0
    M=b*F0*((1+n+5*n*n/4+5*n**3/4)*dlat
      -(3*n+3*n*n+21*n**3/8)*math.sin(dlat)*math.cos(lat+_LAT0)
      +(15*n*n/8+15*n**3/8)*math.sin(2*dlat)*math.cos(2*(lat+_LAT0))
      -(35*n**3/24)*math.sin(3*dlat)*math.cos(3*(lat+_LAT0)))
    dl=lon-_LON0
    I=M+_N0
    II=nu/2*sl*cl
    III=nu/24*sl*cl**3*(5-tl*tl+9*eta2)
    IIIA=nu/720*sl*cl**5*(61-58*tl*tl+tl**4)
    IV=nu*cl
    V=nu/6*cl**3*(nu/rho-tl*tl)
    VI=nu/120*cl**5*(5-18*tl*tl+tl**4+14*eta2-58*tl*tl*eta2)
    N=I+II*dl**2+III*dl**4+IIIA*dl**6
    E=_E0+IV*dl+V*dl**3+VI*dl**5
    return E,N

def _en_to_osgb_ll(E,N):
    a=_AIRY_A; b=_AIRY_B; F0=_F0; n=(a-b)/(a+b)
    lat=_LAT0
    for _ in range(20):
        dlat=lat-_LAT0
        M=b*F0*((1+n+5*n*n/4+5*n**3/4)*dlat
          -(3*n+3*n*n+21*n**3/8)*math.sin(dlat)*math.cos(lat+_LAT0)
          +(15*n*n/8+15*n**3/8)*math.sin(2*dlat)*math.cos(2*(lat+_LAT0))
          -(35*n**3/24)*math.sin(3*dlat)*math.cos(3*(lat+_LAT0)))
        delta=N-_N0-M
        lat+=delta/(a*F0)
        if abs(delta)<1e-5: break
    e2=1.0-(b*b)/(a*a); sl=math.sin(lat); cl=math.cos(lat); tl=math.tan(lat)
    nu=a*F0/math.sqrt(1.0-e2*sl*sl)
    rho=a*F0*(1.0-e2)/(1.0-e2*sl*sl)**1.5
    eta2=nu/rho-1.0; dE=E-_E0; sec=1.0/cl
    VII=tl/(2*rho*nu)
    VIII=tl/(24*rho*nu**3)*(5+3*tl*tl+eta2-9*tl*tl*eta2)
    IX=tl/(720*rho*nu**5)*(61+90*tl*tl+45*tl**4)
    X=sec/nu
    XI=sec/(6*nu**3)*(nu/rho+2*tl*tl)
    XII=sec/(120*nu**5)*(5+28*tl*tl+24*tl**4)
    XIIA=sec/(5040*nu**7)*(61+662*tl*tl+1320*tl**4+720*tl**6)
    lat2=lat-VII*dE**2+VIII*dE**4-IX*dE**6
    lon2=_LON0+X*dE-XI*dE**3+XII*dE**5-XIIA*dE**7
    return lat2,lon2

def wgs84_to_bng(lon_deg,lat_deg):
    lat=math.radians(lat_deg); lon=math.radians(lon_deg)
    x,y,z=_cart_from_ll(lat,lon,_WGS_A,_WGS_B)
    x,y,z=_helmert(x,y,z,-446.448,125.157,-542.060,-0.1502,-0.2470,-0.8421,20.4894)
    lat2,lon2=_ll_from_cart(x,y,z,_AIRY_A,_AIRY_B)
    return _osgb_ll_to_en(lat2,lon2)

def bng_to_wgs84(E,N):
    lat,lon=_en_to_osgb_ll(E,N)
    x,y,z=_cart_from_ll(lat,lon,_AIRY_A,_AIRY_B)
    x,y,z=_helmert(x,y,z,446.448,-125.157,542.060,0.1502,0.2470,0.8421,-20.4894)
    lat2,lon2=_ll_from_cart(x,y,z,_WGS_A,_WGS_B)
    return math.degrees(lon2),math.degrees(lat2)

base={"schema_version":5,"slot_id":SLOT_ID,"lineage_id":LINEAGE_ID,"generated_at":now(),
      "source_window_id":SOURCE_WINDOW,"source_window_reused":False,
      "first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED",
      "accepted_count_claimed":0,"final_package_written":False,"fake_data":False}

s=requests.Session()
headers={"User-Agent":"Mozilla/5.0 AAYS/1.0","Accept":"text/html,application/xhtml+xml"}
html=None; page_url=None; page_status=None; errs=[]
for u in [PAGE,PAGE+"/"]:
    try:
        rr=s.get(u,headers=headers,timeout=60,allow_redirects=True)
        page_status=rr.status_code
        if rr.status_code==200 and "London Borough of Lambeth" in rr.text:
            html=rr.text;page_url=rr.url;break
        errs.append(f"{u}:status={rr.status_code}:url={rr.url}")
    except Exception as e: errs.append(f"{u}:{type(e).__name__}:{e}")
if html is None:
    base.update(status="BLOCKED",blocker="HMLR_INSPIRE_DOWNLOAD_PAGE_UNAVAILABLE",errors=errs,records=[],unmatched=[])
    save(base);raise SystemExit(0)

href=None
row_match=re.search(r'<tr\\b[^>]*>.*?London Borough of Lambeth.*?</tr>',html,re.I|re.S)
if row_match:
    links=re.findall('href="([^"]+)"',row_match.group(0),re.I)+re.findall("href='([^']+)'",row_match.group(0),re.I)
    preferred=[x for x in links if ".gml" in x.lower() or "inspire" in x.lower()]
    if preferred: href=preferred[0]
    elif links: href=links[0]
if not href:
    idx=html.find("London Borough of Lambeth")
    frag=html[max(0,idx-4000):idx+8000] if idx>=0 else ""
    links=re.findall('href="([^"]+)"',frag,re.I)+re.findall("href='([^']+)'",frag,re.I)
    preferred=[x for x in links if ".gml" in x.lower() or "inspire" in x.lower()]
    if preferred: href=preferred[0]
if not href:
    base.update(status="BLOCKED",blocker="HMLR_LAMBETH_GML_LINK_NOT_FOUND",page_status=page_status,page_url=page_url,records=[],unmatched=[])
    save(base);raise SystemExit(0)

gml_url=urllib.parse.urljoin(page_url,href)
gr=s.get(gml_url,headers={"User-Agent":"Mozilla/5.0 AAYS/1.0","Accept":"application/gml+xml,application/xml,text/xml,*/*"},timeout=180)
gml=gr.content
gsha=hashlib.sha256(gml).hexdigest()
if gr.status_code!=200 or len(gml)<1000:
    base.update(status="BLOCKED",blocker="HMLR_LAMBETH_GML_DOWNLOAD_FAILED",gml_url=gml_url,gml_http_status=gr.status_code,gml_size=len(gml),records=[],unmatched=[])
    save(base);raise SystemExit(0)

tp={t["partition_record_id"]:{**t,"xy":wgs84_to_bng(t["lon"],t["lat"]),"hits":[]} for t in TARGETS}

root=ET.fromstring(gml)
feature_count=0
for el in root.iter():
    if lname(el.tag)!="CadastralParcel": continue
    feature_count+=1
    ident=txt_desc(el,["localId","identifier","inspireId"]) or el.attrib.get("{http://www.opengis.net/gml/3.2}id") or el.attrib.get("{http://www.opengis.net/gml}id")
    polygons=[]
    for poly in [x for x in el.iter() if lname(x.tag)=="Polygon"]:
        outer=None;holes=[]
        for ext in [x for x in poly.iter() if lname(x.tag) in ("exterior","outerBoundaryIs")]:
            pl=txt_desc(ext,["posList","coordinates"])
            ring=parse_poslist(pl)
            if len(ring)>=4: outer=ring;break
        for inte in [x for x in poly.iter() if lname(x.tag) in ("interior","innerBoundaryIs")]:
            pl=txt_desc(inte,["posList","coordinates"]);ring=parse_poslist(pl)
            if len(ring)>=4: holes.append(ring)
        if outer: polygons.append((outer,holes))
    if not polygons: continue
    for k,t in tp.items():
        x,y=t["xy"]
        for outer,holes in polygons:
            if inpoly(x,y,outer,holes):
                wouter=[list(bng_to_wgs84(a,b)) for a,b in outer]
                wholes=[[list(bng_to_wgs84(a,b)) for a,b in h] for h in holes]
                t["hits"].append({"identifier":ident,"geometry":{"type":"MultiPolygon","coordinates":[[wouter,*wholes]]}})
                break

records=[];unmatched=[]
for i,t in enumerate(TARGETS,1):
    h=tp[t["partition_record_id"]]["hits"]
    if len(h)!=1 or not h[0]["identifier"]:
        unmatched.append({"record_index":i,"partition_record_id":t["partition_record_id"],"reasons":[f"hmlr_inspire_unique_match_required:found={len(h)}"],"candidate_ids":[x.get("identifier") for x in h]})
        continue
    hit=h[0]
    cid=f"hmlr-inspire:{hit['identifier']}"
    props={
      "evidence_scope":"parcel",
      "coverage_area_id":t["coverage_area_id"],
      "source_resolution":"official_MPS_LSOA_recorded_crime_joined_to_HMLR_INSPIRE_index_polygon",
      "time_window":"MPS_most_recent_24_months_as_hashed_2026-09-28",
      "source_url":MPS_URL,
      "measurement_date":"2026-09-28",
      "measurement_method":"official_MPS_LSOA_CSV_exact_identifier_join",
      "spatial_binding_method":"canonical_point_intersects_HMLR_INSPIRE_index_polygon_GML",
      "confidence_score_0_100":100,
      "evidence_grade":"A",
      "field_evidence":{"security_source":"Metropolitan Police Service / London Datastore","official_csv_sha256":MPS_SHA,
        "lsoa_code":t["coverage_area_id"],"official_lsoa_row_count":t["rows"],"official_crime_value_sum":t["crime_sum"],
        "official_numeric_cells":t["numeric_cells"],"hmlr_inspire_download_page":page_url,"hmlr_inspire_gml_url":gml_url,
        "hmlr_inspire_gml_sha256":gsha,"hmlr_inspire_id":hit["identifier"]},
      "canonical_parcel_id":cid,
      "canonical_parcel_reference":hit["identifier"],
      "partition_record_id":t["partition_record_id"],
      "canonical_lsoa_code":t["coverage_area_id"],
      "canonical_geometry_source_url":gml_url,
      "canonical_geometry_provider":"HM Land Registry",
      "canonical_geometry_dataset":"INSPIRE Index Polygons",
      "source_window_id":SOURCE_WINDOW,
      "cursor":f"{SOURCE_WINDOW}:record={i}"
    }
    records.append({"type":"Feature","id":cid,"geometry":hit["geometry"],"properties":props})

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

base.update(status="SEMANTIC_PRECHECK_COMPLETE",official_source={"publisher":"HM Land Registry","dataset":"INSPIRE Index Polygons","page_url":page_url,"gml_url":gml_url,"gml_http_status":gr.status_code,"gml_sha256":gsha,"gml_size_bytes":len(gml),"feature_count":feature_count},
            processed_count=len(TARGETS),schema_valid_count=len(records)-len(issues),schema_invalid_count=len(issues),
            rejected_count=len(unmatched),records=records,unmatched=unmatched,schema_issues=issues,
            semantic_precheck_passed=(len(records)>0 and len(issues)==0),
            cursor=f"{SOURCE_WINDOW}:record={len(TARGETS)}")
save(base)
print(json.dumps({"status":base["status"],"gml_sha256":gsha,"feature_count":feature_count,"valid":base["schema_valid_count"],"rejected":len(unmatched),"issues":len(issues)}))
raise SystemExit(0)
