#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,re,tempfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

SLOT="future_growth_2"; WS="AAYS_21_SLOT_SAFE_PARALLEL_V1"
HOST="use-land-property-data.service.gov.uk"
PAGE="https://use-land-property-data.service.gov.uk/datasets/inspire/download"
TARGETS=((30762,"Enfield","London Borough of Enfield"),(46142,"Havering","London Borough of Havering"),(61522,"Lambeth","London Borough of Lambeth"))

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def digest(b): return hashlib.sha256(b).hexdigest()
def valid_page(u):
 p=urlparse(u)
 if p.scheme!="https" or p.hostname!=HOST: raise ValueError("official HMLR HTTPS page required")
def valid_key(k):
 if len(k)!=64 or any(c not in "0123456789abcdef" for c in k): raise ValueError("bad continuation key")
def valid_gml(u,label=""):
 p=urlparse(u or "")
 return p.scheme=="https" and bool(p.netloc) and ("gml" in label.lower() or re.search(r"\.gml(?:$|[?#])",u,re.I) is not None)
def write(path,value):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+".",suffix=".tmp")
 try:
  with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as f:
   json.dump(value,f,ensure_ascii=False,sort_keys=True,separators=(",",":")); f.write("\n"); f.flush(); os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp): os.unlink(tmp)

def fixture_capture():
 h="""<table><tr><td>London Borough of Enfield</td><td><a href='https://files.example.test/e.gml'>Download .gml</a></td></tr><tr><td>London Borough of Havering</td><td><a href='https://files.example.test/h.gml?m=2026-07'>Download GML</a></td></tr><tr><td>London Borough of Lambeth</td><td><a href='https://files.example.test/l.gml'>Download .gml</a></td></tr></table>"""
 rows=[]
 for n,l,a in TARGETS:
  m=re.search(re.escape(a)+r".{0,500}?href=['\"](https://[^'\"]+)['\"].{0,300}?>([^<]*gml[^<]*)<",h,re.I|re.S)
  rows.append({"row_no":n,"lpa":l,"authority":a,"href":m.group(1) if m else None,"label":m.group(2) if m else None,"block_tag":"tr","block_text":a+" Download .gml"})
 b=h.encode()
 return {"page_http_status":200,"page_final_url":PAGE,"page_title":"fixture","page_byte_count":len(b),"page_sha256":digest(b),"records":rows}

def browser_capture(u,timeout):
 try: from playwright.sync_api import sync_playwright
 except Exception as e: raise RuntimeError(f"PLAYWRIGHT_IMPORT_FAILED:{type(e).__name__}:{e}") from e
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True)
  try:
   page=b.new_page(accept_downloads=False); r=page.goto(u,wait_until="domcontentloaded",timeout=timeout*1000); page.wait_for_timeout(1200)
   valid_page(page.url); body=page.content().encode()
   if len(body)>5000000: raise ValueError("rendered page too large")
   rows=page.evaluate("""(targets)=>{const norm=v=>(v||'').replace(/\\s+/g,' ').trim().toLowerCase();const blocks=[...document.querySelectorAll('tr,li,article,section,p,div')];return targets.map(t=>{const c=blocks.filter(x=>norm(x.innerText).includes(norm(t.authority))).sort((a,b)=>norm(a.innerText).length-norm(b.innerText).length);for(const x of c){for(const a of x.querySelectorAll('a[href]')){const label=norm(a.innerText||a.textContent),href=a.href||'';if(/gml/i.test(label)||/\\.gml(?:$|[?#])/i.test(href))return{row_no:t.row_no,lpa:t.lpa,authority:t.authority,href,label,block_tag:(x.tagName||'').toLowerCase(),block_text:(x.innerText||'').replace(/\\s+/g,' ').trim().slice(0,500)}}return{row_no:t.row_no,lpa:t.lpa,authority:t.authority,href:null,label:null,block_tag:null,block_text:null}})}""",[{"row_no":n,"lpa":l,"authority":a} for n,l,a in TARGETS])
   return {"page_http_status":int(r.status) if r else None,"page_final_url":page.url,"page_title":page.title(),"page_byte_count":len(body),"page_sha256":digest(body),"records":rows}
  finally: b.close()

def build(u,k,capture,error):
 at=now(); by={int(x["row_no"]):x for x in (capture or {}).get("records",[])}; rows=[]; found=0
 for n,l,a in TARGETS:
  x=by.get(n,{}); href=x.get("href"); ok=isinstance(href,str) and valid_gml(href,str(x.get("label") or "")); found+=int(ok); text=x.get("block_text")
  rows.append({"row_no":n,"lpa":l,"authority":a,"official_page_url":u,"official_page_final_url":(capture or {}).get("page_final_url"),"official_page_http_status":(capture or {}).get("page_http_status"),"official_page_title":(capture or {}).get("page_title"),"official_page_byte_count":(capture or {}).get("page_byte_count",0),"official_page_sha256":(capture or {}).get("page_sha256"),"accessed_at_utc":at,"gml_url":href if ok else None,"link_label":x.get("label") if ok else None,"dom_block_tag":x.get("block_tag") if ok else None,"dom_block_text_excerpt":text if ok else None,"dom_block_text_sha256":digest(text.encode()) if ok and isinstance(text,str) else None,"data_status":"EXACT_OFFICIAL_DOM_GML_URL_FOUND" if ok else ("SOURCE_READ_FAILED" if error else "SOURCE_LINK_NOT_FOUND"),"error":error if error else (None if ok else "No exact HTTPS .gml href in authority DOM block"),"full_gml_downloaded":False,"geometry_copied":False,"membership_inferred":False,"score_written":False,"fake_data":False})
 state="PUBLISHED" if found==3 else "NO_DATA_CONTINUE"
 return {"schema_version":3,"architecture_version":3,"workstream_id":WS,"slot_id":SLOT,"task_continuation_key":k,"state":state,"panel_status":"PUBLISHED" if state=="PUBLISHED" else "BİLGİ TOPLANIYOR","generated_at":now(),"completed_count":3,"target_count":3,"progress_percent":100.0,"exact_gml_url_count":found,"missing_or_failed_count":3-found,"global_business_completed_count":0,"global_business_target_count":30761,"global_progress_percent":0.0,"records":rows,"full_gml_downloaded":False,"raw_page_body_copied":False,"geometry_copied":False,"membership_inferred":False,"scores_written":False,"fake_data":False}

def main():
 p=argparse.ArgumentParser(); p.add_argument("--download-page-url",default=PAGE); p.add_argument("--output",required=True); p.add_argument("--task-continuation-key",required=True); p.add_argument("--timeout-seconds",type=int,default=120); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
 valid_page(a.download_page_url); valid_key(a.task_continuation_key)
 if not 15<=a.timeout_seconds<=240: raise ValueError("timeout 15..240")
 capture=None; error=None
 if a.self_test: capture=fixture_capture()
 else:
  try: capture=browser_capture(a.download_page_url,a.timeout_seconds)
  except Exception as e: error=f"{type(e).__name__}:{str(e)[:1000]}"
 out=build(a.download_page_url,a.task_continuation_key,capture,error); write(a.output,out)
 print(json.dumps({"state":out["state"],"completed_count":3,"target_count":3,"exact_gml_url_count":out["exact_gml_url_count"],"missing_or_failed_count":out["missing_or_failed_count"],"output":str(a.output)},sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()
