#!/usr/bin/env python3
"""Fail-closed resumable hydration for OS/ONS UPRN release packages."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,re,tempfile,time,urllib.request,zipfile
from pathlib import Path
SLOT="internet_access_3";BASE="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/"
OSR=BASE+"runner_outputs/041_os_opendata_download_resolution_latest.json";ONSD=BASE+"runner_outputs/015_ons_uprn_arcgis_release_discovery_latest.json";REG=BASE+"source_snapshots/013_full_release_hydration_uprn_join_registry_latest.json";RO=BASE+"runner_outputs/050_full_release_hydration_manifest_latest.json";WO="england_map_web/data/aays_21_slots/internet_access_3/full_release_hydration_manifest_latest.json"
ARC="https://www.arcgis.com/sharing/rest/content/items/{}/data";HEX32=re.compile(r"^[0-9a-f]{32}$",re.I);CR=re.compile(r"^bytes\s+(\d+)-(\d+)/(\d+|\*)$",re.I)
POSTCODE_ALIASES={"PCDS","PCD","PCD2","POSTCODE"};COORD_FIELDS={"XCOORDINATE","YCOORDINATE","LATITUDE","LONGITUDE"}
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--os-resolution",default=OSR);p.add_argument("--ons-discovery",default=ONSD);p.add_argument("--registry",default=REG);p.add_argument("--runner-output",default=RO);p.add_argument("--web-output",default=WO);p.add_argument("--cache-dir",type=Path,default=Path(tempfile.gettempdir())/"aays_internet_access_3_release_cache");p.add_argument("--chunk-size",type=int,default=8*1024*1024);p.add_argument("--timeout",type=int,default=180);p.add_argument("--retries",type=int,default=4);return p.parse_args()
def root(x):
 if x:
  r=x.expanduser().resolve()
  if not (r/"docs").exists() or not (r/"england_map_web").exists():raise FileNotFoundError(r)
  return r
 for r in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (r/"docs").exists() and (r/"england_map_web").exists():return r
 raise FileNotFoundError("repo root")
def load(p):
 with p.open("r",encoding="utf-8-sig") as h:return json.load(h)
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=p.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def safe(v):return (re.sub(r"[^A-Za-z0-9._-]+","_",str(v)).strip("._")[:180] or "package")
def norm(v):return re.sub(r"[^A-Z0-9]+","",str(v or "").upper())
def digest(p,a):
 d=hashlib.new(a)
 with p.open("rb") as h:
  for b in iter(lambda:h.read(4*1024*1024),b""):d.update(b)
 return d.hexdigest()
def expected_shape(spec):
 pid=str(spec.get("package_id") or "")
 return "UPRN_COORDINATES" if pid=="os_open_uprn" else "UPRN_HEADER" if pid=="os_lids_uprn_topographic_area" else "UPRN_POSTCODE"
def sample_shape(data,shape):
 raw=data.lstrip(b"\xef\xbb\xbf \t\r\n");low=raw[:128].lower()
 if low.startswith((b"<!doctype html",b"<html",b"<?xml")):return {"content_shape_valid":False,"content_shape_reason":"HTML_OR_XML_ERROR_BODY","header_fields":[]}
 if raw.startswith((b"{",b"[")):return {"content_shape_valid":False,"content_shape_reason":"JSON_ERROR_BODY","header_fields":[]}
 text=data.decode("utf-8-sig",errors="replace");line=next((x for x in text.splitlines() if x.strip()),"")
 if not line:return {"content_shape_valid":False,"content_shape_reason":"EMPTY_TEXT","header_fields":[]}
 try:fields=next(csv.reader([line]))
 except Exception:return {"content_shape_valid":False,"content_shape_reason":"CSV_HEADER_PARSE_FAILED","header_fields":[]}
 n={norm(x) for x in fields if str(x).strip()};uprn="UPRN" in n;postcode=bool(n&POSTCODE_ALIASES);coords=COORD_FIELDS.issubset(n)
 valid=uprn and (coords if shape=="UPRN_COORDINATES" else postcode if shape=="UPRN_POSTCODE" else True)
 reason="VALID_"+shape if valid else ("UPRN_HEADER_MISSING" if not uprn else "POSTCODE_HEADER_MISSING" if shape=="UPRN_POSTCODE" and not postcode else "COORDINATE_HEADERS_MISSING")
 return {"content_shape_valid":valid,"content_shape_reason":reason,"header_fields":sorted(n),"uprn_header_present":uprn,"postcode_header_present":postcode,"coordinate_headers_present":coords}
def inspect(p,shape):
 with p.open("rb") as h:prefix=h.read(8)
 if prefix.startswith(b"PK") and zipfile.is_zipfile(p):
  with zipfile.ZipFile(p) as z:
   bad=z.testzip();members=[x for x in z.infolist() if not x.is_dir()];csvs=[x for x in members if x.filename.lower().endswith((".csv",".txt"))];shapes=[]
   for item in csvs[:32]:
    with z.open(item) as h:shapes.append({"member":item.filename,**sample_shape(h.read(256*1024),shape)})
   selected=next((x for x in shapes if x["content_shape_valid"]),shapes[0] if shapes else {"member":None,"content_shape_valid":False,"content_shape_reason":"NO_CSV_OR_TXT_MEMBER","header_fields":[]})
   return {"media_type":"application/zip","zip_integrity_passed":bad is None,"zip_bad_member":bad,"zip_member_count":len(members),"zip_uncompressed_bytes":sum(x.file_size for x in members),"zip_csv_member_count":len(csvs),"shape_member":selected.get("member"),**{k:v for k,v in selected.items() if k!="member"}}
 with p.open("rb") as h:data=h.read(256*1024)
 return {"media_type":"text/csv-or-text","zip_integrity_passed":None,"zip_bad_member":None,"zip_member_count":0,"zip_uncompressed_bytes":0,"zip_csv_member_count":0,"shape_member":p.name,**sample_shape(data,shape)}
def packages(osr,ons):
 b=[]
 if osr.get("state")!="resolved":b.append("OS_DOWNLOAD_RESOLUTION_NOT_RESOLVED")
 if ons.get("state")!="runtime_validation_passed":b.append("ONS_RELEASE_DISCOVERY_NOT_RESOLVED")
 if b:raise ValueError(";".join(b))
 s=osr.get("selected") or {};out=[]
 for pid,item in (("os_open_uprn",s.get("open_uprn")),("os_lids_uprn_topographic_area",s.get("uprn_topographic_area"))):
  if not isinstance(item,dict):raise ValueError("missing OS package:"+pid)
  md5=str(item.get("md5") or "").lower()
  if not HEX32.fullmatch(md5):raise ValueError("invalid OS md5:"+pid)
  out.append({"package_id":pid,"authority":"Ordnance Survey","product_id":"OpenUPRN" if pid=="os_open_uprn" else "LIDS","title":item.get("fileName") or pid,"download_url":item.get("url"),"expected_size":int(item.get("size") or 0),"expected_md5":md5,"release_label":"June 2026"})
 by={str(x.get("product_id")):x for x in (ons.get("products") or []) if isinstance(x,dict)}
 for pid in ("nsul","onsud"):
  item=(by.get(pid) or {}).get("selected") or {};iid=str(item.get("id") or "")
  if not iid:raise ValueError("missing ONS selected item:"+pid)
  out.append({"package_id":pid,"authority":"Office for National Statistics","product_id":pid.upper(),"title":item.get("title") or pid,"download_url":ARC.format(iid),"expected_size":int(item.get("size") or 0),"expected_md5":None,"release_label":ons.get("release_label") or "May 2026","arcgis_item_id":iid})
 if len(out)!=4:raise ValueError("package count")
 return out
def validate(p,s):
 if not p.is_file():return {"valid":False,"reason":"MISSING","bytes":0}
 n=p.stat().st_size;es=int(s.get("expected_size") or 0);em=s.get("expected_md5");md5=digest(p,"md5");info=inspect(p,expected_shape(s));size_ok=es<=0 or n==es;md5_ok=em is None or md5.lower()==str(em).lower();zip_req=str(s.get("package_id") or "").startswith("os_");zip_ok=(info["media_type"]=="application/zip" and info["zip_integrity_passed"] is True and info["zip_csv_member_count"]>0) if zip_req else (info["media_type"]!="application/zip" or info["zip_integrity_passed"] is True);shape_ok=info.get("content_shape_valid") is True;bl=[]
 if not size_ok:bl.append("SIZE_MISMATCH")
 if not md5_ok:bl.append("MD5_MISMATCH")
 if not zip_ok:bl.append("ZIP_INTEGRITY_OR_SHAPE_FAILED")
 if not shape_ok:bl.append("CONTENT_SHAPE_FAILED:"+str(info.get("content_shape_reason")))
 return {"valid":not bl,"reason":"VALID" if not bl else ",".join(bl),"bytes":n,"actual_md5":md5,"actual_sha256":digest(p,"sha256"),"size_verified":size_ok,"md5_verified":md5_ok,"content_shape_verified":shape_ok,"expected_content_shape":expected_shape(s),**info}
def quarantine(p,d,reason):
 if not p.exists():return None
 q=d/"quarantine";q.mkdir(parents=True,exist_ok=True);t=q/f"{p.name}.{safe(reason)}.{time.time_ns()}.quarantine";os.replace(p,t);return str(t)
def range_start(v):
 m=CR.fullmatch(str(v or "").strip());return int(m.group(1)) if m else None
def transfer(s,part,chunk,timeout):
 cur=part.stat().st_size if part.exists() else 0;h={"User-Agent":"TerraYield-AAYS-internet-access-3/20","Accept":"*/*"}
 if cur:h["Range"]=f"bytes={cur}-"
 with urllib.request.urlopen(urllib.request.Request(str(s["download_url"]),headers=h),timeout=timeout) as r:
  status=int(getattr(r,"status",r.getcode()));cr=r.headers.get("Content-Range")
  if status==206:
   if cur<=0 or range_start(cr)!=cur:raise IOError(f"invalid Content-Range:{cur}:{cr}")
   mode="ab"
  elif status==200:mode="wb"
  else:raise IOError("unexpected HTTP status:"+str(status))
  with part.open(mode) as w:
   for b in iter(lambda:r.read(max(64*1024,chunk)),b""):w.write(b)
   w.flush();os.fsync(w.fileno())
 return {"status":status,"content_range":cr,"resumed":mode=="ab"}
def hydrate(s,d,chunk,timeout,retries):
 d.mkdir(parents=True,exist_ok=True);ext=".zip" if str(s["package_id"]).startswith("os_") else ".download";final=d/(safe(f"{s['package_id']}_{s['release_label']}")+ext);part=final.with_suffix(final.suffix+".part");es=int(s.get("expected_size") or 0);qs=[]
 if final.exists():
  c=validate(final,s)
  if c["valid"]:return {**s,"cache_path":str(final),"cache_hit":True,"cache_repaired":False,"attempts":0,"quarantined":qs,"bytes_hydrated":c["bytes"],**{k:v for k,v in c.items() if k not in {"valid","reason","bytes"}}}
  q=quarantine(final,d,"invalid_final_"+c["reason"])
  if q:qs.append(q)
 if part.exists() and es>0 and part.stat().st_size>es:
  q=quarantine(part,d,"oversized_partial")
  if q:qs.append(q)
 last=None
 for i in range(1,max(1,retries)+1):
  try:
   tr=transfer(s,part,chunk,timeout);c=validate(part,s)
   if not c["valid"]:
    q=quarantine(part,d,"invalid_partial_"+c["reason"])
    if q:qs.append(q)
    raise IOError("download validation:"+c["reason"])
   os.replace(part,final);c=validate(final,s)
   if not c["valid"]:
    q=quarantine(final,d,"post_replace_"+c["reason"])
    if q:qs.append(q)
    raise IOError("post-replace validation:"+c["reason"])
   return {**s,"cache_path":str(final),"cache_hit":False,"cache_repaired":bool(qs),"attempts":i,"quarantined":qs,"transfer":tr,"bytes_hydrated":c["bytes"],**{k:v for k,v in c.items() if k not in {"valid","reason","bytes"}}}
  except Exception as e:
   last=e
   if i<max(1,retries):time.sleep(min(2**(i-1),8))
 raise last or IOError("download failed")
def main():
 o=args();r=root(o.repo_root);reg=load(r/o.registry);items=packages(load(r/o.os_resolution),load(r/o.ons_discovery));done=[];bl=[]
 for s in items:
  try:done.append(hydrate(s,o.cache_dir.expanduser().resolve(),o.chunk_size,o.timeout,o.retries))
  except Exception as e:bl.append(f"{s['package_id'].upper()}_HYDRATION_ERROR:{type(e).__name__}:{e}")
 ok=len(done)==4 and not bl;now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat();z={"schema_version":3,"task_id":"aays1-internet-access-3-full-release-hydration-20260722","slot_id":SLOT,"state":"runtime_validation_passed" if ok else "blocked","updated_at":now,"release_contract_sha256":hashlib.sha256(json.dumps(reg.get("release_contract"),sort_keys=True,separators=(",",":")).encode()).hexdigest(),"packages_expected":4,"packages_hydrated":len(done),"packages":done,"download_bytes_hydrated":sum(int(x.get("bytes_hydrated") or 0) for x in done),"quarantined_files":sum(len(x.get("quarantined") or []) for x in done),"cache_repairs":sum(bool(x.get("cache_repaired")) for x in done),"source_checks_executed":12,"validation":{"passed":ok,"blockers":bl},"parcel_relations_promoted":0,"confidence_uplifts":0,"actual_business_data_rows_written":0,"output_semantics":"FULL_OFFICIAL_RELEASE_BYTE_HYDRATION_CHECKSUM_ZIP_CSV_HEADER_SHAPE_AND_CACHE_REPAIR_MANIFEST_ONLY","final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};write(r/o.runner_output,z);write(r/o.web_output,z);print(json.dumps(z,ensure_ascii=False,indent=2));return 0 if ok else 2
if __name__=="__main__":raise SystemExit(main())
