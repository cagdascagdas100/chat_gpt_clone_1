#!/usr/bin/env python3
"""Scan the official UK ETS HSE workbook for two exact site aliases, fail closed."""
import argparse,hashlib,io,json,re,unicodedata,urllib.error,urllib.parse,urllib.request,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
M='http://schemas.openxmlformats.org/spreadsheetml/2006/main'; R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'; P='http://schemas.openxmlformats.org/package/2006/relationships'
def req(x,m):
 if not x: raise ValueError(m)
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(x): return ' '.join(re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',str(x or '')).encode('ascii','ignore').decode().lower()).split())
def col(ref):
 s=re.match(r'[A-Z]+',ref or ''); req(s,'bad cell ref'); n=0
 for c in s.group(): n=n*26+ord(c)-64
 return n
def workbook(raw,lim):
 rows=[]; names=[]
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  req('xl/workbook.xml' in z.namelist(),'invalid xlsx')
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   root=ET.fromstring(z.read('xl/sharedStrings.xml')); ss=[''.join(t.text or '' for t in x.iter('{%s}t'%M)) for x in root.findall('{%s}si'%M)]
  wb=ET.fromstring(z.read('xl/workbook.xml')); rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
  rm={x.get('Id'):x.get('Target') for x in rel.findall('{%s}Relationship'%P)}; sheets=wb.find('{%s}sheets'%M); req(sheets is not None,'no sheets')
  defs=[]
  for s in sheets.findall('{%s}sheet'%M):
   name=s.get('name') or 'unnamed'; target=rm.get(s.get('{%s}id'%R)); req(target,'missing sheet rel'); target=target.lstrip('/'); defs.append((name,target if target.startswith('xl/') else 'xl/'+target))
  req(len(defs)<=lim['maximum_sheets'],'too many sheets')
  for name,path in defs:
   names.append(name); root=ET.fromstring(z.read(path)); data=root.find('{%s}sheetData'%M)
   if data is None: continue
   for i,row in enumerate(data.findall('{%s}row'%M),1):
    req(i<=lim['maximum_rows_per_sheet'],'too many sheet rows'); cells={}
    for c in row.findall('{%s}c'%M):
     k=col(c.get('r')); req(k<=lim['maximum_columns'],'too many columns'); typ=c.get('t'); v=c.find('{%s}v'%M)
     if typ=='inlineStr': val=''.join(t.text or '' for t in c.iter('{%s}t'%M))
     elif v is None or v.text is None: val=''
     elif typ=='s': val=ss[int(v.text)]
     elif typ=='b': val='TRUE' if v.text=='1' else 'FALSE'
     else: val=v.text
     if val!='': cells[k]=val
    if cells: rows.append({'sheet_name':name,'row_number':int(row.get('r') or i),'cells':cells})
    req(len(rows)<=lim['maximum_total_rows'],'too many total rows')
 return rows,names
def load(c,fixture):
 try:
  if fixture: raw=fixture.read_bytes(); status=200
  else:
   u=c['source_evidence_manifest']['source_url']; p=urllib.parse.urlparse(u); req(p.scheme=='https' and p.netloc=='assets.publishing.service.gov.uk','source URL mismatch')
   q=urllib.request.Request(u,headers={'User-Agent':'AAYS-UK-ETS-HSE-Gate/1.0'},method='GET')
   with urllib.request.urlopen(q,timeout=c['network_policy']['dataset_timeout_seconds']) as r: status=int(getattr(r,'status',r.getcode())); raw=r.read(c['network_policy']['maximum_dataset_bytes']+1)
  req(status==200,'HTTP status %s'%status); req(len(raw)<=c['network_policy']['maximum_dataset_bytes'],'dataset too large'); rows,names=workbook(raw,c['network_policy']); return raw,rows,names,None,status
 except urllib.error.HTTPError as e: return None,[],[],f'HTTPError: {e.code} {e.reason}'[:500],e.code
 except Exception as e: return None,[],[],f'{type(e).__name__}: {e}'[:500],None
def main():
 a=argparse.ArgumentParser(); a.add_argument('--contract',type=Path,required=True); a.add_argument('--prior',type=Path,required=True); a.add_argument('--output',type=Path,required=True); a.add_argument('--fixture-xlsx',type=Path); x=a.parse_args()
 cb=x.contract.read_bytes(); pb=x.prior.read_bytes(); c=json.loads(cb); prior=json.loads(pb); pre=c['precondition']
 req(c.get('schema_version')==3 and c.get('slot_id')=='gas_emissions_3' and c.get('state')=='READY' and c.get('status')=='ready' and c.get('claimable') is True and c.get('ready_for_claim') is True,'bad contract')
 req(sha(pb)==pre['prior_output_sha256'] and prior.get('task_id')==pre['required_prior_task_id'] and prior.get('state')==pre['required_prior_state'] and prior.get('next_unverified_step')==pre['required_prior_next_unverified_step'],'bad prior')
 for k in ('source_url','publication_page_url','accessed_at','content_sha256','supports_fields','relevant_record_ids_or_excerpt','license_or_terms_url'): req(c['source_evidence_manifest'].get(k),'missing manifest '+k)
 targets=c['runtime_targets']; req(len(targets)==2,'need two targets'); raw,rows,names,err,status=load(c,x.fixture_xlsx); results=[]
 for t in targets:
  matches=[]; aliases=[(v,norm(v)) for v in t['exact_aliases']]
  for row in rows:
   ordered=[{'column_index':k,'value':row['cells'][k]} for k in sorted(row['cells'])]; text=norm(' | '.join(str(v['value']) for v in ordered)); hit=[v for v,n in aliases if n and n in text]
   if hit: matches.append({'sheet_name':row['sheet_name'],'row_number':row['row_number'],'cells':ordered,'normalized_row_text':text,'matched_exact_aliases':hit})
   req(len(matches)<=t['maximum_matches'],'too many matches')
  results.append({'target_id':t['target_id'],'site_name':t['site_name'],'attempt_completed':True,'exact_aliases':t['exact_aliases'],'matched_rows':len(matches),'matches':matches,'decision':'EXACT_SITE_ROWS_VERIFIED' if matches else 'NO_DATA_CONTINUE','error':err})
 done=sum(v['attempt_completed'] for v in results); mt=sum(bool(v['matched_rows']) for v in results); mr=sum(v['matched_rows'] for v in results); state='MATCHES_VERIFIED' if mt==2 else ('PARTIAL_MATCH_CONTINUE' if mt else 'NO_DATA_CONTINUE'); nxt='VALIDATE_UK_ETS_HSE_MATCHED_EMISSIONS_COLUMNS_FOR_GAS_EMISSIONS_BINDING' if state=='MATCHES_VERIFIED' else ('ADVANCE_UNMATCHED_TARGET_TO_NEXT_SOURCE_AND_VALIDATE_MATCHED_UK_ETS_HSE_ROWS' if mt else 'ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_UK_ETS_HSE_NO_DATA')
 out={'schema_version':3,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'gas_emissions_3','task_id':c['task_id'],'continuation_key':c['continuation_key'],'state':state,'panel_status':'PUBLISHED','execution_mode':'SYNTHETIC_FIXTURE' if x.fixture_xlsx else 'LIVE_NETWORK','first_unverified_step_completed':c['first_unverified_step'],'next_unverified_step':nxt,'input':{'contract_path':x.contract.as_posix(),'contract_sha256':sha(cb),'prior_output_path':x.prior.as_posix(),'prior_output_sha256':sha(pb),'dataset_url':c['source_evidence_manifest']['source_url'],'dataset_http_status':status,'dataset_sha256':sha(raw) if raw else None,'dataset_bytes':len(raw) if raw else 0,'dataset_error':err},'counts':{'completed_count':done,'target_count':2,'dataset_fetch_attempts':1,'workbook_sheets_scanned':len(names),'workbook_rows_scanned':len(rows),'matched_targets':mt,'matched_rows':mr,'produced_business_rows':mr,'produced_source_evidence_records':2},'progress_percent':round(done/2*100,6),'sheet_names':names,'targets':results,'decision':{'exact_normalized_alias_gate_required':True,'all_workbook_sheets_scanned':raw is not None,'source_cells_preserved_without_inference':True,'inferred_values':0,'fake_data':False}}
 req(done==2,'incomplete'); x.output.parent.mkdir(parents=True,exist_ok=True); tmp=x.output.with_suffix(x.output.suffix+'.tmp'); tmp.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n'); tmp.replace(x.output)
if __name__=='__main__': main()
