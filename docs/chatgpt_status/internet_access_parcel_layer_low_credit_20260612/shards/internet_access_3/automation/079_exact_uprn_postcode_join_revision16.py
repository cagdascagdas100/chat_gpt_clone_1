#!/usr/bin/env python3
"""Corrected streaming exact UPRN-to-postcode join.

Requires NSUL and ONSUD to agree on the same UPRN and normalized postcode for every
published preview row. Uses a WITHOUT ROWID relation table and a materialized common
table to avoid the revision-15 single-source preview defect.
"""
from __future__ import annotations
import argparse,csv,io,json,os,re,sqlite3,tempfile,zipfile
from pathlib import Path
from typing import Iterator,TextIO

SLOT_ID="internet_access_3"
DEFAULT_HYDRATION="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/050_full_release_hydration_manifest_latest.json"
DEFAULT_PREFLIGHT="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/052_runtime_resource_download_preflight_latest.json"
DEFAULT_RUNNER="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/053_exact_uprn_postcode_join_revision16_latest.json"
DEFAULT_WEB="england_map_web/data/aays_21_slots/internet_access_3/exact_uprn_postcode_join_revision16_latest.json"
DEFAULT_PREVIEW="england_map_web/data/aays_21_slots/internet_access_3/exact_uprn_postcode_join_revision16_preview_latest.json"
POSTCODE_ALIASES=("PCDS","PCD","PCD2","POSTCODE")

def args():
    p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--hydration",default=DEFAULT_HYDRATION);p.add_argument("--preflight",default=DEFAULT_PREFLIGHT)
    p.add_argument("--runner-output",default=DEFAULT_RUNNER);p.add_argument("--web-output",default=DEFAULT_WEB);p.add_argument("--preview-output",default=DEFAULT_PREVIEW)
    p.add_argument("--database",type=Path,default=Path(tempfile.gettempdir())/"aays_internet_access_3_uprn_join_revision16.sqlite")
    p.add_argument("--minimum-join-ratio",type=float,default=0.98);p.add_argument("--minimum-os-uprn-rows",type=int,default=30000000)
    p.add_argument("--minimum-common-ratio",type=float,default=0.95);p.add_argument("--preview-size",type=int,default=40);return p.parse_args()
def root(explicit):
    if explicit:return explicit.expanduser().resolve()
    for p in [Path.cwd(),*Path(__file__).resolve().parents]:
        if (p/"docs").exists() and (p/"england_map_web").exists():return p
    raise FileNotFoundError("repo root")
def load(path):
    with path.open("r",encoding="utf-8-sig") as h:return json.load(h)
def write(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(payload,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
        os.replace(tmp,path)
    except Exception:
        try:os.unlink(tmp)
        except FileNotFoundError:pass
        raise
def norm_header(v):return re.sub(r"[^A-Z0-9]+","",str(v or "").upper())
def normalize_uprn(v):
    x=re.sub(r"\D+","",str(v or ""));return x if 1<=len(x)<=12 else None
def normalize_postcode(v):
    x=re.sub(r"\s+","",str(v or "").upper());return x if re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}",x) else None
def number(v):
    try:return float(v)
    except (TypeError,ValueError):return None
def text_streams(path:Path)->Iterator[tuple[str,TextIO]]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path,"r") as z:
            for item in z.infolist():
                if item.is_dir() or not item.filename.lower().endswith((".csv",".txt")):continue
                with z.open(item,"r") as raw:
                    text=io.TextIOWrapper(raw,encoding="utf-8-sig",errors="replace",newline="")
                    try:yield item.filename,text
                    finally:text.detach()
    else:
        with path.open("r",encoding="utf-8-sig",errors="replace",newline="") as text:yield path.name,text
def mapping(headers):
    n={norm_header(h):h for h in headers};pc=next((n[a] for a in POSTCODE_ALIASES if a in n),None)
    return {"uprn":n.get("UPRN"),"x":n.get("XCOORDINATE"),"y":n.get("YCOORDINATE"),"lat":n.get("LATITUDE"),"lon":n.get("LONGITUDE"),"postcode":pc}
def setup(c):
    c.executescript("""PRAGMA journal_mode=OFF;PRAGMA synchronous=OFF;PRAGMA temp_store=FILE;
    DROP TABLE IF EXISTS os_uprn;DROP TABLE IF EXISTS relation;DROP TABLE IF EXISTS common;
    CREATE TABLE os_uprn(uprn TEXT PRIMARY KEY,x REAL,y REAL,lat REAL,lon REAL) WITHOUT ROWID;
    CREATE TABLE relation(source TEXT NOT NULL,uprn TEXT NOT NULL,postcode TEXT NOT NULL,PRIMARY KEY(source,uprn,postcode)) WITHOUT ROWID;
    CREATE INDEX relation_uprn_source ON relation(uprn,source,postcode);""")
