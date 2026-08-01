from __future__ import annotations
import argparse,hashlib,json,os,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

TASK_ID='parcel-label-3-wikipedia-geosearch-v1-20260801'; ENDPOINT='https://en.wikipedia.org/w/api.php'
PROBE='england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json'
OUTPUTS=('docs/chatgpt_status/_shared/slots_21/parcel_label_3/wikipedia_geosearch_result_latest.json','england_map_web/data/aays_21_slots/parcel_label_3/wikipedia_geosearch_latest.json')
IDS=('parcel_61523','parcel_61524','parcel_61525'); RADIUS=100; LIMIT=10; SPACING=1.2
DOC='https://www.mediawiki.org/wiki/API:Geosearch/en'; UA='https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en'; GUIDE='https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_API_Usage_Guidelines'; LICENSE='https://en.wikipedia.org/wiki/Wikipedia:Copyrights'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write_json(path,payload):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+'.part'); q.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(q,p)
def points(repo):
 rows=json.loads((repo/PROBE).read_text(encoding='utf-8-sig')).get('canonical_points')
 if not isinstance(rows,list) or len(rows)!=3: raise ValueError('CANONICAL_POINT_COUNT_NOT_3')
 out=[]
 for x in rows:
  pid=str(x.get('parcel_id'))
  if pid not in IDS or x.get('geometry_type')!='Point' or x.get('point_valid') is not True: raise ValueError('CANONICAL_POINT_INVALID')
  out.append({'parcel_id':pid,'latitude':float(x['latitude']),'longitude':float(x['longitude'])})
 out.sort(key=lambda r:IDS.index(r['parcel_id']))
 if tuple(r['parcel_id'] for r in out)!=IDS: raise ValueError('CANONICAL_POINT_IDS_MISMATCH')
 return out
def url(p):
 q={'action':'query','list':'geosearch','gscoord':f"{p['latitude']:.7f}|{p['longitude']:.7f}",'gsradius':str(RADIUS),'gslimit':str(LIMIT),'gsnamespace':'0','format':'json','formatversion':'2','origin':'*'}
 return ENDPOINT+'?'+urllib.parse.urlencode(q)
def fetch(u,t):
 a='AAYS-parcel-label-3/1.0 (bounded geosearch; https://github.com/cagdascagdas100/chat_gpt_clone_1)'
 req=urllib.request.Request(u,headers={'User-Agent':a,'Api-User-Agent':a,'Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=t) as r: return r.read(),int(r.status)
def normalize(p,data):
 rows=data.get('query',{}).get('geosearch',[]) if isinstance(data.get('query'),dict) else []; out=[]
 for x in rows[:LIMIT]:
  if not isinstance(x,dict) or any(x.get(k) in (None,'') for k in ('pageid','title','lat','lon','dist')): continue
  out.append({'parcel_id':p['parcel_id'],'canonical_point':{'latitude':p['latitude'],'longitude':p['longitude']},'wikipedia_page':{'pageid':int(x['pageid']),'title':str(x['title']),'latitude':float(x['lat']),'longitude':float(x['lon']),'distance_m':float(x['dist']),'primary':x.get('primary')},'candidate_only':True,'exact_uprn_bound':False,'property_type_bound':False,'parcel_binding_claimed':False})
 return out
def run(repo,timeout):
 attempts=[]; candidates=[]
 for i,p in enumerate(points(repo)):
  u=url(p); e={'parcel_id':p['parcel_id'],'source_url':u,'accessed_at':now(),'query_sha256':sha(u.encode()),'query_scope':{'radius_metres':RADIUS,'limit':LIMIT,'namespace':0},'http_status':None,'content_sha256':None,'sha256_basis':'raw_response_bytes','relevant_record_ids_or_excerpt':None,'proven_fields':['pageid','title','lat','lon','dist','primary'],'documentation_url':DOC,'user_agent_policy_url':UA,'api_guidelines_url':GUIDE,'license_or_terms_url':LICENSE}
  try:
   body,status=fetch(u,timeout); e['http_status']=status; e['content_sha256']=sha(body); rows=normalize(p,json.loads(body.decode())); candidates.extend(rows); e['relevant_record_ids_or_excerpt']={'returned_count':len(rows),'pageids':[r['wikipedia_page']['pageid'] for r in rows]}
  except Exception as exc:
   s=f'WIKIPEDIA_GEOSEARCH_ERROR:{type(exc).__name__}'; e['content_sha256']=sha(s.encode()); e['sha256_basis']='bounded_error_evidence_string'; e['relevant_record_ids_or_excerpt']=s
  attempts.append(e)
  if i<2: time.sleep(SPACING)
 state='PUBLISHED_CANDIDATE_ONLY' if candidates else 'NO_DATA_CONTINUE'
 blocker=None if candidates else {'code':'WIKIPEDIA_GEOSEARCH_NO_USABLE_RESPONSE','state':'NO_DATA_CONTINUE','candidate_research_blocked':False,'manual_action_required':False,'retry_unchanged_route':False}
 return {'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':TASK_ID,'generated_at':now(),'state':state,'panel_status':'PUBLISHED','completed_count':len(attempts),'target_count':3,'previous_percent':0.0,'progress_percent':round(100*len(attempts)/3,4),'percent_increase':round(100*len(attempts)/3,4),'produced_candidate_rows':len(candidates),'candidates':candidates,'source_evidence':attempts,'blocker':blocker,'next_unverified_step':'SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_WIKIPEDIA_GEOSEARCH','inferred_values':0,'fake_data':False,'final_ready':False}
def validate():
 assert len(IDS)==3 and RADIUS==100 and LIMIT==10 and SPACING>=1 and urllib.parse.urlparse(ENDPOINT).hostname=='en.wikipedia.org'
 assert all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in OUTPUTS+(PROBE,))
 return {'state':'VALIDATED','target_count':3,'expected_ids':list(IDS),'resource_class':'network_fetch','read_path':PROBE,'write_paths':list(OUTPUTS),'radius_metres':RADIUS,'result_limit':LIMIT,'minimum_request_spacing_seconds':SPACING}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root'); ap.add_argument('--timeout',type=int,default=30); ap.add_argument('--validate-only',action='store_true'); a=ap.parse_args()
 if a.validate_only: print(json.dumps(validate(),ensure_ascii=False)); return 0
 repo=Path(a.repo_root).resolve() if a.repo_root else Path(__file__).resolve().parents[4]; result=run(repo,max(1,min(a.timeout,60)))
 for rel in OUTPUTS: write_json(repo/rel,result)
 print(json.dumps({'state':result['state'],'completed_count':result['completed_count'],'target_count':3,'produced_candidate_rows':result['produced_candidate_rows']})); return 0
if __name__=='__main__': raise SystemExit(main())
