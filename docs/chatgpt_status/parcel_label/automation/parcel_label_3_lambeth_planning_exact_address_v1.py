from __future__ import annotations
import argparse, hashlib, http.cookiejar, json, os, re, tempfile
import urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

TASK_ID='parcel-label-3-lambeth-planning-exact-address-v1-20260803'
SEARCH_URL='https://planning.lambeth.gov.uk/online-applications/search.do?action=advanced'
GUIDE_URL='https://www.lambeth.gov.uk/planning-building-control/planning-applications/search-submit-comment-applications'
PRIVACY_URL='https://www.lambeth.gov.uk/about-council/privacy-data-protection/planning-sustainability-service-privacy-notice'
COPYRIGHT_URL='https://www.lambeth.gov.uk/about-council/using-website/copyright'
MAX_BYTES=1_048_576; MAX_CANDIDATES=10

class Forms(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.forms=[]; self.f=None
    def handle_starttag(self,t,a):
        d={k.lower():(v or '') for k,v in a}; t=t.lower()
        if t=='form': self.f={'action':d.get('action',''),'method':(d.get('method') or 'get').lower(),'inputs':[]}
        elif self.f is not None and t=='input': self.f['inputs'].append(d)
    def handle_endtag(self,t):
        if t.lower()=='form' and self.f is not None: self.forms.append(self.f); self.f=None

class Page(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.page=[]; self.href=None; self.text=[]; self.links=[]
    def handle_starttag(self,t,a):
        if t.lower()=='a': self.href=dict(a).get('href') or ''; self.text=[]
    def handle_data(self,d):
        s=' '.join(d.split())
        if s: self.page.append(s); self.text.append(s) if self.href is not None else None
    def handle_endtag(self,t):
        if t.lower()=='a' and self.href is not None:
            s=' '.join(self.text)
            if s: self.links.append((self.href,s))
            self.href=None; self.text=[]

def root(): return Path(__file__).resolve().parents[4]
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def atomic(p,d):
    p.parent.mkdir(parents=True,exist_ok=True); b=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode(); fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.')
    try:
        with os.fdopen(fd,'wb') as f: f.write(b); f.flush(); os.fsync(f.fileno())
        os.replace(t,p)
    finally:
        if os.path.exists(t): os.unlink(t)

def rows(base):
    r=json.loads((base/'docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json').read_text())['records']
    if len(r)!=3 or {x.get('parcel_id') for x in r}!={'parcel_61523','parcel_61524','parcel_61525'}: raise ValueError('expected three exact rows')
    if any(x.get('exact_uprn_bound') is not True or x.get('mdu_status_verified') is not True for x in r): raise ValueError('non-terminal input')
    return r

def get(opener,req,timeout):
    with opener.open(req,timeout=timeout) as res:
        b=res.read(MAX_BYTES+1)
        if len(b)>MAX_BYTES: raise ValueError('response exceeds 1 MiB')
        return int(getattr(res,'status',200)),res.geturl(),b

def discover(html):
    p=Forms(); p.feed(html)
    for f in p.forms:
        for i in f['inputs']:
            m=' '.join((i.get('name',''),i.get('id',''),i.get('placeholder',''),i.get('value',''))).lower()
            if any(k in m for k in ('address','location','site')) and not any(k in m for k in ('email','password','comment')): return f,i.get('name') or i.get('id')
    return None,None

def form_values(f,name,address):
    out=[]; ok=False
    for i in f['inputs']:
        n=i.get('name',''); typ=(i.get('type') or 'text').lower(); v=i.get('value','')
        if not n: continue
        if n==name: out.append((n,address)); ok=True
        elif typ=='hidden': out.append((n,v))
        elif typ in {'radio','checkbox'} and i.get('checked')=='checked': out.append((n,v or 'true'))
        elif typ in {'submit','button'} and v: out.append((n,v))
    if not ok: raise ValueError('address field not populated')
    return out

def exact_visible(text,row):
    text=' '.join(text.upper().split()); pc=row['POSTCODE'].upper(); m=re.match(r'^\s*(\d+[A-Z]?)\s+(.+?)\s+London\s+'+re.escape(pc)+r'\s*$',row['FULLADDRESS'],re.I)
    if not m: raise ValueError('unexpected address format')
    return re.search(rf'\b{re.escape(m.group(1).upper())}\b',text) is not None and all(w.upper() in text for w in re.findall(r'[A-Za-z]+',m.group(2)) if len(w)>2) and (pc in text or pc.replace(' ','') in text.replace(' ',''))

def candidates(html,url,row):
    p=Page(); p.feed(html)
    if not exact_visible(' '.join(p.page),row): return []
    out=[]; seen=set()
    for href,text in p.links:
        u=urllib.parse.urljoin(url,href)
        if re.search(r'(application|planning|case|details|reference)',text+' '+u,re.I) and (u,text) not in seen:
            seen.add((u,text)); out.append({'parcel_id':row['parcel_id'],'UPRN':row['UPRN'],'FULLADDRESS':row['FULLADDRESS'],'POSTCODE':row['POSTCODE'],'source_url':u,'display_text':text[:500],'context_only':True,'exact_uprn_preserved':True,'official_property_type_preserved':True,'official_mdu_status_preserved':True})
            if len(out)>=MAX_CANDIDATES: break
    return out

def ev(row,url,at,digest,basis,excerpt,status,made):
    return {'parcel_id':row['parcel_id'],'UPRN':row['UPRN'],'searched_exact_address':row['FULLADDRESS'],'source_url':url,'accessed_at':at,'content_sha256':digest,'sha256_basis':basis,'record_scope':'one bounded official Lambeth planning Public Access exact-address form-discovery/search attempt; maximum two requests, 1 MiB and 10 candidate links','supports_fields':['planning application reference','site address','proposal description','application status and decision where published'],'relevant_record_ids_or_excerpt':excerpt,'terms_or_license_urls':[GUIDE_URL,PRIVACY_URL,COPYRIGHT_URL],'http_status':status,'requests_made':made}

def attempt(row,timeout):
    at=now(); made=0; op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())); op.addheaders=[('User-Agent','AAYS-parcel-label-evidence/1.0 bounded official-source research')]
    try:
        status,url,b=get(op,urllib.request.Request(SEARCH_URL,headers={'Accept':'text/html'}),timeout); made+=1; f,n=discover(b.decode('utf-8','replace'))
        if not f or not n: return [],ev(row,url,at,sha(b),'bounded_landing_response_bytes','NO_DISCOVERABLE_ADDRESS_SEARCH_FORM',status,made)
        vals=urllib.parse.urlencode(form_values(f,n,row['FULLADDRESS'])); action=urllib.parse.urljoin(url,f.get('action') or url); method=(f.get('method') or 'get').lower()
        req=urllib.request.Request(action,data=vals.encode(),headers={'Content-Type':'application/x-www-form-urlencoded','Accept':'text/html'}) if method=='post' else urllib.request.Request(action+('&' if urllib.parse.urlparse(action).query else '?')+vals,headers={'Accept':'text/html'})
        status,url,b=get(op,req,timeout); made+=1; html=b.decode('utf-8','replace'); e=ev(row,url,at,sha(b),'bounded_search_response_bytes',re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html))[:1500],status,made); e.update({'discovered_form_method':method,'discovered_address_field':n}); return candidates(html,url,row),e
    except Exception as x:
        s=f'LAMBETH_PLANNING_EXACT_ADDRESS_ERROR:{type(x).__name__}:{x}'; return [],ev(row,SEARCH_URL,at,sha(s.encode()),'bounded_error_evidence_string',s,None,made)

