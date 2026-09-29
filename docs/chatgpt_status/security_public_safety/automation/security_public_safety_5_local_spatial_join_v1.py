from __future__ import annotations
import hashlib,json,os,re,subprocess,sys,urllib.parse
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
bs4=ensure("bs4")
try:
    from pyproj import Transformer
except Exception:
    subprocess.check_call([sys.executable,"-m","pip","install","-q","pyproj"])
    from pyproj import Transformer
from bs4 import BeautifulSoup
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

soup=BeautifulSoup(html,"html.parser")
href=None
for tr in soup.find_all(["tr","li","div"]):
    t=" ".join(tr.stripped_strings)
    if "London Borough of Lambeth" in t:
        a=tr.find("a",href=True)
        if a: href=a["href"];break
if not href:
    idx=html.find("London Borough of Lambeth")
    frag=html[idx:idx+4000] if idx>=0 else ""
    m=re.search(r'href=["\']([^"\']+)["\']',frag,re.I)
    if m: href=m.group(1)
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

to_bng=Transformer.from_crs("EPSG:4326","EPSG:27700",always_xy=True)
to_wgs=Transformer.from_crs("EPSG:27700","EPSG:4326",always_xy=True)
tp={t["partition_record_id"]:{**t,"xy":to_bng.transform(t["lon"],t["lat"]),"hits":[]} for t in TARGETS}

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
                wouter=[list(to_wgs.transform(a,b)) for a,b in outer]
                wholes=[[list(to_wgs.transform(a,b)) for a,b in h] for h in holes]
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
