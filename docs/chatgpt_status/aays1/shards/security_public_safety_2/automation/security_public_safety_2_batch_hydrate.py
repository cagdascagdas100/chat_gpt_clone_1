from __future__ import annotations

import argparse, csv, hashlib, json, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Iterator

SLOT_ID='security_public_safety_2'; START=30762; END=31061; EXPECTED=300
TARGET={f'parcel_{n}' for n in range(START,END+1)}
BRANCH='codex/aays-single-runner-v5-20260706'; RATE_SECONDS=0.35
REPO=Path(os.environ.get('AAYS_REPO_ROOT',r'F:\chatgpt\chat_gpt_clone_1_main'))
DATA=REPO/'england_map_web'/'data'; SHARD=REPO/'docs'/'chatgpt_status'/'aays1'/'shards'/SLOT_ID
WEB=DATA/'aays_18_slots'/SLOT_ID; OUT=SHARD/'runner_outputs'
SOURCES=[DATA/'parcel_security_scores_rechecked_0_120m_spatial.geojson',DATA/'program_layer_matrix'/'security.geojson',DATA/'parcel_security_scores_compact.geojson']

def utc()->str:return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:
 d=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):d.update(c)
 return d.hexdigest()

def http_json(url:str)->dict[str,Any]:
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'AAYS-security-public-safety-slot2/3.0','Accept':'application/json','Cache-Control':'no-cache'})
  with urllib.request.urlopen(req,timeout=60) as r:
   b=r.read(); return {'url':url,'http_status':int(r.status),'sha256':sha_bytes(b),'json':json.loads(b.decode()),'error':None}
 except Exception as e:return {'url':url,'http_status':None,'sha256':None,'json':None,'error':f'{type(e).__name__}:{e}'}

