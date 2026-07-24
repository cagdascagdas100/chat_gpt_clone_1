#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin
import requests

SLOT_ID='future_growth_1'
DEFAULT_PAGE='https://use-land-property-data.service.gov.uk/datasets/inspire/download'
MAX_DOWNLOAD_BYTES=1_500_000_000
MAX_EXTRACTED_BYTES=2_000_000_000

class RowAnchorParser(HTMLParser):
    def __init__(self)->None:
        super().__init__(); self.depth=0; self.context=[]; self.href=None; self.anchor=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in {'tr','li'}:
            self.depth+=1
            if self.depth==1: self.context=[]
        if tag=='a': self.href=dict(attrs).get('href'); self.anchor=[]
    def handle_data(self,data):
        if self.depth: self.context.append(data)
        if self.href is not None: self.anchor.append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.href is not None:
            self.links.append((' '.join(self.context).strip(),' '.join(self.anchor).strip(),self.href)); self.href=None; self.anchor=[]
        if tag in {'tr','li'} and self.depth: self.depth-=1

def normal(value:Any)->str:
    return ' '.join(re.sub(r'[^a-z0-9]+',' ',str(value or '').casefold()).split())
def slug(value:str)->str:
    return re.sub(r'[^a-z0-9]+','-',value.casefold()).strip('-') or 'authority'