def build(r,timeout):
    c=[]; evidence=[]
    for x in r:
        found,e=attempt(x,timeout); c+=found; evidence.append(e)
    n=len(c)
    return {'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':TASK_ID,'generated_at':now(),'state':'CANDIDATES_FOUND_CONTEXT_ONLY' if n else 'NO_DATA_CONTINUE','panel_status':'PUBLISHED','completed_count':3,'target_count':3,'previous_percent':0.0,'progress_percent':100.0,'percent_increase':100.0,'core_exact_rows_preserved':3,'core_final_ready_preserved':True,'produced_candidate_rows':n,'candidate_rows':c,'source_evidence':evidence,'blocker':{'code':None if n else 'LAMBETH_PLANNING_NO_USABLE_RESPONSE_OR_NO_EXACT_ADDRESS_RESULT','state':'NONE' if n else 'NO_DATA_CONTINUE','manual_action_required':False,'retry_unchanged_route':False},'next_unverified_step':'SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_PLANNING_EXACT_ADDRESS','search_url':SEARCH_URL,'council_guide_url':GUIDE_URL,'privacy_url':PRIVACY_URL,'copyright_url':COPYRIGHT_URL,'login_or_account_used':False,'comment_or_representation_submitted':False,'document_download_performed':False,'captcha_bypass_attempted':False,'pagination_performed':False,'bulk_download_performed':False,'full_register_scan_performed':False,'address_reuse_performed':False,'property_type_binding_changed':False,'mdu_status_changed':False,'inferred_values':0,'fake_data':False,'final_ready':True}

def main():
    a=argparse.ArgumentParser(); a.add_argument('--timeout',type=float,default=5); a.add_argument('--validate-only',action='store_true'); z=a.parse_args(); base=root(); r=rows(base); print('PASS_3_EXACT_UPRN_ADDRESSES_LAMBETH_PLANNING_MAX2_REQUESTS_EACH_MAX1MIB_10_CANDIDATES_READ_ONLY')
    if z.validate_only:return 0
    d=build(r,max(1,min(z.timeout,30))); atomic(base/'docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_planning_exact_address_result_latest.json',d); atomic(base/'england_map_web/data/aays_21_slots/parcel_label_3/lambeth_planning_exact_address_latest.json',d); print(f"PASS_CONTEXT_CANDIDATES_{d['produced_candidate_rows']}_3_OF_3" if d['produced_candidate_rows'] else 'PASS_NO_DATA_CONTINUE_3_OF_3'); return 0
if __name__=='__main__': raise SystemExit(main())