def stream_features(path:Path,chunk:int=1<<20)->Iterator[dict[str,Any]]:
 dec=json.JSONDecoder()
 with path.open('r',encoding='utf-8-sig') as f:
  buf=''; started=False; eof=False
  while True:
   if not eof and (not started or len(buf)<chunk//2):
    s=f.read(chunk); buf+=s; eof=not bool(s)
   if not started:
    i=buf.find('"features"')
    if i<0:
     if eof:raise ValueError('FEATURES_NOT_FOUND')
     buf=buf[-64:];continue
    j=buf.find('[',i)
    if j<0:
     if eof:raise ValueError('FEATURES_OPEN_NOT_FOUND')
     buf=buf[i:];continue
    buf=buf[j+1:];started=True
   buf=buf.lstrip()
   if not buf:
    if eof:raise ValueError('UNEXPECTED_EOF')
    continue
   if buf[0]==']':return
   if buf[0]==',':buf=buf[1:];continue
   try:item,end=dec.raw_decode(buf)
   except json.JSONDecodeError:
    if eof:raise
    s=f.read(chunk);buf+=s;eof=not bool(s);continue
   buf=buf[end:]
   if isinstance(item,dict):yield item

def pid(feature:dict[str,Any])->str:
 p=feature.get('properties') or {};return str(p.get('security_parcel_id') or p.get('parcel_id') or '')

def find_rows()->tuple[Path|None,dict[str,dict[str,Any]]]:
 paths=[p for p in SOURCES if p.is_file()]
 paths+=sorted((p for p in DATA.rglob('*') if p.is_file() and p.suffix.lower() in {'.json','.geojson'} and p not in paths),key=lambda p:p.stat().st_size,reverse=True)
 for path in paths:
  found={}
  try:
   for f in stream_features(path):
    x=pid(f)
    if x in TARGET:found[x]=f
    if len(found)==EXPECTED:return path,found
  except Exception:continue
 return None,{}

def iod_lookup(path:Path|None)->tuple[dict[str,dict[str,str]],dict[str,Any]]:
 if not path or not path.is_file():return {},{'status':'NOT_AVAILABLE','path':str(path) if path else None}
 with path.open('r',encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f); names={x.lower().strip():x for x in r.fieldnames or []}
  code=names.get('lsoa code (2021)') or names.get('lsoa_code'); score=names.get('crime score') or names.get('crime_score')
  rank=names.get('crime rank (where 1 is most deprived)') or names.get('crime rank') or names.get('crime_rank')
  decile=names.get('crime decile (where 1 is most deprived 10% of lsoas)') or names.get('crime decile') or names.get('crime_decile')
  if not code or not score:return {},{'status':'INVALID_COLUMNS','fieldnames':r.fieldnames}
  out={row.get(code,'').strip():{'iod25_crime_score':row.get(score),'iod25_crime_rank':row.get(rank) if rank else None,'iod25_crime_decile':row.get(decile) if decile else None} for row in r if row.get(code,'').strip()}
 return out,{'status':'LOADED','path':str(path),'sha256':sha_file(path),'rows':len(out),'corrected_v2_required':True}

def contract()->dict[str,Any]:
 slot=os.environ.get('AAYS_SLOT_ID',SLOT_ID); branch=os.environ.get('AAYS_TARGET_BRANCH',BRANCH)
 shared=REPO/'docs'/'chatgpt_status'/'_shared'/'slots_18'/SLOT_ID
 failures=[]
 if slot!=SLOT_ID:failures.append(f'WRONG_SLOT:{slot}')
 if branch!=BRANCH:failures.append(f'WRONG_BRANCH:{branch}')
 for n in ['current_task_latest.json','status_latest.json','ownership_latest.json']:
  if not (shared/n).is_file():failures.append(f'MISSING:{shared/n}')
 return {'pass':not failures,'failures':failures,'shared_root':str(shared),'web_root':str(WEB)}

def build(features:dict[str,dict[str,Any]],month:str|None,iod:dict[str,dict[str,str]],skip_api:bool)->list[dict[str,Any]]:
 rows=[]
 for n in range(START,END+1):
  x=f'parcel_{n}';f=features.get(x)
  if not f:
   rows.append({'parcel_id':x,'candidate_status':'CANONICAL_FEATURE_NOT_FOUND','accuracy_score_4':0,'needs_manual_review':True,'output_semantics':'NO_DATA'});continue
  p=f.get('properties') or {};g=f.get('geometry') or {};coord=g.get('coordinates') if g.get('type')=='Point' else None
  lsoa=p.get('security_lsoa_code') or p.get('lsoa_code'); row={'parcel_id':x,'row_no':p.get('row_no'),'hmlr_inspire_id':p.get('hmlr_inspire_id'),'london_authority':p.get('london_authority'),'lsoa_code':lsoa,'lsoa_name':p.get('security_lsoa_name') or p.get('lsoa_name'),'geometry':g,'candidate_status':'CANONICAL_FOUND_API_PENDING','accuracy_score_4':2,'needs_manual_review':True,'output_semantics':'AREA_LEVEL_PROXY','parcel_measurement':False}
  if lsoa and lsoa in iod:row.update(iod[lsoa])
  if coord and month and not skip_api:
   url='https://data.police.uk/api/crimes-street/all-crime?'+urllib.parse.urlencode({'date':month,'lat':coord[1],'lng':coord[0]});live=http_json(url);cr=live.get('json');ok=live.get('http_status')==200 and isinstance(cr,list)
   row.update({'official_api_url':url,'official_api_http_status':live.get('http_status'),'official_api_sha256':live.get('sha256'),'official_api_one_mile_supporting_count':len(cr) if isinstance(cr,list) else None,'official_api_semantics':'ANONYMISED_APPROXIMATE_SUPPORTING_EVIDENCE_NOT_EXACT_PARCEL_COUNT','official_api_error':live.get('error')})
   row['accuracy_score_4']=4 if ok and lsoa in iod else (3 if ok else 2);row['candidate_status']='CANONICAL_API_IOD25_V2_VERIFIED' if row['accuracy_score_4']==4 else ('CANONICAL_API_VERIFIED_IOD25_V2_PENDING' if ok else 'CANONICAL_API_FAILED');time.sleep(RATE_SECONDS)
  rows.append(row)
 return rows

def write_csv(path:Path,rows:list[dict[str,Any]])->None:
 keys=sorted({k for r in rows for k in r if k!='geometry'});path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)

