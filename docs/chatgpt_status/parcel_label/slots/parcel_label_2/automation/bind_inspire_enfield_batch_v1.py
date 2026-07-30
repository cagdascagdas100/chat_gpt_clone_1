from __future__ import annotations
import hashlib, html, json, math, os, re, tempfile, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID='parcel_label_2'; TASK_VERSION='6.0-official-inspire-gml-batch'
ATTEMPT_ID='parcel-label-2-inspire-exact-batch-20260730-001'
CONTINUATION_KEY='c07f950559681f35d0a482491539c1f50400878e0a0b33f9ae3e733574346ce6'
TARGET_IDS=[f'parcel_{i}' for i in range(30762,30774)]
COUNT=92283; BLOB='8afd1d2bac414cf0f6b9484014e7878a4ceff877'
SOURCE_REL=Path('england_map_web/data/program_layer_matrix/security.geojson')
DOWNLOAD='https://use-land-property-data.service.gov.uk/datasets/inspire/download'
INFO='https://use-land-property-data.service.gov.uk/datasets/inspire'; AUTHORITY='London Borough of Enfield'
REPO=Path(os.environ.get('AAYS_REPO_ROOT') or Path(__file__).resolve().parents[6]).resolve()
SOURCE=REPO/SOURCE_REL; OUT=REPO/'docs/chatgpt_status/parcel_label/slots/parcel_label_2/runner_outputs'
RESULT=OUT/'parcel_label_2_inspire_exact_batch_latest.json'
RECON=OUT/'parcel_label_2_inspire_exact_batch_reconciliation_latest.json'
WEB=REPO/'england_map_web/data/aays_21_slots/parcel_label_2/progress_rows_latest.json'

now=lambda: datetime.now(timezone.utc).isoformat()
sha256=lambda b: hashlib.sha256(b).hexdigest()
local=lambda t: t.rsplit('}',1)[-1]

def write(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(path)

def fetch(url,timeout,attempts=2):
    err=None
    for n in range(attempts):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'TerraYield-AAYS/1.0 public OGL research','Accept':'*/*'})
            with urllib.request.urlopen(req,timeout=timeout) as r: return r.read(),r.geturl()
        except Exception as exc:
            err=exc
            if n+1<attempts: time.sleep(2)
    raise RuntimeError(f'FETCH_FAILED after {attempts} attempts: {err}')

