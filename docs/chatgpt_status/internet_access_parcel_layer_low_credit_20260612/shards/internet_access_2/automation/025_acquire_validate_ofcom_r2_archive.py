# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, csv, hashlib, http.cookiejar, io, json, os, re, shutil, subprocess, sys, time, urllib.parse, urllib.request, uuid, zipfile
from datetime import datetime, timezone
from pathlib import Path

SLOT='internet_access_2'
TASK='internet-access-2-ofcom-dynamic-zip-join-existing-11013-v2-20260722T041000Z'
KEY='40ce1dc4f1ad5a0ab95078c6b920881699b36760c9c4579f3050b21d6cd68e36'
QUEUE=Path('docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/queue/internet_access_2_ofcom_dynamic_zip_join_existing_11013_006.v3.task.json')
OUT=Path('docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2')
READBACK=OUT/'source_snapshots/012_ofcom_spring_2026_archive_download_readback.json'
VALIDATION=OUT/'validation/012_ofcom_r2_archive_strict_validation.json'
STATUS=OUT/'status/012_status.json'
PROGRESS=OUT/'progress/012_progress.jsonl'
HOST='www.ofcom.org.uk'; TYPES={'application/zip','application/x-zip-compressed','application/octet-stream'}
R2=re.compile(r'(?:^|/)202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$',re.I)
R1=re.compile(r'(?:^|/)202601_fixed_postcode_coverage_r1_([A-Z0-9]+)\.csv$',re.I)
ALIASES={
 'postcode':['postcode','postcode_space'],'postcode_area':['postcode area','postcode_area'],
 'sfbb':['SFBB availability (% premises)','SFBB availability'],
 'ufbb100':['UFBB (100Mbit/s) availability (% premises)','UFBB100 availability (% premises)'],
 'ufbb300':['UFBB availability (% premises)','UFBB (300Mbit/s) availability (% premises)'],
 'gigabit':['Gigabit availability (% premises)','Gigabit availability'],
 'unable30':['% of premises unable to receive 30Mbit/s','unable to receive 30Mbit/s']}

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def norm(v): return re.sub(r'[^a-z0-9]+','',str(v or '').casefold())
def sha(path):
 d=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): d.update(b)
 return d.hexdigest()
def write(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_name(path.name+'.tmp.'+uuid.uuid4().hex)
 tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); os.replace(tmp,path)
