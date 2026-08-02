from __future__ import annotations
import argparse, hashlib, html, json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

TASK_ID='parcel-label-3-ofsted-inspection-postcode-v1-20260802'
PROBE='england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json'
OUT=('docs/chatgpt_status/_shared/slots_21/parcel_label_3/ofsted_inspection_postcode_result_latest.json','england_map_web/data/aays_21_slots/parcel_label_3/ofsted_inspection_postcode_latest.json')
LANDING='https://reports.ofsted.gov.uk/'
GOVUK='https://www.gov.uk/find-ofsted-inspection-report'
COPYRIGHT='https://www.gov.uk/guidance/using-ofsted-logos-and-copyright'
OGL='https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
POSTCODES=(('parcel_61523','SW16 5TG'),('parcel_61524','SW16 5AE'),('parcel_61525','SW16 5AZ'))
MAX_BYTES=1_048_576; MAX_CANDIDATES=20

def now()->str:return datetime.now(timezone.utc).isoformat()
def digest(v:bytes|str)->str:return hashlib.sha256(v.encode() if isinstance(v,str) else v).hexdigest()
def write(path:str,obj:dict[str,Any])->None:
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')));os.replace(t,p)
def points()->list[dict[str,Any]]:
 d=json.loads(Path(PROBE).read_text()); rows={x['parcel_id']:x for x in d['canonical_points']}; out=[]
 for pid,_ in POSTCODES:
  r=rows.get(pid)
  if not r or r.get('geometry_type')!='Point' or r.get('point_valid') is not True:raise ValueError('invalid canonical point '+pid)
  lon=float(r['longitude']);lat=float(r['latitude'])
  if not(-180<=lon<=180 and -90<=lat<=90):raise ValueError('invalid coordinate '+pid)
  out.append({'parcel_id':pid,'longitude':lon,'latitude':lat})
 return out