def import_os(c,path,batch_size=20000):
    rows=duplicates=0;members=[];batch=[]
    for name,text in text_streams(path):
        reader=csv.DictReader(text);m=mapping(reader.fieldnames or [])
        if not all(m[k] for k in ("uprn","x","y","lat","lon")):continue
        accepted=0
        for raw in reader:
            u=normalize_uprn(raw.get(m["uprn"]));vals=(number(raw.get(m["x"])),number(raw.get(m["y"])),number(raw.get(m["lat"])),number(raw.get(m["lon"])))
            if not u or any(v is None for v in vals):continue
            batch.append((u,*vals));accepted+=1
            if len(batch)>=batch_size:
                before=c.total_changes;c.executemany("INSERT OR IGNORE INTO os_uprn VALUES(?,?,?,?,?)",batch);changed=c.total_changes-before;rows+=changed;duplicates+=len(batch)-changed;batch=[]
        members.append({"member":name,"accepted_rows":accepted,"field_map":m})
    if batch:
        before=c.total_changes;c.executemany("INSERT OR IGNORE INTO os_uprn VALUES(?,?,?,?,?)",batch);changed=c.total_changes-before;rows+=changed;duplicates+=len(batch)-changed
    c.commit();return {"rows_inserted":rows,"duplicate_uprns":duplicates,"members":members}
def import_relation(c,path,source,batch_size=30000):
    inserted=duplicates=0;members=[];batch=[]
    for name,text in text_streams(path):
        reader=csv.DictReader(text);m=mapping(reader.fieldnames or [])
        if not m["uprn"] or not m["postcode"]:continue
        accepted=0
        for raw in reader:
            u=normalize_uprn(raw.get(m["uprn"]));pc=normalize_postcode(raw.get(m["postcode"]))
            if not u or not pc:continue
            batch.append((source,u,pc));accepted+=1
            if len(batch)>=batch_size:
                before=c.total_changes;c.executemany("INSERT OR IGNORE INTO relation VALUES(?,?,?)",batch);changed=c.total_changes-before;inserted+=changed;duplicates+=len(batch)-changed;batch=[]
        members.append({"member":name,"accepted_rows":accepted,"field_map":m})
    if batch:
        before=c.total_changes;c.executemany("INSERT OR IGNORE INTO relation VALUES(?,?,?)",batch);changed=c.total_changes-before;inserted+=changed;duplicates+=len(batch)-changed
    c.commit();return {"rows_inserted":inserted,"duplicate_identical_rows":duplicates,"members":members}
def source_stats(c,source):
    distinct=int(c.execute("SELECT COUNT(DISTINCT uprn) FROM relation WHERE source=?",(source,)).fetchone()[0])
    matched=int(c.execute("SELECT COUNT(DISTINCT r.uprn) FROM relation r JOIN os_uprn o ON o.uprn=r.uprn WHERE r.source=?",(source,)).fetchone()[0])
    conflicts=int(c.execute("SELECT COUNT(*) FROM (SELECT uprn FROM relation WHERE source=? GROUP BY uprn HAVING COUNT(DISTINCT postcode)>1)",(source,)).fetchone()[0])
    return {"distinct_relation_uprns":distinct,"matched_os_uprns":matched,"join_ratio":round(matched/distinct,8) if distinct else 0.0,"duplicate_postcode_conflicts":conflicts}
def build_common(c):
    c.executescript("""DROP TABLE IF EXISTS common;
    CREATE TABLE common(uprn TEXT PRIMARY KEY,postcode TEXT NOT NULL) WITHOUT ROWID;
    INSERT INTO common(uprn,postcode)
    SELECT n.uprn,n.postcode FROM relation n
    JOIN relation d ON d.uprn=n.uprn AND d.postcode=n.postcode
    JOIN os_uprn o ON o.uprn=n.uprn
    WHERE n.source='nsul' AND d.source='onsud'
    GROUP BY n.uprn,n.postcode
    HAVING COUNT(DISTINCT n.postcode)=1;
    """)
    c.commit();return int(c.execute("SELECT COUNT(*) FROM common").fetchone()[0])
def cross_conflicts(c):
    return int(c.execute("""SELECT COUNT(*) FROM (
      SELECT n.uprn FROM relation n JOIN relation d ON d.uprn=n.uprn
      WHERE n.source='nsul' AND d.source='onsud' AND n.postcode<>d.postcode GROUP BY n.uprn)""").fetchone()[0])
def preview(c,size):
    sql="""SELECT x.uprn,x.postcode,o.x,o.y,o.lat,o.lon FROM common x JOIN os_uprn o ON o.uprn=x.uprn ORDER BY x.uprn LIMIT ?"""
    return [{"uprn":u,"postcode":pc,"sources":["nsul","onsud"],"x_coordinate":x,"y_coordinate":y,"latitude":lat,"longitude":lon,
      "relation_semantics":"EXACT_SAME_UPRN_AND_POSTCODE_IN_NSUL_AND_ONSUD_NOT_PARCEL_RELATION","parcel_relation_promoted":False}
      for u,pc,x,y,lat,lon in c.execute(sql,(size,))]