def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()
def write_json(path:Path,payload:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load_candidates(path:Path)->list[dict[str,Any]]:
    payload=json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(payload,dict) or payload.get('slot_id') not in {None,SLOT_ID}: raise ValueError('starter manifest slot_id mismatch')
    rows=payload.get('candidates')
    if not isinstance(rows,list) or not rows: raise ValueError('starter manifest must contain candidates')
    required={'hmlr_inspire_id','local_authority_name'}
    if any(not required.issubset(row) for row in rows if isinstance(row,dict)): raise ValueError('candidate identity fields missing')
    return [dict(row) for row in rows]
def resolve(page_html:str,page_url:str,authorities:list[str]):
    parser=RowAnchorParser(); parser.feed(page_html); records=[]; blocked=[]
    for authority in authorities:
        target=normal(authority); matches=[]
        for context,anchor,href in parser.links:
            if not href: continue
            ctx=normal(context); label=normal(anchor); stem=normal(Path(href.split('?',1)[0]).stem)
            exact_context = ctx==target or ctx.startswith(target+' ') or (' '+target+' ') in (' '+ctx+' ')
            exact_file = stem==target or stem.startswith(target+' ')
            is_download = label in {'download gml','download'} or href.lower().split('?',1)[0].endswith(('.gml','.zip'))
            if is_download and (exact_context or exact_file): matches.append({'context':context,'anchor_text':anchor,'url':urljoin(page_url,href)})
        matches=list({m['url']:m for m in matches}.values())
        if len(matches)!=1: blocked.append({'authority':authority,'status':'NO_UNIQUE_EXACT_DOWNLOAD_LINK','matches':matches})
        else: records.append({'authority':authority,'normalized_authority':target,'download_link':matches[0]})
    return records,blocked
def download(session:requests.Session,url:str,target:Path,timeout:int):
    target.parent.mkdir(parents=True,exist_ok=True); total=0; h=hashlib.sha256()
    with session.get(url,timeout=timeout,stream=True,allow_redirects=True) as response:
        response.raise_for_status(); declared=response.headers.get('content-length')
        if declared and int(declared)>MAX_DOWNLOAD_BYTES: raise ValueError('download exceeds declared safety limit')
        content_type=response.headers.get('content-type','')
        with target.open('wb') as out:
            for chunk in response.iter_content(1<<20):
                if not chunk: continue
                total+=len(chunk)
                if total>MAX_DOWNLOAD_BYTES: raise ValueError('download exceeds streamed safety limit')
                out.write(chunk); h.update(chunk)
        resolved=response.url
    if total==0: raise ValueError('empty HMLR download')
    return {'resolved_url':resolved,'content_type':content_type,'size_bytes':total,'raw_sha256':h.hexdigest()}
def extract(raw:Path,output_dir:Path):
    head=raw.read_bytes()[:1024].lstrip().lower()
    if head.startswith(b'<html') or b'<!doctype html' in head: raise ValueError('HMLR returned HTML')
    output_dir.mkdir(parents=True,exist_ok=True)
    if not zipfile.is_zipfile(raw):
        dest=output_dir/'source.gml'; raw.replace(dest); return [dest]
    total=0; paths=[]
    with zipfile.ZipFile(raw) as z:
        for info in z.infolist():
            p=Path(info.filename)
            if info.is_dir() or p.suffix.lower() not in {'.gml','.xml'}: continue
            if p.is_absolute() or '..' in p.parts: raise ValueError('unsafe archive path')
            total+=info.file_size
            if total>MAX_EXTRACTED_BYTES: raise ValueError('extracted size limit exceeded')
            dest=output_dir/p.name
            with z.open(info) as src,dest.open('wb') as out:
                while chunk:=src.read(1<<20): out.write(chunk)
            paths.append(dest)
    if not paths: raise ValueError('archive contains no GML/XML')
    return paths

def main(argv:Iterable[str]|None=None)->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--starter-manifest',type=Path,required=True); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--download-page',default=DEFAULT_PAGE); ap.add_argument('--timeout',type=int,default=90); ap.add_argument('--resolve-only',action='store_true'); ap.add_argument('--page-html',type=Path); args=ap.parse_args(argv)
    try:
        rows=load_candidates(args.starter_manifest); authorities=sorted({str(r['local_authority_name']).strip() for r in rows})
        session=requests.Session(); session.headers.update({'User-Agent':'AAYS-TerraYield/future_growth_1-hmlr-resolver-v1','Accept':'text/html,application/gml+xml,application/xml,application/zip,*/*'})
        if args.page_html: page_body=args.page_html.read_bytes(); resolved_page=args.download_page
        else:
            response=session.get(args.download_page,timeout=args.timeout,allow_redirects=True); response.raise_for_status(); page_body=response.content; resolved_page=response.url
        records,blocked=resolve(page_body.decode('utf-8',errors='replace'),resolved_page,authorities); vectors=[]
        if not args.resolve_only:
            for record in records:
                root=args.output_dir/'hmlr'/slug(record['authority']); raw=root/'source_download'; meta=download(session,record['download_link']['url'],raw,args.timeout); paths=extract(raw,root/'extracted'); record.update(meta); record['vectors']=[{'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha256(p)} for p in paths]; vectors.extend(str(p) for p in paths)
        ready=len(records)==len(authorities) and not blocked
        status='READY_HMLR_URLS_RESOLVED' if args.resolve_only and ready else ('READY_HMLR_GML_DOWNLOADED' if ready else 'BLOCKED_HMLR_SOURCE_PREPARATION')
        payload={'schema_version':2,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':SLOT_ID,'status':status,'download_page':args.download_page,'download_page_resolved_url':resolved_page,'download_page_sha256':hashlib.sha256(page_body).hexdigest(),'candidate_count':len(rows),'authority_count':len(authorities),'prepared_authority_count':len(records),'resolve_only':args.resolve_only,'records':records,'blocked':blocked,'vector_paths':vectors,'exact_authority_match_required':True,'nearest_or_fuzzy_authority_match_used':False,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}; code=0 if ready else 2
    except Exception as exc:
        payload={'schema_version':2,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':SLOT_ID,'status':'BLOCKED_HMLR_SOURCE_PREPARATION','error':f'{type(exc).__name__}: {exc}','actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}; code=2
    write_json(args.output_dir/'hmlr_source_manifest.json',payload); print(json.dumps({'ok':code==0,'status':payload['status'],'slot_id':payload['slot_id']})); return code
if __name__=='__main__': raise SystemExit(main())
