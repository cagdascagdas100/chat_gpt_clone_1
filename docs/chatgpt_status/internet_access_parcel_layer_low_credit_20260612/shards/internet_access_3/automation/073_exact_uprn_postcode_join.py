#!/usr/bin/env python3
"""Stream hydrated OS/ONS UPRN products into SQLite and validate exact UPRN joins.

The resulting examples are exact UPRN-to-postcode source relations. They are not parcel
relations and cannot raise the parcel confidence ceiling.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,re,sqlite3,tempfile,zipfile
from pathlib import Path
from typing import Any,Iterator,TextIO
SLOT_ID="internet_access_3"
DEFAULT_HYDRATION="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/050_full_release_hydration_manifest_latest.json"
DEFAULT_RUNNER_OUTPUT="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/051_exact_uprn_postcode_join_latest.json"
DEFAULT_WEB_OUTPUT="england_map_web/data/aays_21_slots/internet_access_3/exact_uprn_postcode_join_latest.json"
DEFAULT_PREVIEW="england_map_web/data/aays_21_slots/internet_access_3/exact_uprn_postcode_join_preview_latest.json"
POSTCODE_ALIASES=("PCDS","PCD","PCD2","POSTCODE")
def parse_args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--hydration',default=DEFAULT_HYDRATION);p.add_argument('--runner-output',default=DEFAULT_RUNNER_OUTPUT);p.add_argument('--web-output',default=DEFAULT_WEB_OUTPUT);p.add_argument('--preview-output',default=DEFAULT_PREVIEW);p.add_argument('--database',type=Path,default=Path(tempfile.gettempdir())/'aays_internet_access_3_uprn_join.sqlite');p.add_argument('--minimum-join-ratio',type=float,default=0.98);p.add_argument('--minimum-os-uprn-rows',type=int,default=30000000);p.add_argument('--preview-size',type=int,default=40);return p.parse_args()
def root(explicit):
 if explicit:return explicit.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repo root')
def load(path):
 with path.open('r',encoding='utf-8-sig') as h:return json.load(h)
def write(path,payload):
 path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(payload,h,ensure_ascii=False,separators=(',',':'));h.write('\n')
  os.replace(tmp,path)
 except Exception:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def norm_header(value):return re.sub(r'[^A-Z0-9]+','',str(value or '').upper())
def normalize_uprn(value):
 text=re.sub(r'\D+','',str(value or ''));return text if 1<=len(text)<=12 else None
def normalize_postcode(value):
 text=re.sub(r'\s+','',str(value or '').upper());return text if re.fullmatch(r'[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}',text) else None
def as_float(value):
 try:return float(value)
 except (TypeError,ValueError):return None
def text_streams(path:Path)->Iterator[tuple[str,TextIO]]:
 if zipfile.is_zipfile(path):
  archive=zipfile.ZipFile(path,'r')
  try:
   for item in archive.infolist():
    if item.is_dir() or not item.filename.lower().endswith(('.csv','.txt')):continue
    raw=archive.open(item,'r');text=io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline='');yield item.filename,text;text.close()
  finally:archive.close()
 else:
  with path.open('r',encoding='utf-8-sig',errors='replace',newline='') as text:yield path.name,text
def field_map(headers):
 normalized={norm_header(h):h for h in headers};postcode=next((normalized[a] for a in POSTCODE_ALIASES if a in normalized),None)
 return {'uprn':normalized.get('UPRN'),'x':normalized.get('XCOORDINATE'),'y':normalized.get('YCOORDINATE'),'lat':normalized.get('LATITUDE'),'lon':normalized.get('LONGITUDE'),'postcode':postcode}
def setup(conn):
 conn.executescript('''PRAGMA journal_mode=OFF;PRAGMA synchronous=OFF;PRAGMA temp_store=FILE;DROP TABLE IF EXISTS os_uprn;DROP TABLE IF EXISTS relation;CREATE TABLE os_uprn(uprn TEXT PRIMARY KEY,x REAL,y REAL,lat REAL,lon REAL);CREATE TABLE relation(source TEXT NOT NULL,uprn TEXT NOT NULL,postcode TEXT NOT NULL);CREATE INDEX relation_source_uprn ON relation(source,uprn);CREATE INDEX relation_uprn ON relation(uprn);''')
def import_os(conn,path,batch_size=10000):
 rows=0;duplicates=0;members=[];batch=[]
 for name,text in text_streams(path):
  reader=csv.DictReader(text);mapping=field_map(list(reader.fieldnames or []))
  if not all(mapping[k] for k in ('uprn','x','y','lat','lon')):continue
  member_rows=0
  for raw in reader:
   uprn=normalize_uprn(raw.get(mapping['uprn']));x=as_float(raw.get(mapping['x']));y=as_float(raw.get(mapping['y']));lat=as_float(raw.get(mapping['lat']));lon=as_float(raw.get(mapping['lon']))
   if not uprn or None in (x,y,lat,lon):continue
   batch.append((uprn,x,y,lat,lon));member_rows+=1
   if len(batch)>=batch_size:
    before=conn.total_changes;conn.executemany('INSERT OR IGNORE INTO os_uprn VALUES(?,?,?,?,?)',batch);changed=conn.total_changes-before;duplicates+=len(batch)-changed;rows+=changed;batch=[]
  members.append({'member':name,'accepted_rows':member_rows,'field_map':mapping})
 if batch:
  before=conn.total_changes;conn.executemany('INSERT OR IGNORE INTO os_uprn VALUES(?,?,?,?,?)',batch);changed=conn.total_changes-before;duplicates+=len(batch)-changed;rows+=changed
 conn.commit();return {'rows_inserted':rows,'duplicate_uprns':duplicates,'members':members}
def import_relation(conn,path,source,batch_size=20000):
 inserted=0;members=[];batch=[]
 for name,text in text_streams(path):
  reader=csv.DictReader(text);mapping=field_map(list(reader.fieldnames or []))
  if not mapping['uprn'] or not mapping['postcode']:continue
  member_rows=0
  for raw in reader:
   uprn=normalize_uprn(raw.get(mapping['uprn']));postcode=normalize_postcode(raw.get(mapping['postcode']))
   if not uprn or not postcode:continue
   batch.append((source,uprn,postcode));member_rows+=1
   if len(batch)>=batch_size:conn.executemany('INSERT INTO relation VALUES(?,?,?)',batch);inserted+=len(batch);batch=[]
  members.append({'member':name,'accepted_rows':member_rows,'field_map':mapping})
 if batch:conn.executemany('INSERT INTO relation VALUES(?,?,?)',batch);inserted+=len(batch)
 conn.commit();return {'rows_inserted':inserted,'members':members}
def source_stats(conn,source):
 distinct=int(conn.execute('SELECT COUNT(DISTINCT uprn) FROM relation WHERE source=?',(source,)).fetchone()[0]);matched=int(conn.execute('SELECT COUNT(DISTINCT r.uprn) FROM relation r JOIN os_uprn o ON o.uprn=r.uprn WHERE r.source=?',(source,)).fetchone()[0]);conflicts=int(conn.execute('SELECT COUNT(*) FROM (SELECT uprn FROM relation WHERE source=? GROUP BY uprn HAVING COUNT(DISTINCT postcode)>1)',(source,)).fetchone()[0]);return {'distinct_relation_uprns':distinct,'matched_os_uprns':matched,'join_ratio':round(matched/distinct,8) if distinct else 0.0,'duplicate_postcode_conflicts':conflicts}
def preview(conn,size):
 conn.create_function('stable_hash',1,lambda x:hashlib.sha1(str(x).encode()).hexdigest(),deterministic=True);query='''SELECT r.uprn,MIN(r.postcode),GROUP_CONCAT(DISTINCT r.source),o.x,o.y,o.lat,o.lon FROM relation r JOIN os_uprn o ON o.uprn=r.uprn GROUP BY r.uprn,o.x,o.y,o.lat,o.lon HAVING COUNT(DISTINCT r.source)>=1 AND COUNT(DISTINCT r.postcode)=1 ORDER BY stable_hash(r.uprn) LIMIT ?''';result=[]
 for uprn,postcode,sources,x,y,lat,lon in conn.execute(query,(size,)):result.append({'uprn':uprn,'postcode':postcode,'sources':sorted(str(sources).split(',')),'x_coordinate':x,'y_coordinate':y,'latitude':lat,'longitude':lon,'relation_semantics':'EXACT_UPRN_TO_POSTCODE_SOURCE_RELATION_NOT_PARCEL_RELATION','parcel_relation_promoted':False})
 return result
def main():
 o=parse_args();r=root(o.repo_root);hydration=load(r/o.hydration);blockers=[]
 if hydration.get('state')!='runtime_validation_passed' or int(hydration.get('packages_hydrated') or 0)!=4:blockers.append('FULL_RELEASE_HYDRATION_NOT_PASSED')
 packages={item.get('package_id'):item for item in hydration.get('packages') or [] if isinstance(item,dict)}
 for key in ('os_open_uprn','nsul','onsud'):
  if key not in packages or not packages[key].get('cache_path'):blockers.append(key.upper()+'_PACKAGE_MISSING')
 if blockers:
  summary={'schema_version':1,'slot_id':SLOT_ID,'state':'blocked','validation':{'passed':False,'blockers':blockers},'parcel_relations_promoted':0,'confidence_uplifts':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,summary);write(r/o.web_output,summary);print(json.dumps(summary,indent=2));return 2
 db=o.database.expanduser().resolve();db.parent.mkdir(parents=True,exist_ok=True)
 if db.exists():db.unlink()
 conn=sqlite3.connect(db)
 try:
  setup(conn);os_audit=import_os(conn,Path(packages['os_open_uprn']['cache_path']));relation_audits={source:import_relation(conn,Path(packages[source]['cache_path']),source) for source in ('nsul','onsud')};stats={source:source_stats(conn,source) for source in ('nsul','onsud')};cross_conflicts=int(conn.execute('SELECT COUNT(*) FROM (SELECT uprn FROM relation GROUP BY uprn HAVING COUNT(DISTINCT postcode)>1)').fetchone()[0]);examples=preview(conn,o.preview_size)
 finally:conn.close()
 if os_audit['rows_inserted']<o.minimum_os_uprn_rows:blockers.append(f"OS_OPEN_UPRN_ROW_COUNT_BELOW_MINIMUM:{os_audit['rows_inserted']}<{o.minimum_os_uprn_rows}")
 if os_audit['duplicate_uprns']!=0:blockers.append('OS_OPEN_UPRN_DUPLICATE_KEYS')
 for source,value in stats.items():
  if value['distinct_relation_uprns']==0:blockers.append(source.upper()+'_NO_RELATION_ROWS')
  if value['join_ratio']<o.minimum_join_ratio:blockers.append(f"{source.upper()}_JOIN_RATIO_BELOW_GATE:{value['join_ratio']}<{o.minimum_join_ratio}")
  if value['duplicate_postcode_conflicts']!=0:blockers.append(source.upper()+'_DUPLICATE_POSTCODE_CONFLICTS')
 if cross_conflicts!=0:blockers.append('NSUL_ONSUD_POSTCODE_CONFLICTS')
 if len(examples)!=o.preview_size:blockers.append(f'JOIN_PREVIEW_COUNT_MISMATCH:{len(examples)}!={o.preview_size}')
 passed=not blockers;now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();summary={'schema_version':1,'task_id':'aays1-internet-access-3-exact-uprn-postcode-join-20260722','slot_id':SLOT_ID,'state':'runtime_validation_passed' if passed else 'blocked','updated_at':now,'database_path':str(db),'os_open_uprn':os_audit,'relation_imports':relation_audits,'join_stats':stats,'cross_source_postcode_conflicts':cross_conflicts,'join_ratio_minimum':o.minimum_join_ratio,'preview_rows_written':len(examples),'source_checks_executed':4,'validation':{'passed':passed,'blockers':blockers},'relation_semantics':'EXACT_UPRN_TO_POSTCODE_SOURCE_JOIN_ONLY','parcel_relations_promoted':0,'confidence_uplifts':0,'actual_business_data_rows_written':0,'first_unverified_step_after_run':'ESTABLISH_EXACT_PARCEL_OR_HMLR_FEATURE_TO_UPRN_RELATION_OR_RETAIN_POSTCODE_PROXY','final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,summary);write(r/o.web_output,summary);write(r/o.preview_output,{'schema_version':1,'slot_id':SLOT_ID,'updated_at':now,'row_count':len(examples),'rows':examples,'parcel_relations_promoted':0,'final_ready':False});print(json.dumps(summary,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as exc:print(json.dumps({'slot_id':SLOT_ID,'state':'exception','error_type':type(exc).__name__,'error':str(exc),'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},indent=2),file=__import__('sys').stderr);raise