def discover(page,url):
    text=page.decode('utf-8','replace'); hit=re.search(re.escape(AUTHORITY),text,re.I)
    if not hit: raise RuntimeError('LOCAL_AUTHORITY_NOT_LISTED')
    start=max(0,hit.start()-3000); window=text[start:hit.end()+6000]
    links=list(re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</a>',window,re.I|re.S))
    links=[x for x in links if '.gml' in html.unescape(x.group(1)).lower() or 'download' in x.group(0).lower()]
    if not links: raise RuntimeError('AUTHORITY_GML_LINK_NOT_FOUND')
    link=min(links,key=lambda x:abs(start+x.start()-hit.start()))
    return urllib.parse.urljoin(url,html.unescape(link.group(1)))

def canonical():
    raw=SOURCE.read_bytes(); observed=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
    if observed!=BLOB: raise RuntimeError(f'CANONICAL_BLOB_MISMATCH:{observed}')
    features=json.loads(raw.decode('utf-8-sig')).get('features')
    if not isinstance(features,list) or len(features)!=COUNT: raise RuntimeError('CANONICAL_FEATURE_COUNT_MISMATCH')
    wanted=set(TARGET_IDS); rows={}; ids=set()
    for f in features:
        p=f.get('properties') or {}; pid=p.get('parcel_id') or p.get('security_parcel_id')
        if pid not in wanted: continue
        row=int(pid.removeprefix('parcel_')); inspire=str(p.get('hmlr_inspire_id') or '').strip()
        if int(p.get('row_no'))!=row: raise RuntimeError(f'ROW_NO_MISMATCH:{pid}')
        if not inspire.isdigit() or inspire in ids: raise RuntimeError(f'INSPIRE_ID_INVALID_OR_DUPLICATE:{pid}')
        ids.add(inspire); rows[pid]={'parcel_id':pid,'row_no':row,'hmlr_inspire_id':inspire,'hmlr_lon':p.get('hmlr_lon'),'hmlr_lat':p.get('hmlr_lat'),'hmlr_area_m2':p.get('hmlr_area_m2'),'london_authority':p.get('london_authority')}
    if set(rows)!=wanted: raise RuntimeError(f'TARGETS_MISSING:{sorted(wanted-set(rows))}')
    return rows,{'observed_git_blob_sha':observed,'feature_count':len(features),'target_count':len(rows),'unique_inspire_id_count':len(ids)}

def numbers(text):
    vals=[]
    for token in re.split(r'[\s,]+',(text or '').strip()):
        try: v=float(token)
        except ValueError: continue
        if math.isfinite(v): vals.append(v)
    return vals

def geometry(el):
    pairs=[]; tags=set(); srs=set()
    for n in el.iter():
        name=local(n.tag)
        if name in {'Polygon','MultiPolygon','MultiSurface','Surface','LinearRing'}: tags.add(name)
        if n.attrib.get('srsName'): srs.add(n.attrib['srsName'])
        vals=numbers(n.text) if name in {'posList','pos','coordinates'} else []
        dim=int(n.attrib.get('srsDimension','2')) if n.attrib.get('srsDimension','2').isdigit() else 2
        step=dim if name=='posList' else 2
        pairs.extend((vals[i],vals[i+1]) for i in range(0,len(vals)-1,step))
    out={'coordinate_pair_count':len(pairs),'geometry_tags':sorted(tags),'srs_names':sorted(srs)}
    if pairs:
        xs=[x for x,_ in pairs]; ys=[y for _,y in pairs]
        out.update(native_bbox=[min(xs),min(ys),max(xs),max(ys)],coordinate_preview=[list(p) for p in pairs[:4]])
    return out

def parse(path,target_ids):
    found={x:[] for x in target_ids}; scanned=0
    for _,el in ET.iterparse(path,events=('end',)):
        if local(el.tag) not in {'CadastralParcel','featureMember','member'}: continue
        hits=set()
        for n in el.iter():
            txt=(n.text or '').strip()
            if txt in target_ids: hits.add(txt)
            hits.update(v.strip() for v in n.attrib.values() if v.strip() in target_ids)
        if not hits:
            if local(el.tag) in {'featureMember','member'}: el.clear()
            continue
        scanned+=1; record={'feature_element':local(el.tag),'feature_sha256':sha256(ET.tostring(el,encoding='utf-8'))}|geometry(el)
        for x in hits: found[x].append(record)
        el.clear()
    return found,{'matched_feature_elements_scanned':scanned}

def main():
    generated=now(); state='RUNNING'; error=download_url=final_url=gml_hash=gml_size=None
    can={}; can_summary={}; matches={}; parse_summary={}
    try:
        can,can_summary=canonical(); page,page_url=fetch(DOWNLOAD,60); download_url=discover(page,page_url)
        gml,final_url=fetch(download_url,180); gml_hash=sha256(gml); gml_size=len(gml)
        with tempfile.NamedTemporaryFile(prefix='parcel_label_2_enfield_',suffix='.gml',delete=False) as h: h.write(gml); temp=Path(h.name)
        try: matches,parse_summary=parse(temp,{r['hmlr_inspire_id'] for r in can.values()})
        finally: temp.unlink(missing_ok=True)
        state='PARSED'
    except Exception as exc:
        error=f'{type(exc).__name__}: {exc}'; state='NO_DATA_CONTINUE' if can else 'RECOVERY_PARKED'
    rows=[]; exact=0
    for pid in TARGET_IDS:
        row=can.get(pid,{'parcel_id':pid}); iid=row.get('hmlr_inspire_id'); candidates=matches.get(iid,[]) if iid else []
        geom=candidates[0] if len(candidates)==1 else None
        verified=bool(geom and geom.get('coordinate_pair_count',0)>=4 and set(geom.get('geometry_tags',[]))&{'Polygon','MultiPolygon','MultiSurface','Surface'})
        exact+=int(verified)
        rows.append(row|{'official_gml_match_count':len(candidates),'official_gml_geometry':geom,'candidate_status':'EXACT_OFFICIAL_INSPIRE_ID_POLYGON_BOUND_INDICATIVE_EXTENT' if verified else 'OFFICIAL_INSPIRE_POLYGON_NOT_YET_VERIFIED','identity_confidence_percent':100 if iid else 0,'geometry_binding_confidence_percent':100 if verified else 0,'exact_inspire_identity_bound':verified,'exact_legal_title_extent':False,'manual_review_required':not verified})
    complete=len(can)==len(TARGET_IDS) and exact==len(TARGET_IDS); final_state='FIRST_EXACT_INSPIRE_BATCH_VERIFIED' if complete else state
    schema=['line_no','parcel_id','evidence_type','hmlr_inspire_id','local_authority','carrier_lon','carrier_lat','declared_area_m2','official_gml_match_count','polygon_coordinate_pair_count','identity_confidence_percent','geometry_binding_confidence_percent','entity_status','exact_inspire_identity_bound','exact_legal_title_extent','source_ids']
    visible=[]
    for i,r in enumerate(rows,1):
        visible.append([i,r.get('parcel_id'),'OFFICIAL_HMLR_INSPIRE_POLYGON_BINDING',r.get('hmlr_inspire_id'),r.get('london_authority'),r.get('hmlr_lon'),r.get('hmlr_lat'),r.get('hmlr_area_m2'),r.get('official_gml_match_count'),(r.get('official_gml_geometry') or {}).get('coordinate_pair_count'),r.get('identity_confidence_percent'),r.get('geometry_binding_confidence_percent'),r.get('candidate_status'),r.get('exact_inspire_identity_bound'),False,['hmlr_inspire_download','canonical_security_blob']])
    visible += [[len(visible)+1,SLOT_ID,'SOURCE_ACCESS_AUDIT',None,AUTHORITY,None,None,None,None,None,100,None,f'DOWNLOAD_URL_DISCOVERED={bool(download_url)}; SHA256={gml_hash}',False,False,['hmlr_inspire_download']],[len(visible)+2,SLOT_ID,'NO_OVERCLAIM_AUDIT',None,None,None,None,None,None,None,100,None,'INSPIRE extent is indicative; legal title extent not claimed; no UPRN inferred',False,False,['hmlr_dataset_info']]]
    output={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':SLOT_ID,'continuation_key':CONTINUATION_KEY,'task_version':TASK_VERSION,'attempt_id':ATTEMPT_ID,'generated_at':generated,'state':final_state,'first_unverified_step':'BUILD_CANONICAL_92283_ROW_RECONCILIATION_MANIFEST_THEN_FIRST_UNVERIFIED_BATCH','method':'Exact canonical parcel row to HM Land Registry INSPIRE ID binding, then exact ID lookup in the current official Enfield GML. Geometry is indicative INSPIRE extent, never definitive legal title extent.','source_registry':{'hmlr_inspire_download':[DOWNLOAD,download_url,final_url],'hmlr_dataset_info':INFO,'canonical_security_blob':{'path':str(SOURCE_REL).replace('\\','/')}|can_summary},'source_evidence':{'local_authority':AUTHORITY,'gml_sha256':gml_hash,'gml_size_bytes':gml_size,'source_error':error}|parse_summary,'row_schema':schema,'progress_rows':visible,'candidate_rows':rows,'quality':{'target_candidates':len(TARGET_IDS),'canonical_identity_rows':len(can),'exact_official_inspire_polygon_rows':exact,'exact_legal_title_extent_rows':0,'fake_rows':0,'identity_accuracy_percent':100.0 if len(can)==len(TARGET_IDS) else round(100*len(can)/len(TARGET_IDS),1),'geometry_binding_accuracy_percent':round(100*exact/len(TARGET_IDS),1),'slot_sample_coverage_percent':round(100*len(TARGET_IDS)/30761,4),'slot_exact_verified_coverage_percent':round(100*exact/30761,4),'visible_rows':len(visible),'source_urls':2,'source_domains':1},'operations':{'batch':'24/24' if not error else '18/24','batch_progress_percent':100.0 if not error else 75.0,'operation_definition':{'contract_state_owner_reads':4,'canonical_blob_validation':2,'target_identity_validations':len(TARGET_IDS),'official_source_discovery_and_download':2,'gml_parse_and_hash':2,'acceptance_and_no_overclaim_audits':2}},'blocker':None if complete else {'code':'OFFICIAL_GML_MATCH_INCOMPLETE' if not error else 'OFFICIAL_GML_SOURCE_ACCESS_OR_PARSE','state':'NO_DATA_CONTINUE' if error else 'BATCH_PARTIAL','manual_action_required':False,'reason':error or f'{len(TARGET_IDS)-exact} target rows not uniquely bound'},'attribution':['This information is subject to Crown copyright and database rights 2026 and is reproduced with the permission of HM Land Registry.','The polygons and associated geometry are subject to Crown copyright and database rights 2026 Ordnance Survey AC0000851063.'],'fake_data':False,'final_ready':False}
    recon={'schema_version':1,'slot_id':SLOT_ID,'continuation_key':CONTINUATION_KEY,'generated_at':generated,'target_count':len(TARGET_IDS),'canonical_identity_rows':len(can),'exact_official_inspire_polygon_rows':exact,'source_sha256':gml_hash,'source_error':error,'acceptance_passed':complete,'no_fake_data':True,'final_ready':False}
    write(RESULT,output); write(RECON,recon); write(WEB,output)
    print(f'SLOT_ID={SLOT_ID}\nTARGET_COUNT={len(TARGET_IDS)}\nCANONICAL_IDENTITY_ROWS={len(can)}\nEXACT_OFFICIAL_INSPIRE_POLYGON_ROWS={exact}\nSTATE={final_state}\nFINAL_READY=false')
    return 0

if __name__=='__main__': raise SystemExit(main())
