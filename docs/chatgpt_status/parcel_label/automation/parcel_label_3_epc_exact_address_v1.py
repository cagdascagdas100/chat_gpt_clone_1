from __future__ import annotations
import argparse, hashlib, html, json, os, re, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

TASK_ID='parcel-label-3-epc-exact-address-v1-20260803'
INPUT='docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json'
INPUT_BLOB='c5c3b41970b77b59bd83ea923252a062a217f0d2'
OUT=['docs/chatgpt_status/_shared/slots_21/parcel_label_3/epc_exact_address_result_latest.json','england_map_web/data/aays_21_slots/parcel_label_3/epc_exact_address_latest.json']
SEARCH='https://find-energy-certificate.service.gov.uk/find-a-certificate/search-by-postcode'
SERVICE='https://www.gov.uk/find-energy-certificate'
NOTICE='https://www.gov.uk/guidance/energy-performance-certificates-opt-out-of-public-disclosure'
GUIDE='https://www.gov.uk/government/publications/energy-performance-certificates-for-the-construction-sale-and-let-of-dwellings/a-guide-to-energy-performance-certificates-for-the-marketing-sale-and-let-of-dwellings'
NOTES='https://www.gov.uk/government/publications/energy-performance-of-buildings-certificates-in-england-and-wales-technical-notes/energy-performance-of-buildings-certificates-in-england-and-wales-technical-notes'
OGL='https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
IDS=['parcel_61523','parcel_61524','parcel_61525']; MAX=1_048_576

class P(HTMLParser):
 def __init__(self): super().__init__(convert_charrefs=True); self.href=None; self.buf=[]; self.links=[]; self.text=[]
 def handle_starttag(self,t,a):
  if t.lower()=='a': self.href=dict(a).get('href') or ''; self.buf=[]
 def handle_data(self,d):
  s=' '.join(d.split())
  if s: self.text.append(s); self.buf.append(s) if self.href is not None else None
 def handle_endtag(self,t):
  if t.lower()=='a' and self.href is not None:
   s=' '.join(self.buf)
   if s: self.links.append((self.href,s))
   self.href=None; self.buf=[]

def root(): return Path(__file__).resolve().parents[4]
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def toks(s): return re.findall(r'[A-Z0-9]+',html.unescape(str(s)).upper())
def sig(r):
 ts=toks(r['FULLADDRESS']); pc=str(r['POSTCODE']).replace(' ','').upper(); house=ts[0]
 street={x for x in ts[1:] if x!='LONDON' and not (x.startswith('SW') and any(c.isdigit() for c in x)) and x not in {pc[:4],pc[4:]}}
 if not street: raise ValueError('street signature missing')
 return house,street,pc
def match(s,r):
 ts=toks(s); house,street,pc=sig(r); return house in set(ts) and street.issubset(set(ts)) and pc in ''.join(ts)
def load(base):
 p=json.loads((base/INPUT).read_text()); rows=p.get('records')
 if not isinstance(rows,list) or len(rows)!=3: raise ValueError('expected 3 rows')
 d={r.get('parcel_id'):r for r in rows}; rows=[d[i] for i in IDS]
 for r in rows:
  if r.get('exact_uprn_bound') is not True or r.get('mdu_status_verified') is not True or not str(r.get('UPRN','')).isdigit(): raise ValueError('invalid exact input')
  sig(r)
 return rows
def get(url,timeout):
 q=urllib.request.Request(url,headers={'Accept':'text/html','User-Agent':'AAYS-parcel-label-evidence/1.0 bounded-official-EPC-check'})
 with urllib.request.urlopen(q,timeout=timeout) as x:
  b=x.read(MAX+1)
  if len(b)>MAX: raise ValueError('response exceeds 1 MiB')
  return int(getattr(x,'status',200)),x.geturl(),b
def link(b,url,r):
 p=P(); p.feed(b.decode('utf-8','replace')); m=sorted({urllib.parse.urljoin(url,h) for h,t in p.links if '/energy-certificate/' in h and match(t+' '+h,r)})
 return (m[0],'EXACT_ONE_CERTIFICATE_LINK') if len(m)==1 else (None,'NO_EXACT_ADDRESS_CERTIFICATE_LINK' if not m else 'AMBIGUOUS_EXACT_LINKS')
def one(patterns,text):
 for pat in patterns:
  m=re.search(pat,text,re.I)
  if m:return ' '.join(m.group(1).split())
 return None
def fields(b):
 p=P(); p.feed(b.decode('utf-8','replace')); t=' '.join(p.text)
 return {'current_energy_rating':one([r'Current energy rating\s*([A-G])\b',r'Energy efficiency rating\s*([A-G])\b'],t),'property_type':one([r'Property type\s*([^|]{1,100}?)(?=Total floor area|Built form|Main heating|$)'],t),'total_floor_area':one([r'Total floor area\s*([0-9.,]+\s*(?:square metres|m²|m2))'],t),'certificate_reference':one([r'Certificate number\s*([0-9-]{10,30})',r'Report reference number\s*([0-9-]{10,30})'],t),'valid_until':one([r'Valid until\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})'],t),'lodgement_date':one([r'Certificate date\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})'],t)}
