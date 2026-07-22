# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="internet_access_2"; MAX_SAMPLES=24; EXPECTED_FILES=121; EXPECTED_ROWS=1741096
R2=re.compile(r"(?:^|/)202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$",re.I)
PC=re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b",re.I)
ALIASES={
 "postcode":["postcode","postcode_space"],"area":["postcode area","postcode_area"],
 "sfbb":["SFBB availability (% premises)","SFBB availability"],
 "ufbb100":["UFBB (100Mbit/s) availability (% premises)","UFBB100 availability (% premises)"],
 "ufbb300":["UFBB availability (% premises)","UFBB (300Mbit/s) availability (% premises)"],
 "gigabit":["Gigabit availability (% premises)","Gigabit availability"],
 "unable30":["% of premises unable to receive 30Mbit/s","unable to receive 30Mbit/s"]}

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def normh(v): return re.sub(r"[^a-z0-9]+","",str(v or "").casefold())
def col(fields,names):
 d={normh(x):x for x in fields}
 return next((d[normh(x)] for x in names if normh(x) in d),None)
def normpc(v):
 c=re.sub(r"\s+","",str(v).upper())
 if len(c)<5: raise ValueError("INVALID_POSTCODE")
 return c[:-3]+" "+c[-3:]
def area(pc):
 m=re.match(r"^([A-Z]{1,2})",pc)
 if not m: raise ValueError("POSTCODE_AREA_NOT_FOUND")
 return m.group(1)
def ph(pc): return hashlib.sha256(pc.encode()).hexdigest()[:16]
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def strings(v):
 if isinstance(v,str): yield v
 elif isinstance(v,list):
  for x in v: yield from strings(x)
 elif isinstance(v,dict):
  for k,x in v.items():
   if any(t in str(k).casefold() for t in ("postcode","sample","candidate")): yield from strings(x)
def samples(path):
 out=[]
 for text in strings(json.loads(path.read_text(encoding="utf-8-sig"))):
  for m in PC.finditer(text):
   p=normpc(m.group(1))
   if p not in out: out.append(p)
 if not out: raise RuntimeError("NO_POSTCODES_FOUND")
 if len(out)>MAX_SAMPLES: raise RuntimeError("TOO_MANY_POSTCODES")
 return out
def gate(v,archive):
 d=v.get("download") if isinstance(v.get("download"),dict) else {}
 expected=str(d.get("sha256") or v.get("archive_sha256") or v.get("sha256") or "").lower()
 checks={"state":v.get("state")=="OFCom_POSTCODE_ZIP_SCHEMA_ACCEPTED","accepted":v.get("accepted") is True,
 "revision":v.get("observed_postcode_revision")=="r2",
 "files":int(v.get("r2_postcode_file_count",v.get("postcode_file_count",0)))==EXPECTED_FILES,
 "rows":int(v.get("total_r2_postcode_rows",v.get("total_postcode_rows",0)))==EXPECTED_ROWS,
 "crc":v.get("zip_crc_ok") is True,"sha":bool(expected and sha(archive)==expected)}
 checks["all"]=all(checks.values()); return checks
def num(v):
 try:return float(str(v or "").strip().replace("%",""))
 except:return None
def join(archive,pcs):
 wanted={p:i for i,p in enumerate(pcs,1)}; byarea={}
 for p in pcs: byarea.setdefault(area(p),[]).append(p)
 rows=[]
 with zipfile.ZipFile(archive) as z:
  bad=z.testzip()
  if bad: raise RuntimeError("ZIP_CRC_FAILURE:"+bad)
  members={}
  for n in z.namelist():
   m=R2.search(n.replace("\\","/"))
   if m:
    a=m.group(1).upper()
    if a in members: raise RuntimeError("DUPLICATE_AREA_FILE:"+a)
    members[a]=n
  for a,group in sorted(byarea.items()):
   member=members.get(a)
   if not member:
    rows += [{"sample_index":wanted[p],"postcode_hash":ph(p),"postcode_area":a,"state":"NO_DATA_AREA_FILE_MISSING"} for p in group]; continue
   found={p:[] for p in group}
   with z.open(member) as raw:
    r=csv.DictReader(io.TextIOWrapper(raw,encoding="utf-8-sig",errors="strict",newline="")); fields=list(r.fieldnames or [])
    c={k:col(fields,v) for k,v in ALIASES.items()}; missing=[k for k,v in c.items() if not v]
    if missing: raise RuntimeError("CORE_COLUMNS_MISSING:"+",".join(missing))
    for rn,row in enumerate(r,2):
     p=normpc(row.get(c["postcode"],""))
     if p in found: found[p].append({"source_file":member,"source_row":rn,"sfbb":num(row.get(c["sfbb"])),"ufbb100":num(row.get(c["ufbb100"])),"ufbb300":num(row.get(c["ufbb300"])),"gigabit":num(row.get(c["gigabit"])),"unable30":num(row.get(c["unable30"]))})
   for p in group:
    f=found[p]; base={"sample_index":wanted[p],"postcode_hash":ph(p),"postcode_area":a,"source_file":member}
    if len(f)==1: rows.append(base|{"state":"PASS_EXACT_POSTCODE_MATCH","accuracy_tier":"3/4_POSTCODE_PROXY"}|f[0])
    elif not f: rows.append(base|{"state":"NO_DATA_EXACT_POSTCODE_NOT_FOUND"})
    else: rows.append(base|{"state":"REJECT_AMBIGUOUS_DUPLICATE_POSTCODE","duplicate_matches":len(f)})
 return sorted(rows,key=lambda x:x["sample_index"])
def main():
 p=argparse.ArgumentParser(); p.add_argument("--archive",required=True);p.add_argument("--samples",required=True);p.add_argument("--validation",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 archive=Path(a.archive).resolve(); output=Path(a.output).resolve(); v=json.loads(Path(a.validation).read_text(encoding="utf-8-sig")); g=gate(v,archive)
 out={"schema_version":1,"slot_id":SLOT_ID,"checked_at":now(),"archive_gate":g,"candidate_accuracy_written":0,"parcel_measured_values_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
 if not g["all"]: out|={"state":"BLOCKED_ARCHIVE_VALIDATION_GATE_NOT_ACCEPTED","operation_rows":[]}; code=2
 else:
  rows=join(archive,samples(Path(a.samples))); exact=sum(x["state"]=="PASS_EXACT_POSTCODE_MATCH" for x in rows); rejected=sum(x["state"].startswith("REJECT") for x in rows)
  out|={"state":"STRICT_24_SAMPLE_EXACT_POSTCODE_JOIN_COMPLETE" if not rejected else "STRICT_24_SAMPLE_JOIN_REVIEW_REQUIRED","sample_count":len(rows),"exact_postcode_matches":exact,"official_coverage_verified_candidates":exact,"candidate_accuracy_written":exact,"accuracy_tier":"3/4_POSTCODE_PROXY" if exact else None,"operation_rows":rows,"completed_at":now()}; code=0 if not rejected else 2
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return code
if __name__=="__main__": raise SystemExit(main())
