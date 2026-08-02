#!/usr/bin/env python3
"""Wave353: temporary DuckDB/httpfs direct Overture S3 three-bbox query gate."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path
DELTA=0.00035
MAX_CANDIDATES=25

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def atomic(path:Path,obj:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,sort_keys=True,separators=(',',':'));f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def rows(doc):
    out=[]
    for r in doc.get('rows',[]):
        p=r.get('properties') or {}
        out.append({'parcel_id':r.get('parcel_id') or p.get('parcel_id'),'hmlr_inspire_id':p.get('hmlr_inspire_id'),'longitude':p.get('hmlr_lon'),'latitude':p.get('hmlr_lat'),'london_authority':p.get('london_authority'),'geometry_type':r.get('geometry_type')})
    return out
def bbox(r):
    x=float(r['longitude']);y=float(r['latitude'])
    return [round(x-DELTA,7),round(y-DELTA,7),round(x+DELTA,7),round(y+DELTA,7)]
def self_test():
    assert re.fullmatch(r'[0-9a-f]{64}',sha(b'abc'))
    b=bbox({'longitude':-0.04,'latitude':51.67});assert b[0]<b[2] and b[1]<b[3]
    assert MAX_CANDIDATES==25
    print('SELF_TEST_PASS')
def install_duckdb(target:Path,timeout:int)->dict:
    cmd=[sys.executable,'-m','pip','install','--disable-pip-version-check','--no-input','--target',str(target),'duckdb']
    t=time.monotonic()
    try:r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    except subprocess.TimeoutExpired as e:
        data=(e.stdout or b'')+(e.stderr or b'')
        return {'attempted':True,'timed_out':True,'returncode':None,'installed':False,'duration_seconds':round(time.monotonic()-t,3),'log_bytes':len(data),'log_sha256':sha(data),'log_excerpt':data.decode('utf-8','replace')[-4000:]}
    data=r.stdout or b'';installed=any(target.glob('duckdb*'))
    return {'attempted':True,'timed_out':False,'returncode':r.returncode,'installed':installed,'duration_seconds':round(time.monotonic()-t,3),'log_bytes':len(data),'log_sha256':sha(data),'log_excerpt':data.decode('utf-8','replace')[-4000:]}
def run_query(pyroot:Path,release:str,row:dict,timeout:int)->dict:
    b=bbox(row);payload={'release':release,'bbox':b,'limit':MAX_CANDIDATES}
    code="""import duckdb,json,sys
