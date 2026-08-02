#!/usr/bin/env python3
"""Wave351: bounded Fused Overture UDF bbox query-contract gate."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, tempfile, time
from pathlib import Path
from urllib import request

MAX_DOC=600_000
MAX_SOURCE=120_000
UA="AAYS-Wave351/1.0 contract-only"
DELTA=0.00015

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(payload,f,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def bounded_get(name: str, url: str, timeout: float, max_bytes: int) -> dict:
    out={'probe_name':name,'source_url':url,'method':'GET','http_status':None,'final_url':None,
         'content_type':None,'content_length_header':None,'bytes_read':0,
         'content_sha256':sha256_bytes(b''),'truncated':False,'network_error':None,'_text':''}
    req=request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,text/plain,*/*'},method='GET')
    try:
        with request.urlopen(req,timeout=timeout) as r:
            data=r.read(max_bytes+1)
            out['http_status']=getattr(r,'status',None); out['final_url']=r.geturl()
            out['content_type']=r.headers.get('Content-Type'); out['content_length_header']=r.headers.get('Content-Length')
            if len(data)>max_bytes: data=data[:max_bytes]; out['truncated']=True
            out['bytes_read']=len(data); out['content_sha256']=sha256_bytes(data); out['_text']=data.decode('utf-8','replace')
    except Exception as exc:
        out['network_error']=f'{type(exc).__name__}:{exc}'
    return out

def canonical_rows(doc: dict) -> list[dict]:
    rows=[]
    for row in doc.get('rows',[]):
        p=row.get('properties') or {}
        rows.append({'parcel_id':row.get('parcel_id') or p.get('parcel_id'),'row_no':p.get('row_no'),
                     'hmlr_inspire_id':p.get('hmlr_inspire_id'),'longitude':p.get('hmlr_lon'),
                     'latitude':p.get('hmlr_lat'),'london_authority':p.get('london_authority'),
                     'geometry_type':row.get('geometry_type')})
    return rows

def bbox_for(row: dict) -> list[float]:
    lon=float(row['longitude']); lat=float(row['latitude'])
    return [round(lon-DELTA,7),round(lat-DELTA,7),round(lon+DELTA,7),round(lat+DELTA,7)]

def self_test() -> None:
    assert re.fullmatch(r'[0-9a-f]{64}',sha256_bytes(b'abc'))
    r={'longitude':-0.04,'latitude':51.67}
    b=bbox_for(r); assert len(b)==4 and b[0]<b[2] and b[1]<b[3]
    sample={'rows':[{'parcel_id':'parcel_30762','geometry_type':'Point','properties':{'row_no':30762,'hmlr_inspire_id':'46058185','hmlr_lon':-0.0407406,'hmlr_lat':51.6769078,'london_authority':'Enfield'}}]}
    rows=canonical_rows(sample); assert rows[0]['parcel_id']=='parcel_30762'
    print('SELF_TEST_PASS')

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--canonical'); ap.add_argument('--fixture'); ap.add_argument('--output')
    ap.add_argument('--timeout',type=float,default=30); ap.add_argument('--delay',type=float,default=1.0)
    ap.add_argument('--accessed-at'); ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test: self_test(); return 0
    if not (args.canonical and args.fixture and args.output): ap.error('--canonical, --fixture and --output are required')
    canonical=json.loads(Path(args.canonical).read_text(encoding='utf-8'))
    fixture=json.loads(Path(args.fixture).read_text(encoding='utf-8'))
    targets={'parcel_30762','parcel_30763','parcel_30764'}
    scoped=[r for r in canonical_rows(canonical) if r['parcel_id'] in targets]
    if len(scoped)!=3 or any(r['london_authority']!='Enfield' for r in scoped): raise SystemExit('CANONICAL_SCOPE_VALIDATION_FAILED')
    bbox_contracts=[dict(r,bounds=bbox_for(r),overture_type='building',theme='buildings',release='2026-07-22-0',use_columns=['id','bbox','geometry','sources']) for r in scoped]
    urls=fixture['candidate_urls']; probes=[]
    order=[('overture_fused_docs',MAX_DOC),('fused_running_udfs',MAX_DOC),('fused_udfs_as_api',MAX_DOC),('pinned_udf_source',MAX_SOURCE)]
    for i,(name,limit) in enumerate(order):
        probes.append(bounded_get(name,urls[name],args.timeout,limit))
        if i+1<len(order): time.sleep(args.delay)
    texts={p['probe_name']:p.pop('_text','') for p in probes}
    checks={
      'overture_docs_contract': all(re.search(x,texts['overture_fused_docs'],re.I|re.S) for x in [r'(bbox|bounds)',r'overture_type',r'building',r'release',r'column']),
      'running_docs_contract': all(re.search(x,texts['fused_running_udfs'],re.I|re.S) for x in [r'public UDF',r'fused\.load',r'min_x',r'max_y']),
      'api_token_contract': all(re.search(x,texts['fused_udfs_as_api'],re.I|re.S) for x in [r'canvas token',r'fc_',r'udf\.ai']),
      'pinned_source_contract': all(re.search(x,texts['pinned_udf_source'],re.I|re.S) for x in [r'def udf',r'bounds',r'release',r'overture_type',r'use_columns',r'us-west-2\.opendata\.source\.coop',r'table_to_tile'])
    }
    live_count=sum(1 for p in probes if p['network_error'] is None and p['http_status'] and 200<=p['http_status']<400)
    fused_sdk_installed=importlib.util.find_spec('fused') is not None
    canvas_token_present=bool(os.environ.get('FUSED_CANVAS_TOKEN'))
    contract_live=(live_count==4 and all(checks.values()))
    remote_udf_execution_attempted=False
    business_rows=0; parcel_rows=0
    state='FUSED_OVERTURE_UDF_BBOX_CONTRACT_AVAILABLE_CONTINUE_BOUNDED_EXECUTION' if contract_live else 'NO_DATA_CONTINUE'
    blocker_parts=[]
    if not contract_live: blocker_parts.append('FUSED_OVERTURE_UDF_BBOX_CONTRACT_NOT_LIVE_ACQUIRED')
    if not fused_sdk_installed: blocker_parts.append('FUSED_PYTHON_SDK_NOT_INSTALLED')
    if not canvas_token_present: blocker_parts.append('PUBLIC_FUSED_CANVAS_TOKEN_NOT_PROVIDED')
    blocker_parts += ['REMOTE_FUSED_UDF_COMPUTE_NOT_EXECUTED_BY_CONTRACT_GATE_DESIGN','THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED','THREE_EXACT_UPRNS_NOT_ACQUIRED','EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE']
    blocker=';'.join(blocker_parts)
    next_step='ASSESS_FUSED_PYTHON_SDK_PUBLIC_UDF_LOAD_AND_THREE_BOUNDED_BBOX_QUERY_EXECUTION_OR_NO_DATA_CONTINUE'
    errors=[f"{p['probe_name']}:{p['network_error']}" for p in probes if p['network_error']]
    runtime=[{'source_url':'https://docs.overturemaps.org/getting-data/data-mirrors/fused/','accessed_at':args.accessed_at,
      'content_sha256':sha256_bytes(('\n'.join(errors) if errors else json.dumps({'checks':checks,'probes':probes},sort_keys=True)).encode()),
      'hash_scope':'four_bounded_contract_probe_receipts','record_scope':'Overture/Fused docs and pinned UDF source; no remote UDF compute or GeoParquet body.',
      'relevant_record_ids_or_excerpt':'; '.join(errors) if errors else json.dumps(checks,sort_keys=True),
      'supports_fields':['bounded_contract_probe','bbox_parameter_contract','public_udf_loading_contract','canvas_token_contract','remote_compute_not_attempted','no_exact_binding'],
      'license_or_terms_url':'https://docs.overturemaps.org/attribution/'}]
    payload={'schema_version':1,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'gas_emissions_2','wave':351,
      'accessed_at':args.accessed_at,'state':state,'decision':'FUSED_OVERTURE_UDF_BBOX_QUERY_CONTRACT_GATE_ASSESSED',
      'canonical_sample_rows_in_scope':3,'bbox_contracts':bbox_contracts,'probe_count':4,'live_probe_count':live_count,
      'network_error_count':sum(1 for p in probes if p['network_error']),'total_bytes_read':sum(p['bytes_read'] for p in probes),
      'contract_checks':checks,'fused_sdk_installed':fused_sdk_installed,'canvas_token_present':canvas_token_present,
      'remote_udf_execution_attempted':remote_udf_execution_attempted,'geoparquet_body_downloaded':False,
      'probes':probes,'source_evidence_manifest':fixture['source_evidence_manifest'],'runtime_source_evidence':runtime,
      'business_rows_produced':business_rows,'parcel_rows_bound':parcel_rows,'completed_count':0,'target_count':30761,
      'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'blocker':blocker,'first_unverified_step':next_step,
      'fake_data':False,'final_ready':False}
    atomic_json(Path(args.output),payload)
    print(json.dumps({'state':state,'probe_count':4,'live_probe_count':live_count,'network_error_count':payload['network_error_count'],
      'total_bytes_read':payload['total_bytes_read'],'fused_sdk_installed':fused_sdk_installed,'canvas_token_present':canvas_token_present,
      'remote_udf_execution_attempted':False,'business_rows_produced':0,'parcel_rows_bound':0,'first_unverified_step':next_step},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