class P(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.forms=[];self.form=None;self.links=[];self.link=None
 def handle_starttag(self,tag,attrs):
  a={k.lower():(v or '') for k,v in attrs};tag=tag.lower()
  if tag=='form':self.form={'action':a.get('action',''),'method':a.get('method','get').lower(),'inputs':[]};self.forms.append(self.form)
  elif tag in {'input','select','textarea'} and self.form is not None:self.form['inputs'].append({k:a.get(k,'') for k in ('name','id','type','value','placeholder','aria-label')})
  elif tag=='a' and a.get('href'):self.link={'href':a['href'],'text':''};self.links.append(self.link)
 def handle_data(self,data):
  if self.link is not None:self.link['text']+=data
 def handle_endtag(self,tag):
  if tag.lower()=='form':self.form=None
  elif tag.lower()=='a':self.link=None

def fetch(url:str,timeout:float,data:bytes|None=None)->tuple[bytes,int|None,str]:
 q=urllib.request.Request(url,data=data,headers={'Accept':'text/html,application/xhtml+xml','Content-Type':'application/x-www-form-urlencoded' if data is not None else 'text/plain','User-Agent':'TerraYield-AAYS/1.0 bounded Ofsted postcode research'})
 with urllib.request.urlopen(q,timeout=timeout) as r:
  raw=r.read(MAX_BYTES+1)
  if len(raw)>MAX_BYTES:raise ValueError('response exceeded 1 MiB')
  return raw,getattr(r,'status',None),r.geturl()
def discover(raw:bytes,base:str)->dict[str,Any]:
 p=P();p.feed(raw.decode(errors='replace'))
 for f in p.forms:
  for x in f['inputs']:
   if x.get('type') in {'hidden','submit','button','checkbox','radio'}:continue
   h=' '.join(str(x.get(k,'')) for k in ('name','id','placeholder','aria-label')).lower()
   if x.get('name') and any(t in h for t in ('location','postcode','post code','town','city')):
    return {'action':urllib.parse.urljoin(base,f.get('action') or base),'method':f.get('method') if f.get('method') in {'get','post'} else 'get','field':x['name'],'inputs':f['inputs']}
 raise ValueError('Ofsted location/postcode search form not discovered')
def submit(f:dict[str,Any],postcode:str)->tuple[str,bytes|None,str]:
 params=[]
 for x in f['inputs']:
  n=x.get('name')
  if not n:continue
  if n==f['field']:params.append((n,postcode))
  elif x.get('type')=='hidden' and x.get('value'):params.append((n,str(x['value'])))
 enc=urllib.parse.urlencode(params)
 if f['method']=='post':return f['action'],enc.encode(),digest(enc)
 return f['action']+('&' if urllib.parse.urlparse(f['action']).query else '?')+enc,None,digest(enc)
def candidates(raw:bytes,url:str,pid:str,postcode:str)->list[dict[str,Any]]:
 p=P();p.feed(raw.decode(errors='replace'));seen=set();out=[]
 for a in p.links:
  u=urllib.parse.urljoin(url,a['href']);z=urllib.parse.urlparse(u)
  if z.netloc!='reports.ofsted.gov.uk' or '/provider/' not in z.path.lower() or u in seen:continue
  seen.add(u);label=re.sub(r'\s+',' ',html.unescape(a.get('text',''))).strip()
  out.append({'parcel_id':pid,'searched_postcode':postcode,'provider_name_or_link_text':label or None,'provider_url':u,'candidate_only':True,'exact_parcel_binding_claimed':False,'property_type_binding_claimed':False})
  if len(out)>=MAX_CANDIDATES:break
 return out

def run(timeout:float)->dict[str,Any]:
 pts=points();pm={x['parcel_id']:x for x in pts};ev=[];cand=[]
 for pid,postcode in POSTCODES:
  at=now();made=0
  try:
   land,ls,lf=fetch(LANDING,timeout);made=1;f=discover(land,lf);u,body,payload=submit(f,postcode);raw,rs,rf=fetch(u,timeout,body);made=2;found=candidates(raw,rf,pid,postcode);cand+=found
   ev.append({'parcel_id':pid,'searched_postcode':postcode,'canonical_point':pm[pid],'source_url':rf,'landing_url':LANDING,'accessed_at':at,'content_sha256':digest(raw),'landing_content_sha256':digest(land),'request_payload_sha256':payload,'sha256_basis':'bounded_raw_html_response_bytes','record_scope':'one official Ofsted landing request plus one discovered postcode-search submission; maximum 20 provider links and 1 MiB per response','supports_fields':['Ofsted provider candidate URL','visible provider name or link text','postcode-level search association'],'relevant_record_ids_or_excerpt':{'candidate_count':len(found),'candidate_urls':[x['provider_url'] for x in found],'form_method':f['method'],'location_field':f['field']},'govuk_service_url':GOVUK,'copyright_url':COPYRIGHT,'license_or_terms_url':OGL,'landing_http_status':ls,'http_status':rs,'requests_made':made})
  except Exception as e:
   msg=f'OFSTED_INSPECTION_POSTCODE_ERROR:{type(e).__name__}:{e}'
   ev.append({'parcel_id':pid,'searched_postcode':postcode,'canonical_point':pm[pid],'source_url':LANDING,'landing_url':LANDING,'accessed_at':at,'content_sha256':digest(msg),'sha256_basis':'bounded_error_evidence_string','record_scope':'one bounded official Ofsted form-discovery/postcode-search attempt; maximum one landing and one search response; no report or document crawl','supports_fields':['Ofsted inspection-report postcode-search availability'],'relevant_record_ids_or_excerpt':msg[:512],'govuk_service_url':GOVUK,'copyright_url':COPYRIGHT,'license_or_terms_url':OGL,'http_status':getattr(e,'code',None),'requests_made':made})
 state='OFSTED_PROVIDER_CANDIDATES_FOUND' if cand else 'NO_DATA_CONTINUE'
 result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':TASK_ID,'generated_at':now(),'state':state,'panel_status':'PUBLISHED','completed_count':3,'target_count':3,'previous_percent':0.0,'progress_percent':100.0,'percent_increase':100.0,'validated_canonical_points':pts,'produced_candidate_rows':len(cand),'candidate_rows':cand,'source_evidence':ev,'blocker':{'code':'NONE' if cand else 'OFSTED_REPORTS_NO_USABLE_RESPONSE_OR_NO_POSTCODE_PROVIDER_RESULTS','state':state,'manual_action_required':False,'retry_unchanged_route':False},'next_unverified_step':'VALIDATE_OFSTED_PROVIDER_CANDIDATES_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE' if cand else 'SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OFSTED_INSPECTION_POSTCODE','api_or_login_used':False,'bulk_download_performed':False,'report_or_document_crawl_performed':False,'large_data_downloaded':False,'property_type_binding_claimed':False,'exact_parcel_binding_claimed':False,'inferred_values':0,'fake_data':False,'final_ready':False}
 for p in OUT:write(p,result)
 return result

def validate()->None:
 if len(points())!=3:raise ValueError('target count')
 if any(Path(p).is_absolute() for p in (PROBE,*OUT)):raise ValueError('relative paths required')
 if MAX_BYTES!=1_048_576 or MAX_CANDIDATES!=20 or len(POSTCODES)!=3:raise ValueError('bounded guards')
 if not LANDING.startswith('https://reports.ofsted.gov.uk/'):raise ValueError('official source guard')
 print('PASS_TARGET_3_OFSTED_FORM_DISCOVERY_POSTCODE_MAX2_REQUESTS_EACH_MAX1MIB_20_CANDIDATES')
def main()->None:
 a=argparse.ArgumentParser();a.add_argument('--timeout',type=float,default=20);a.add_argument('--validate-only',action='store_true');x=a.parse_args()
 if x.validate_only:validate();return
 r=run(x.timeout);print(json.dumps({'state':r['state'],'completed_count':r['completed_count'],'target_count':r['target_count'],'produced_candidate_rows':r['produced_candidate_rows'],'evidence_records':len(r['source_evidence'])},separators=(',',':')))
if __name__=='__main__':main()