def html(payload:dict[str,Any])->str:
 tr=''.join(f"<tr><td>{i}</td><td>{escape(str(r['parcel_id']))}</td><td>{escape(str(r['candidate_status']))}</td><td>{r['accuracy_score_4']}</td><td>{escape(str(r.get('lsoa_code') or 'not_available'))}</td><td>{escape(str(r.get('official_api_http_status') or 'not_available'))}</td><td>{escape(str(r.get('official_api_one_mile_supporting_count') or 'not_available'))}</td></tr>" for i,r in enumerate(payload['rows'],1))
 return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="15"><title>Security/Public Safety Slot 2</title><style>body{{font-family:Segoe UI,Arial,sans-serif;margin:20px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:6px}}</style></head><body data-slot-id="{SLOT_ID}" data-visible-row-count="{len(payload['rows'])}" data-final-ready="false"><h1>Security / Public Safety — Slot 2</h1><p>Gerçek canonical={payload['canonical_rows']}/300; doğruluk ≥3={payload['accuracy_ge_3_count']}; 4/4={payload['accuracy_4_count']}; promoted=0.</p><table><thead><tr><th>#</th><th>Parsel</th><th>Durum</th><th>/4</th><th>LSOA</th><th>HTTP</th><th>1 mil destek</th></tr></thead><tbody>{tr}</tbody></table><p>AREA_LEVEL_PROXY; exact parsel suçu değildir. final_ready=false.</p></body></html>'''

def run(a:argparse.Namespace)->dict[str,Any]:
 c=contract()
 if not c['pass']:raise RuntimeError(';'.join(c['failures']))
 source,features=find_rows();latest={'http_status':200,'sha256':'TEST','json':{'date':a.test_month}} if a.test_month else http_json('https://data.police.uk/api/crime-last-updated');month=str((latest.get('json') or {}).get('date') or '')[:7] or None
 iod,iod_meta=iod_lookup(Path(a.iod25_csv) if a.iod25_csv else None);rows=build(features,month,iod,a.skip_api)
 canonical=sum(r['candidate_status']!='CANONICAL_FEATURE_NOT_FOUND' for r in rows);ge3=sum(int(r.get('accuracy_score_4') or 0)>=3 for r in rows);four=sum(int(r.get('accuracy_score_4') or 0)==4 for r in rows)
 payload={'schema_version':3,'slot_id':SLOT_ID,'generated_at':utc(),'hydrate_partition':{'start':START,'end':END,'count':EXPECTED},'source_file':str(source) if source else None,'source_file_sha256':sha_file(source) if source else None,'official_api_latest':{k:v for k,v in latest.items() if k!='json'}|{'month':month},'iod25':iod_meta,'rows':rows,'canonical_rows':canonical,'accuracy_ge_3_count':ge3,'accuracy_4_count':four,'promoted_business_rows':0,'actual_business_rows_written':0,'output_semantics':'AREA_LEVEL_PROXY','fake_data':False,'final_ready':False}
 OUT.mkdir(parents=True,exist_ok=True);WEB.mkdir(parents=True,exist_ok=True);jp=OUT/'security_public_safety_2_hydrated_300_latest.json';cp=OUT/'security_public_safety_2_hydrated_300_latest.csv';gp=OUT/'security_public_safety_2_hydrated_300_latest.geojson';wp=WEB/'hydrated_300_latest.json';hp=WEB/'progress.html'
 jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');write_csv(cp,rows);gp.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':r.get('geometry'),'properties':{k:v for k,v in r.items() if k!='geometry'}} for r in rows]},ensure_ascii=False,separators=(',',':'))+'\n');wp.write_text(jp.read_text());hp.write_text(html(payload))
 csv_rows=sum(1 for _ in cp.open())-1;geo_rows=len(json.loads(gp.read_text())['features']);payload['artifacts']={'json_sha256':sha_file(jp),'csv_sha256':sha_file(cp),'geojson_sha256':sha_file(gp),'html_sha256':sha_file(hp),'parity_pass':csv_rows==geo_rows==len(rows)==EXPECTED};jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');wp.write_text(jp.read_text());return payload

def args()->argparse.Namespace:
 p=argparse.ArgumentParser();p.add_argument('--iod25-csv');p.add_argument('--skip-api',action='store_true');p.add_argument('--test-month');return p.parse_args()
if __name__=='__main__':
 r=run(args());print(json.dumps({'slot_id':SLOT_ID,'canonical_rows':r['canonical_rows'],'accuracy_ge_3_count':r['accuracy_ge_3_count'],'accuracy_4_count':r['accuracy_4_count'],'parity_pass':r['artifacts']['parity_pass'],'final_ready':False}))