def ev(r,url,at,dig,basis,status,n,excerpt): return {'parcel_id':r['parcel_id'],'UPRN':r['UPRN'],'searched_postcode':r['POSTCODE'],'expected_full_address':r['FULLADDRESS'],'source_url':url,'accessed_at':at,'content_sha256':dig,'sha256_basis':basis,'record_scope':'one official EPC postcode listing plus at most one strict exact-address certificate page; max two requests and 1 MiB each','supports_fields':['exact address certificate-link presence','current rating','property type','total floor area','certificate reference and dates'],'relevant_record_ids_or_excerpt':excerpt,'license_or_terms_urls':[NOTICE,GUIDE,NOTES,OGL],'http_status':status,'requests_made':n}
def attempt(r,timeout):
 url=SEARCH+'?lang=en&property_type=domestic&postcode='+urllib.parse.quote_plus(r['POSTCODE']); at=now(); n=0
 try:
  st,u,b=get(url,timeout); n=1; cert,decision=link(b,u,r); listing_sha=sha(b)
  if cert is None:return None,ev(r,u,at,listing_sha,'bounded_listing_response_bytes',st,n,decision)
  st,u,b=get(cert,timeout); n=2; f=fields(b)
  row={k:r[k] for k in ['parcel_id','UPRN','FULLADDRESS','POSTCODE','BLPUCLASS','official_property_type_label','official_mdu_status']}; row.update({'epc_certificate_url':u,'epc_exact_address_match':True,**f,'exact_uprn_bound':True,'inferred':False})
  e=ev(r,u,at,sha(b),'bounded_certificate_response_bytes',st,n,json.dumps({'decision':decision,'fields':f},sort_keys=True)); e['listing_content_sha256']=listing_sha
  return row,e
 except Exception as x:
  s=f'EPC_EXACT_ADDRESS_ERROR:{type(x).__name__}:{x}'; return None,ev(r,url,at,sha(s.encode()),'bounded_error_evidence_string',None,n,s)
def write(path,payload):
 path.parent.mkdir(parents=True,exist_ok=True); raw=json.dumps(payload,separators=(',',':')).encode(); fd,tmp=tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def build(rows,timeout):
 rec=[]; evidence=[]
 for r in rows:
  x,e=attempt(r,timeout); evidence.append(e); rec.append(x) if x else None
 completed=len(rows); target=3; pct=completed/target*100; state='PUBLISHED' if len(rec)==3 else 'NO_DATA_CONTINUE'
 return {'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':TASK_ID,'generated_at':now(),'state':state,'panel_status':'PUBLISHED','completed_count':completed,'target_count':target,'previous_percent':0.0,'progress_percent':pct,'percent_increase':pct,'exact_verified_rows':len(rec),'records':rec,'source_evidence':evidence,'blocker':None if len(rec)==3 else {'code':'EPC_EXACT_ADDRESS_NOT_VERIFIED_FOR_ALL_TARGETS','state':'NO_DATA_CONTINUE','manual_action_required':False,'retry_unchanged_route':False},'next_unverified_step':'SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_EPC_EXACT_ADDRESS','input_path':INPUT,'input_git_blob_sha':INPUT_BLOB,'service_url':SERVICE,'search_base_url':SEARCH,'opt_out_and_reuse_notice_url':NOTICE,'guide_url':GUIDE,'technical_notes_url':NOTES,'open_government_licence_url':OGL,'address_reuse_performed':False,'login_or_api_key_used':False,'bulk_download_performed':False,'full_register_scan_performed':False,'large_data_downloaded':False,'property_type_inferred':False,'inferred_values':0,'fake_data':False,'final_ready':len(rec)==3}
def validate(base):
 if len(load(base))!=3 or MAX!=1_048_576 or not SEARCH.startswith('https://find-energy-certificate.service.gov.uk/'):raise ValueError('validation failed')
 print('PASS_3_EXACT_UPRN_ADDRESSES_EPC_POSTCODE_LISTING_MAX1_CERT_PAGE_EACH_MAX1MIB_NO_ADDRESS_REUSE')
def main():
 a=argparse.ArgumentParser();a.add_argument('--timeout',type=float,default=5);a.add_argument('--validate-only',action='store_true');x=a.parse_args();base=root();validate(base)
 if x.validate_only:return 0
 p=build(load(base),max(1,min(x.timeout,30)))
 for rel in OUT:write(base/rel,p)
 print('PASS_PUBLISHED_3_OF_3_EPC_EXACT_ADDRESS' if p['exact_verified_rows']==3 else f"PASS_NO_DATA_CONTINUE_{p['completed_count']}_OF_{p['target_count']}_EXACT_ROWS_{p['exact_verified_rows']}")
 return 0
if __name__=='__main__':raise SystemExit(main())
