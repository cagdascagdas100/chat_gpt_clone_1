#!/usr/bin/env python3
"""Checkpointed exact UPRN/postcode join with full-table resume fingerprints."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,re,sqlite3,tempfile
from pathlib import Path
SLOT_ID='internet_access_3';AUTOMATION=Path(__file__).resolve().parent;HEX64=re.compile(r'^[0-9a-f]{64}$')
BASE='docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/'
def args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--hydration',default=BASE+'050_full_release_hydration_manifest_latest.json');p.add_argument('--preflight',default=BASE+'052_runtime_resource_download_preflight_latest.json');p.add_argument('--cache-ledger',default=BASE+'055_release_cache_identity_ledger_latest.json');p.add_argument('--runner-output',default=BASE+'056_exact_uprn_postcode_join_revision17_latest.json');p.add_argument('--web-output',default='england_map_web/data/aays_21_slots/internet_access_3/exact_uprn_postcode_join_revision17_latest.json');p.add_argument('--preview-output',default='england_map_web/data/aays_21_slots/internet_access_3/exact_uprn_postcode_join_revision17_preview_latest.json');p.add_argument('--database',type=Path,default=Path(tempfile.gettempdir())/'aays_internet_access_3_uprn_join_revision17.sqlite');p.add_argument('--minimum-join-ratio',type=float,default=.98);p.add_argument('--minimum-common-ratio',type=float,default=.95);p.add_argument('--minimum-os-uprn-rows',type=int,default=30000000);p.add_argument('--preview-size',type=int,default=40);return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repo root')
def load(p):
 with p.open('r',encoding='utf-8-sig') as h:return json.load(h)
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(o,h,ensure_ascii=False,separators=(',',':'));h.write('\n')
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def import_rev16():
 p=AUTOMATION/'079_exact_uprn_postcode_join_revision16.py';s=importlib.util.spec_from_file_location('rev16_join',p)
 if not s or not s.loader:raise ImportError(p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def package_manifest(packages):
 rows=[]
 for key in ('os_open_uprn','nsul','onsud'):
  x=packages.get(key) or {};sha=str(x.get('actual_sha256') or '').lower();path=Path(str(x.get('cache_path') or ''))
  if not HEX64.fullmatch(sha):raise ValueError(key.upper()+'_SHA256_MISSING_OR_INVALID')
  if not path.is_file():raise FileNotFoundError(path)
  size=path.stat().st_size;expected=int(x.get('bytes_hydrated') or 0)
  if expected and size!=expected:raise ValueError(f'{key.upper()}_SIZE_CHANGED:{size}!={expected}')
  rows.append({'package_id':key,'sha256':sha,'size':size,'cache_path':str(path)})
 return rows,hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def checkpoint_schema(c):c.execute('CREATE TABLE IF NOT EXISTS checkpoint(stage TEXT PRIMARY KEY,manifest_sha256 TEXT NOT NULL,completed_at TEXT NOT NULL,row_count INTEGER NOT NULL,audit_json TEXT NOT NULL) WITHOUT ROWID');c.commit()
def get_cp(c,stage,manifest):
 row=c.execute('SELECT row_count,audit_json FROM checkpoint WHERE stage=? AND manifest_sha256=?',(stage,manifest)).fetchone();return None if not row else {'row_count':int(row[0]),'audit':json.loads(row[1])}
def _table_meta(c,table):
 if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',table):raise ValueError('invalid table')
 info=c.execute(f'PRAGMA table_info("{table}")').fetchall()
 if not info:raise ValueError('missing table:'+table)
 cols=[str(x[1]) for x in info];pk=[str(x[1]) for x in sorted((x for x in info if int(x[5])>0),key=lambda x:int(x[5]))]
 return cols,pk or cols
def table_fingerprint(c,table,where='',params=(),batch_size=50000):
 cols,order=_table_meta(c,table);q='SELECT '+','.join(f'"{x}"' for x in cols)+f' FROM "{table}"'
 if where:q+=' WHERE '+where
 q+=' ORDER BY '+','.join(f'"{x}"' for x in order)
 h=hashlib.sha256();h.update(json.dumps({'table':table,'columns':cols,'order':order,'where':where},sort_keys=True,separators=(',',':')).encode())
 count=0;cur=c.execute(q,params)
 while True:
  rows=cur.fetchmany(batch_size)
  if not rows:break
  for row in rows:
   h.update(json.dumps(row,ensure_ascii=False,separators=(',',':'),default=str).encode());h.update(b'\n')
  count+=len(rows)
 return {'sha256':h.hexdigest(),'rows_hashed':count,'columns':cols,'order_by':order}
def put_cp(c,stage,manifest,row_count,audit,table,where='',params=()):
 fp=table_fingerprint(c,table,where,params)
 if fp['rows_hashed']!=int(row_count):raise ValueError(f'{stage}_FINGERPRINT_COUNT_MISMATCH')
 payload=dict(audit);payload['_checkpoint_fingerprint']=fp
 now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();c.execute('INSERT OR REPLACE INTO checkpoint VALUES(?,?,?,?,?)',(stage,manifest,now,int(row_count),json.dumps(payload,separators=(',',':'))));c.commit()
def table_count(c,table,where='',params=()):return int(c.execute('SELECT COUNT(*) FROM '+table+(' WHERE '+where if where else ''),params).fetchone()[0])
def valid_cp(c,stage,manifest,table,where='',params=()):
 cp=get_cp(c,stage,manifest)
 if not cp or table_count(c,table,where,params)!=cp['row_count']:return None
 saved=(cp.get('audit') or {}).get('_checkpoint_fingerprint')
 if not isinstance(saved,dict) or not HEX64.fullmatch(str(saved.get('sha256') or '')):return None
 current=table_fingerprint(c,table,where,params)
 return cp if current==saved else None
def build_common_safe(c):
 c.executescript("""DROP TABLE IF EXISTS common;
 CREATE TABLE common(uprn TEXT PRIMARY KEY,postcode TEXT NOT NULL) WITHOUT ROWID;
 WITH ns AS (
   SELECT uprn,MIN(postcode) AS postcode FROM relation
   WHERE source='nsul' GROUP BY uprn HAVING COUNT(DISTINCT postcode)=1
 ), od AS (
   SELECT uprn,MIN(postcode) AS postcode FROM relation
   WHERE source='onsud' GROUP BY uprn HAVING COUNT(DISTINCT postcode)=1
 )
 INSERT INTO common(uprn,postcode)
 SELECT ns.uprn,ns.postcode FROM ns JOIN od ON od.uprn=ns.uprn AND od.postcode=ns.postcode
 JOIN os_uprn o ON o.uprn=ns.uprn;""")
 c.commit();return int(c.execute('SELECT COUNT(*) FROM common').fetchone()[0])
def preview(c,size):
 sql='SELECT x.uprn,x.postcode,o.x,o.y,o.lat,o.lon FROM common x JOIN os_uprn o ON o.uprn=x.uprn ORDER BY x.uprn LIMIT ?'
 return [{'uprn':u,'postcode':pc,'sources':['nsul','onsud'],'x_coordinate':x,'y_coordinate':y,'latitude':lat,'longitude':lon,'relation_semantics':'EXACT_SAME_UPRN_AND_POSTCODE_IN_NSUL_AND_ONSUD_NOT_PARCEL_RELATION','parcel_relation_promoted':False} for u,pc,x,y,lat,lon in c.execute(sql,(size,))]
def main():
 o=args();r=root(o.repo_root);hydr=load(r/o.hydration);pre=load(r/o.preflight);ledger=load(r/o.cache_ledger);blockers=[]
 if pre.get('state')!='runtime_validation_passed':blockers.append('RESOURCE_PREFLIGHT_NOT_PASSED')
 if ledger.get('state')!='runtime_validation_passed' or int(ledger.get('packages_bound') or 0)!=4:blockers.append('CACHE_IDENTITY_LEDGER_NOT_PASSED')
 if hydr.get('state')!='runtime_validation_passed' or int(hydr.get('packages_hydrated') or 0)!=4:blockers.append('HYDRATION_NOT_PASSED')
 packages={x.get('package_id'):x for x in hydr.get('packages') or [] if isinstance(x,dict)}
 if blockers:
  s={'schema_version':2,'slot_id':SLOT_ID,'state':'blocked','validation':{'passed':False,'blockers':blockers},'stages_resumed':0,'stages_executed':0,'parcel_relations_promoted':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,s);write(r/o.web_output,s);return 2
 manifest_rows,manifest=package_manifest(packages);db=o.database.expanduser().resolve();db.parent.mkdir(parents=True,exist_ok=True);rev16=import_rev16();resumed=[];executed=[];fingerprints={};c=sqlite3.connect(db)
 try:
  checkpoint_schema(c);existing={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")};old=c.execute('SELECT DISTINCT manifest_sha256 FROM checkpoint').fetchall()
  if old and any(x[0]!=manifest for x in old):
   c.close();q=db.with_suffix(db.suffix+'.stale.'+manifest[:12]);n=1
   while q.exists():q=db.with_suffix(db.suffix+f'.stale.{manifest[:12]}.{n}');n+=1
   os.replace(db,q);c=sqlite3.connect(db);existing=set()
  if not {'os_uprn','relation'}.issubset(existing):rev16.setup(c);checkpoint_schema(c)
  cp=valid_cp(c,'os_import',manifest,'os_uprn')
  if cp:os_audit=cp['audit'];resumed.append('os_import')
  else:
   c.execute('DELETE FROM os_uprn');c.commit();os_audit=rev16.import_os(c,Path(packages['os_open_uprn']['cache_path']));put_cp(c,'os_import',manifest,table_count(c,'os_uprn'),os_audit,'os_uprn');executed.append('os_import')
  fingerprints['os_import']=get_cp(c,'os_import',manifest)['audit']['_checkpoint_fingerprint']
  imports={}
  for source in ('nsul','onsud'):
   stage=source+'_import';cp=valid_cp(c,stage,manifest,'relation','source=?',(source,))
   if cp:imports[source]=cp['audit'];resumed.append(stage)
   else:
    c.execute('DELETE FROM relation WHERE source=?',(source,));c.commit();imports[source]=rev16.import_relation(c,Path(packages[source]['cache_path']),source);put_cp(c,stage,manifest,table_count(c,'relation','source=?',(source,)),imports[source],'relation','source=?',(source,));executed.append(stage)
   fingerprints[stage]=get_cp(c,stage,manifest)['audit']['_checkpoint_fingerprint']
  stats={s:rev16.source_stats(c,s) for s in ('nsul','onsud')};conflicts=rev16.cross_conflicts(c);tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")};cp=valid_cp(c,'common_build',manifest,'common') if 'common' in tables else None
  if cp:common=cp['row_count'];resumed.append('common_build')
  else:
   common=build_common_safe(c);put_cp(c,'common_build',manifest,common,{'rows':common},'common');executed.append('common_build')
  fingerprints['common_build']=get_cp(c,'common_build',manifest)['audit']['_checkpoint_fingerprint'];examples=preview(c,o.preview_size)
 finally:c.close()
 if os_audit['rows_inserted']<o.minimum_os_uprn_rows:blockers.append('OS_OPEN_UPRN_ROW_COUNT_BELOW_MINIMUM')
 if os_audit['duplicate_uprns']!=0:blockers.append('OS_OPEN_UPRN_DUPLICATE_KEYS')
 for source,value in stats.items():
  if value['join_ratio']<o.minimum_join_ratio:blockers.append(source.upper()+'_JOIN_RATIO_BELOW_GATE')
  if value['duplicate_postcode_conflicts']!=0:blockers.append(source.upper()+'_DUPLICATE_POSTCODE_CONFLICTS')
 denominator=min(stats['nsul']['matched_os_uprns'],stats['onsud']['matched_os_uprns']);common_ratio=round(common/denominator,8) if denominator else 0.0
 if common_ratio<o.minimum_common_ratio:blockers.append('COMMON_EXACT_RATIO_BELOW_GATE')
 if conflicts!=0:blockers.append('CROSS_SOURCE_POSTCODE_CONFLICTS')
 if len(examples)!=o.preview_size:blockers.append('PREVIEW_COUNT_MISMATCH')
 if any(set(x.get('sources') or [])!={'nsul','onsud'} for x in examples):blockers.append('PREVIEW_NOT_DUAL_SOURCE')
 passed=not blockers;now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();s={'schema_version':2,'task_id':'aays1-internet-access-3-checkpointed-exact-uprn-join-20260722','slot_id':SLOT_ID,'state':'runtime_validation_passed' if passed else 'blocked','updated_at':now,'database_path':str(db),'input_manifest':manifest_rows,'input_manifest_sha256':manifest,'stages_total':4,'stages_resumed':len(resumed),'stages_executed':len(executed),'resumed_stage_names':resumed,'executed_stage_names':executed,'checkpoint_fingerprints':fingerprints,'checkpoint_validation_semantics':'FULL_ORDERED_TABLE_CONTENT_SHA256_NOT_ROW_COUNT_ONLY','os_open_uprn':os_audit,'relation_imports':imports,'join_stats':stats,'common_exact_uprn_postcode_rows':common,'common_exact_ratio':common_ratio,'cross_source_postcode_conflicts':conflicts,'preview_rows_written':len(examples),'source_checks_executed':6,'validation':{'passed':passed,'blockers':blockers},'relation_semantics':'CHECKPOINTED_EXACT_SAME_UPRN_AND_POSTCODE_IN_NSUL_AND_ONSUD_ONLY','parcel_relations_promoted':0,'confidence_uplifts':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
 write(r/o.runner_output,s);write(r/o.web_output,s);write(r/o.preview_output,{'schema_version':2,'slot_id':SLOT_ID,'updated_at':now,'row_count':len(examples),'rows':examples,'input_manifest_sha256':manifest,'dual_source_required':True,'parcel_relations_promoted':0,'final_ready':False});print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