def main():
    o=args();r=root(o.repo_root);hydration=load(r/o.hydration);preflight=load(r/o.preflight);blockers=[]
    if preflight.get("state")!="runtime_validation_passed":blockers.append("RUNTIME_RESOURCE_PREFLIGHT_NOT_PASSED")
    if hydration.get("state")!="runtime_validation_passed" or int(hydration.get("packages_hydrated") or 0)!=4:blockers.append("FULL_RELEASE_HYDRATION_NOT_PASSED")
    packages={x.get("package_id"):x for x in hydration.get("packages") or [] if isinstance(x,dict)}
    for k in ("os_open_uprn","nsul","onsud"):
        if k not in packages or not packages[k].get("cache_path"):blockers.append(k.upper()+"_PACKAGE_MISSING")
    if blockers:
        s={"schema_version":1,"slot_id":SLOT_ID,"state":"blocked","validation":{"passed":False,"blockers":blockers},"parcel_relations_promoted":0,
        "confidence_uplifts":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
        write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,indent=2));return 2
    db=o.database.expanduser().resolve();db.parent.mkdir(parents=True,exist_ok=True)
    if db.exists():db.unlink()
    c=sqlite3.connect(db)
    try:
        setup(c);os_audit=import_os(c,Path(packages["os_open_uprn"]["cache_path"]))
        imports={s:import_relation(c,Path(packages[s]["cache_path"]),s) for s in ("nsul","onsud")}
        stats={s:source_stats(c,s) for s in ("nsul","onsud")};conflicts=cross_conflicts(c);common=build_common(c);examples=preview(c,o.preview_size)
    finally:c.close()
    if os_audit["rows_inserted"]<o.minimum_os_uprn_rows:blockers.append(f"OS_OPEN_UPRN_ROW_COUNT_BELOW_MINIMUM:{os_audit['rows_inserted']}<{o.minimum_os_uprn_rows}")
    if os_audit["duplicate_uprns"]!=0:blockers.append("OS_OPEN_UPRN_DUPLICATE_KEYS")
    for source,value in stats.items():
        if value["distinct_relation_uprns"]==0:blockers.append(source.upper()+"_NO_RELATION_ROWS")
        if value["join_ratio"]<o.minimum_join_ratio:blockers.append(f"{source.upper()}_JOIN_RATIO_BELOW_GATE:{value['join_ratio']}<{o.minimum_join_ratio}")
        if value["duplicate_postcode_conflicts"]!=0:blockers.append(source.upper()+"_DUPLICATE_POSTCODE_CONFLICTS")
    denominator=min(stats["nsul"]["matched_os_uprns"],stats["onsud"]["matched_os_uprns"])
    common_ratio=round(common/denominator,8) if denominator else 0.0
    if common_ratio<o.minimum_common_ratio:blockers.append(f"NSUL_ONSUD_COMMON_EXACT_RATIO_BELOW_GATE:{common_ratio}<{o.minimum_common_ratio}")
    if conflicts!=0:blockers.append("NSUL_ONSUD_POSTCODE_CONFLICTS")
    if len(examples)!=o.preview_size:blockers.append(f"JOIN_PREVIEW_COUNT_MISMATCH:{len(examples)}!={o.preview_size}")
    if any(set(x["sources"])!={"nsul","onsud"} for x in examples):blockers.append("PREVIEW_NOT_DUAL_SOURCE")
    passed=not blockers;now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary={"schema_version":1,"task_id":"aays1-internet-access-3-exact-uprn-postcode-join-revision16-20260722","slot_id":SLOT_ID,
    "state":"runtime_validation_passed" if passed else "blocked","updated_at":now,"database_path":str(db),"os_open_uprn":os_audit,"relation_imports":imports,
    "join_stats":stats,"common_exact_uprn_postcode_rows":common,"common_exact_ratio":common_ratio,"cross_source_postcode_conflicts":conflicts,
    "join_ratio_minimum":o.minimum_join_ratio,"common_ratio_minimum":o.minimum_common_ratio,"preview_rows_written":len(examples),"source_checks_executed":4,
    "validation":{"passed":passed,"blockers":blockers},"relation_semantics":"EXACT_SAME_UPRN_AND_POSTCODE_IN_NSUL_AND_ONSUD_ONLY",
    "parcel_relations_promoted":0,"confidence_uplifts":0,"actual_business_data_rows_written":0,
    "first_unverified_step_after_run":"ESTABLISH_EXACT_PARCEL_OR_HMLR_FEATURE_TO_UPRN_RELATION_OR_RETAIN_POSTCODE_PROXY",
    "final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    write(r/o.runner_output,summary);write(r/o.web_output,summary)
    write(r/o.preview_output,{"schema_version":1,"slot_id":SLOT_ID,"updated_at":now,"row_count":len(examples),"rows":examples,
    "dual_source_required":True,"parcel_relations_promoted":0,"final_ready":False})
    print(json.dumps(summary,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id":SLOT_ID,"state":"exception","error_type":type(exc).__name__,"error":str(exc),"final_ready":False,
        "fake_data":False,"db_write":False,"migration":False,"production_deploy":False},indent=2),file=__import__("sys").stderr);raise