def append(path,obj):
 old=path.read_text(encoding='utf-8') if path.exists() else ''
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_name(path.name+'.tmp.'+uuid.uuid4().hex)
 tmp.write_text(old+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8'); os.replace(tmp,path)
def check_url(url):
 p=urllib.parse.urlparse(url)
 if p.scheme!='https' or p.hostname!=HOST: raise RuntimeError('OFFICIAL_URL_SCOPE_VIOLATION:'+url)
def repo_root(arg):
 if arg: return Path(arg).resolve()
 if os.getenv('AAYS_REPO_ROOT'): return Path(os.environ['AAYS_REPO_ROOT']).resolve()
 p=subprocess.run(['git','rev-parse','--show-toplevel'],text=True,capture_output=True)
 if p.returncode: raise RuntimeError('REPO_ROOT_UNRESOLVED')
 return Path(p.stdout.strip()).resolve()
def archive_path(arg,portable):
 if arg: return Path(arg).resolve()
 root=portable or os.getenv('AAYS_PORTABLE_ROOT')
 if not root: raise RuntimeError('AAYS_PORTABLE_ROOT_REQUIRED')
 return Path(root).resolve()/'state/source_cache/ofcom_spring_2026/ofcom_fixed_coverage_202601_v2.zip'
def task_contract(repo,override):
 p=Path(override).resolve() if override else repo/QUEUE
 t=json.loads(p.read_text(encoding='utf-8-sig'))
 if t.get('slot_id')!=SLOT or t.get('task_id')!=TASK or t.get('continuation_key')!=KEY: raise RuntimeError('TASK_CONTRACT_SCOPE_MISMATCH')
 e=t.get('source_evidence') or {}; a=t.get('acceptance_contract') or {}
 req={'source_url','landing_url','license_or_terms_url','content_sha256','supports_fields','relevant_record_ids_or_excerpt'}
 if req-set(e): raise RuntimeError('SOURCE_EVIDENCE_FIELDS_MISSING:'+','.join(sorted(req-set(e))))
 return e,a
def opener(landing):
 check_url(landing); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 r=urllib.request.Request(landing,headers={'User-Agent':'Mozilla/5.0 AAYS-Ofcom-R2/1.0','Accept-Language':'en-GB,en;q=0.9'})
 with op.open(r,timeout=120) as x:
  check_url(x.geturl())
  if getattr(x,'status',200)!=200: raise RuntimeError('LANDING_HTTP_STATUS:'+str(getattr(x,'status',None)))
  x.read(1024)
 return op
def download(e,dest,retries):
 urls=[e['source_url'],*(e.get('alternate_official_urls') or [])]; attempts=[]; last=''
 dest.parent.mkdir(parents=True,exist_ok=True)
 for n in range(1,retries+1):
  for url in urls:
   started=now(); tmp=dest.with_name(dest.name+'.partial.'+uuid.uuid4().hex)
   try:
    check_url(url); op=opener(e['landing_url'])
    q=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 AAYS-Ofcom-R2/1.0','Referer':e['landing_url'],'Accept':','.join(sorted(TYPES))})
    with op.open(q,timeout=600) as x,tmp.open('xb') as f:
     check_url(x.geturl()); st=getattr(x,'status',200); ct=str(x.headers.get_content_type()).lower()
     if st!=200: raise RuntimeError('DOWNLOAD_HTTP_STATUS:'+str(st))
     if ct not in TYPES: raise RuntimeError('DOWNLOAD_CONTENT_TYPE_REJECTED:'+ct)
     shutil.copyfileobj(x,f,1<<20); f.flush(); os.fsync(f.fileno())
    size=tmp.stat().st_size
    if not 30_000_000<=size<=100_000_000: raise RuntimeError('ARCHIVE_BYTES_OUT_OF_RANGE:'+str(size))
    if dest.exists():
     if sha(dest)!=sha(tmp): raise RuntimeError('ARCHIVE_TARGET_RACE_DIFFERENT_HASH')
     tmp.unlink()
    else: os.replace(tmp,dest)
    attempts.append({'attempt':n,'url':url,'state':'PASS','started_at':started,'finished_at':now()})
    return {'state':'DOWNLOADED','source_url':url,'landing_url':e['landing_url'],'http_status':st,'content_type':ct,'bytes':dest.stat().st_size,'sha256':sha(dest),'attempts':attempts}
   except Exception as ex:
    last=f'{type(ex).__name__}:{ex}'; attempts.append({'attempt':n,'url':url,'state':'FAIL','error':last,'started_at':started,'finished_at':now()})
    if tmp.exists(): tmp.unlink()
  if n<retries: time.sleep(min(8,2**n))
 raise RuntimeError('ALL_OFFICIAL_DOWNLOAD_ROUTES_FAILED:'+last)
def inspect(path,expected_files,expected_rows,production):
 if not path.is_file() or not zipfile.is_zipfile(path): raise RuntimeError('ARCHIVE_NOT_VALID_ZIP:'+str(path))
 size=path.stat().st_size
 if production and not 30_000_000<=size<=100_000_000: raise RuntimeError('ARCHIVE_BYTES_OUT_OF_RANGE:'+str(size))
 with zipfile.ZipFile(path) as z:
  bad=z.testzip()
  if bad: raise RuntimeError('ZIP_CRC_FAILURE:'+bad)
  names=[n.replace('\\','/') for n in z.namelist()]; r2=sorted(n for n in names if R2.search(n)); r1=[n for n in names if R1.search(n)]
  areas=[]; total=0; missing=[]; empty=[]; members=[]
  for name in r2:
   m=R2.search(name); area=m.group(1).upper() if m else ''; areas.append(area)
   with z.open(name) as raw:
    reader=csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig',errors='strict',newline='')); fields=list(reader.fieldnames or [])
    lookup={norm(v):v for v in fields}; miss=[k for k,v in ALIASES.items() if not any(norm(a) in lookup for a in v)]; rows=sum(1 for _ in reader)
   total+=rows; members.append({'member':name,'postcode_area':area,'rows':rows})
   if not rows: empty.append(name)
   if miss: missing.append({'file':name,'missing':miss})
  checks={'zip_crc_ok':True,'r2_file_count_ok':len(r2)==expected_files,'unique_postcode_areas_ok':len(set(areas))==expected_files,'total_rows_ok':total==expected_rows,'stale_r1_absent':not r1,'all_files_nonempty':not empty,'core_columns_complete':not missing}
  checks['all']=all(checks.values())
  return {'archive_sha256':sha(path),'archive_bytes':size,'observed_r2_files':len(r2),'observed_unique_areas':len(set(areas)),'observed_rows':total,'observed_stale_r1_files':len(r1),'empty_files':empty,'missing_columns':missing,'member_evidence':members,'checks':checks}
def outcomes(repo,e,path,dl,val,error):
 ts=now(); state='PUBLISHED_ARCHIVE_ACQUISITION_AND_STRICT_R2_ACCEPTANCE_PASS' if not error else 'BLOCKED_ARCHIVE_ACQUISITION_OR_STRICT_R2_ACCEPTANCE'; panel='PUBLISHED' if not error else 'BLOCKED'
 write(repo/READBACK,{'schema_version':1,'slot_id':SLOT,'task_id':TASK,'continuation_key':KEY,'generated_at':ts,'state':state,'source_url':e['source_url'],'landing_url':e['landing_url'],'license_or_terms_url':e['license_or_terms_url'],'archive_runtime_path':str(path),'archive_written_to_git':False,'download':dl,'error':error,'fake_data':False,'final_ready':False})
 write(repo/VALIDATION,{'schema_version':1,'slot_id':SLOT,'task_id':TASK,'continuation_key':KEY,'generated_at':ts,'state':state,'validation':val,'error':error,'official_coverage_verified_candidates':0,'parcel_measured_speed_rows':0,'fake_data':False,'final_ready':False})
 write(repo/STATUS,{'schema_version':3,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':SLOT,'task_id':TASK,'continuation_key':KEY,'updated_at':ts,'state':state,'panel_status':panel,'completed_count':5,'target_count':6,'progress_percent':83.33,'archive_acquisition_pass':bool(val and val.get('checks',{}).get('all')),'official_coverage_verified_candidates':0,'blocker':error,'fake_data':False,'final_ready':False})
 append(repo/PROGRESS,{'schema_version':1,'slot_id':SLOT,'task_id':TASK,'continuation_key':KEY,'recorded_at':ts,'completed_count':5,'target_count':6,'previous_percent':83.33,'current_percent':83.33,'percent_increase':0.0,'archive_acquisition_evidence_records':1,'candidate_rows_added':0})
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root'); ap.add_argument('--portable-root'); ap.add_argument('--archive-path'); ap.add_argument('--task-contract'); ap.add_argument('--use-existing-archive',action='store_true',help=argparse.SUPPRESS); ap.add_argument('--expected-files',type=int,help=argparse.SUPPRESS); ap.add_argument('--expected-rows',type=int,help=argparse.SUPPRESS); ap.add_argument('--retries',type=int,default=3); a=ap.parse_args()
 if os.getenv('AAYS_SLOT_ID') not in (None,'',SLOT): raise RuntimeError('WRONG_SLOT_EXECUTION_FORBIDDEN')
 if not 1<=a.retries<=4: raise RuntimeError('RETRY_COUNT_OUT_OF_RANGE')
 repo=repo_root(a.repo_root); e,c=task_contract(repo,a.task_contract); path=archive_path(a.archive_path,a.portable_root); ef=a.expected_files or int(c['expected_r2_files']); er=a.expected_rows or int(c['expected_rows']); production=ef==121 and er==1_741_096; dl=val=None
 try:
  if path.exists(): dl={'state':'CACHE_HIT','bytes':path.stat().st_size,'sha256':sha(path),'source_url':e['source_url'],'landing_url':e['landing_url']}
  elif a.use_existing_archive: raise RuntimeError('EXISTING_ARCHIVE_REQUIRED:'+str(path))
  else: dl=download(e,path,a.retries)
  val=inspect(path,ef,er,production)
  if not val['checks']['all']: raise RuntimeError('STRICT_ARCHIVE_ACCEPTANCE_FAILED:'+json.dumps(val['checks'],sort_keys=True))
  outcomes(repo,e,path,dl,val,None); print(json.dumps({'state':'PASS','slot_id':SLOT,'task_id':TASK,'archive_sha256':val['archive_sha256'],'observed_r2_files':val['observed_r2_files'],'observed_rows':val['observed_rows'],'duplicate_task_created':False,'second_runner_started':False})); return 0
 except Exception as ex:
  err=f'{type(ex).__name__}:{ex}'; outcomes(repo,e,path,dl,val,err); print(json.dumps({'state':'BLOCKED','slot_id':SLOT,'task_id':TASK,'error':err,'duplicate_task_created':False,'second_runner_started':False}),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