p=json.loads(sys.argv[1]);b=p['bbox']
con=duckdb.connect(':memory:')
con.execute('SET threads=1')
con.execute(\"SET memory_limit='512MB'\")
con.execute('SET enable_http_metadata_cache=true')
con.execute('INSTALL httpfs')
con.execute('LOAD httpfs')
con.execute(\"SET s3_region='us-west-2'\")
path=f\"s3://overturemaps-us-west-2/release/{p['release']}/theme=buildings/type=building/*\"
sql=f\"SELECT id,bbox.xmin,bbox.ymin,bbox.xmax,bbox.ymax,version,subtype,class,height FROM read_parquet('{path}',filename=true,hive_partitioning=1) WHERE bbox.xmin < {b[2]} AND bbox.xmax > {b[0]} AND bbox.ymin < {b[3]} AND bbox.ymax > {b[1]} LIMIT {int(p['limit'])}\"
cur=con.execute(sql);cols=[d[0] for d in cur.description];rs=[dict(zip(cols,r)) for r in cur.fetchall()]
print(json.dumps({'duckdb_version':duckdb.__version__,'candidate_count':len(rs),'candidates':rs},default=str,sort_keys=True))"""
    env=os.environ.copy();env['PYTHONPATH']=str(pyroot)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    t=time.monotonic()
    try:r=subprocess.run([sys.executable,'-c',code,json.dumps(payload)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=timeout,check=False)
    except subprocess.TimeoutExpired as e:
        return {'parcel_id':row['parcel_id'],'bbox':b,'attempted':True,'timed_out':True,'returncode':None,'duration_seconds':round(time.monotonic()-t,3),'stdout_excerpt':(e.stdout or b'').decode('utf-8','replace')[-2000:],'stderr_excerpt':(e.stderr or b'').decode('utf-8','replace')[-4000:],'success':False,'candidate_count':0,'candidates':[]}
    out=r.stdout.decode('utf-8','replace');err=r.stderr.decode('utf-8','replace')
    res={'parcel_id':row['parcel_id'],'bbox':b,'attempted':True,'timed_out':False,'returncode':r.returncode,'duration_seconds':round(time.monotonic()-t,3),'stdout_excerpt':out[-4000:],'stderr_excerpt':err[-4000:],'success':False,'candidate_count':0,'candidates':[]}
    if r.returncode==0:
        try:
            d=json.loads(out.strip().splitlines()[-1]);res.update({'success':True,'candidate_count':d.get('candidate_count',0),'candidates':d.get('candidates',[]),'duckdb_version':d.get('duckdb_version')})
        except Exception:pass
    return res
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--canonical');ap.add_argument('--fixture');ap.add_argument('--output');ap.add_argument('--query-timeout',type=int,default=45);ap.add_argument('--install-timeout',type=int,default=120);ap.add_argument('--delay',type=float,default=1);ap.add_argument('--accessed-at');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:self_test();return 0
    if not(a.canonical and a.fixture and a.output and a.accessed_at):ap.error('required args missing')
    c=json.loads(Path(a.canonical).read_text());f=json.loads(Path(a.fixture).read_text());target={'parcel_30762','parcel_30763','parcel_30764'};sc=[r for r in rows(c) if r['parcel_id'] in target]
    if len(sc)!=3 or any(r['london_authority']!='Enfield' for r in sc):raise SystemExit('CANONICAL_SCOPE_VALIDATION_FAILED')
    pre=importlib.util.find_spec('duckdb') is not None;cli=shutil.which('duckdb');install=None;queries=[];tmp=None;pyroot=None
    try:
        if pre:pyroot=Path('')
        else:
            tmp=tempfile.TemporaryDirectory(prefix='aays-wave353-duckdb-');pyroot=Path(tmp.name);install=install_duckdb(pyroot,a.install_timeout)
        available=pre or bool(install and install['installed'])
        if available:
            for i,r in enumerate(sc):
                queries.append(run_query(pyroot,f['confirmed_release'],r,a.query_timeout))
                if i+1<len(sc):time.sleep(a.delay)
        else:queries=[{'parcel_id':r['parcel_id'],'bbox':bbox(r),'attempted':False,'reason':'DUCKDB_NOT_AVAILABLE','success':False,'candidate_count':0,'candidates':[]} for r in sc]
    finally:
        if tmp:tmp.cleanup()
    successes=sum(bool(q.get('success')) for q in queries);candidates=sum(int(q.get('candidate_count',0)) for q in queries)
    install_failed=not pre and not bool(install and install.get('installed'));block=[]
    if install_failed:block.append('DUCKDB_NOT_INSTALLABLE_FROM_CONFIGURED_PACKAGE_INDEX')
    if successes<3:block.append('THREE_BOUNDED_DUCKDB_HTTPFS_OVERTURE_S3_QUERIES_NOT_COMPLETED')
    if candidates==0:block.append('THREE_OVERTURE_BUILDING_CANDIDATE_SETS_NOT_ACQUIRED')
    block+=['THREE_EXACT_UPRNS_NOT_ACQUIRED','EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE']
    state='OVERTURE_S3_BOUNDED_CANDIDATES_ACQUIRED_CONTINUE_EXACT_BINDING' if successes==3 and candidates>0 else 'NO_DATA_CONTINUE'
    nxt='ASSESS_OVERTURE_STAC_BUILDING_ASSET_LIST_AND_BOUNDED_PARQUET_RANGE_QUERY_OR_NO_DATA_CONTINUE'
    receipts=json.dumps({'preinstalled':pre,'cli':cli,'install':install,'queries':queries},sort_keys=True,default=str)
    runtime=[{'source_url':'https://pypi.org/project/duckdb/','accessed_at':a.accessed_at,'content_sha256':sha(receipts.encode()),'hash_scope':'temporary_duckdb_install_httpfs_and_three_bbox_query_receipts','record_scope':'Temporary DuckDB installation, conditional httpfs load, and three isolated official Overture S3 bbox queries; no persistent package or credential.','relevant_record_ids_or_excerpt':f'preinstalled={pre}; cli_present={bool(cli)}; install_returncode={None if install is None else install.get("returncode")}; successful_bbox_query_count={successes}; candidate_feature_count={candidates}','supports_fields':['duckdb_installability','httpfs_load','official_overture_s3','three_bounded_bbox_queries','candidate_count','no_exact_binding_claim'],'license_or_terms_url':'https://github.com/duckdb/duckdb/blob/main/LICENSE'}]
    obj={'schema_version':1,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'gas_emissions_2','wave':353,'accessed_at':a.accessed_at,'state':state,'decision':'DUCKDB_HTTPFS_DIRECT_OVERTURE_S3_THREE_BBOX_GATE_ASSESSED','confirmed_release':f['confirmed_release'],'canonical_sample_rows_in_scope':3,'assessments':[dict(r,bbox=bbox(r)) for r in sc],'duckdb_module_preinstalled':pre,'duckdb_cli_present':bool(cli),'temporary_duckdb_install':install,'query_execution_count':3,'successful_bbox_query_count':successes,'candidate_feature_count':candidates,'bbox_queries':queries,'geoparquet_full_downloaded':False,'source_evidence_manifest':f['source_evidence_manifest'],'runtime_source_evidence':runtime,'business_rows_produced':0,'parcel_rows_bound':0,'completed_count':0,'target_count':30761,'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'blocker':';'.join(block),'first_unverified_step':nxt,'fake_data':False,'final_ready':False}
    atomic(Path(a.output),obj);print(json.dumps({'state':state,'duckdb_preinstalled':pre,'install_returncode':None if install is None else install.get('returncode'),'successful_bbox_query_count':successes,'candidate_feature_count':candidates,'business_rows_produced':0,'parcel_rows_bound':0,'first_unverified_step':nxt},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
