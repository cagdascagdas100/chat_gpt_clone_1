#!/usr/bin/env python3
"""Bounded DuckDB/httpfs Overture S3 bbox gate; no geometry or parcel binding."""
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
STAC='https://stac.overturemaps.org/catalog.json'; PKG='duckdb>=1.1.0'; MAX=25

def h(b): return hashlib.sha256(b).hexdigest()
def bbox(x,y,d=.00035): return [round(x-d,7),round(y-d,7),round(x+d,7),round(y+d,7)]
def latest(j):
    v=j.get('latest')
    if isinstance(v,str) and v[:4].isdigit(): return v
    for x in j.get('links',[]):
        if x.get('rel')=='latest':
            for p in reversed(str(x.get('href','')).rstrip('/').split('/')):
                if p[:4].isdigit() and '.' in p: return p.removesuffix('.json')
    return None
def write(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); data=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
    with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f: f.write(data); n=f.name
    os.replace(n,p)
def stac_get(timeout):
    t=time.monotonic()
    try:
        r=urllib.request.urlopen(urllib.request.Request(STAC,headers={'User-Agent':'AAYS-W353'}),timeout=timeout); b=r.read(200001)
        if len(b)>200000: raise ValueError('STAC_TOO_LARGE')
        return {'ok':True,'bytes':len(b),'sha256':h(b),'json':json.loads(b),'seconds':round(time.monotonic()-t,3)}
    except Exception as e: return {'ok':False,'bytes':0,'error':f'{type(e).__name__}:{e}','seconds':round(time.monotonic()-t,3)}
def install(target,timeout):
    c=[sys.executable,'-m','pip','install','--disable-pip-version-check','--no-input','--no-cache-dir','--target',target,PKG]; t=time.monotonic()
    try:
        r=subprocess.run(c,capture_output=True,text=True,timeout=timeout); s=(r.stdout or '')+(r.stderr or '')
        return {'attempted':True,'returncode':r.returncode,'installed':r.returncode==0 and Path(target,'duckdb').exists(),'seconds':round(time.monotonic()-t,3),'log_sha256':h(s.encode()),'log_excerpt':s[-1200:],'temporary_only':True}
    except subprocess.TimeoutExpired: return {'attempted':True,'returncode':None,'installed':False,'timed_out':True,'temporary_only':True}
def query(target,release,pid,b,timeout):
    code="""import duckdb,json,os\ncon=duckdb.connect(':memory:'); con.execute('INSTALL httpfs'); con.execute('LOAD httpfs'); con.execute(\"SET s3_region='us-west-2'\")\nb=json.loads(os.environ['B']); p=os.environ['P']; q='SELECT id,bbox.xmin,bbox.ymin,bbox.xmax,bbox.ymax FROM read_parquet(?,hive_partitioning=1) WHERE bbox.xmin<? AND bbox.xmax>? AND bbox.ymin<? AND bbox.ymax>? LIMIT 25'; print(json.dumps(con.execute(q,[p,b[2],b[0],b[3],b[1]]).fetchall()))"""
    env=os.environ.copy(); env['PYTHONPATH']=target; env['B']=json.dumps(b); env['P']=f's3://overturemaps-us-west-2/release/{release}/theme=buildings/type=building/*.parquet'
    try:
        r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=timeout,env=env); rows=json.loads(r.stdout) if r.returncode==0 else []
        return {'parcel_id':pid,'attempted':True,'success':r.returncode==0,'returncode':r.returncode,'row_count':len(rows),'rows':rows[:MAX],'stderr_sha256':h((r.stderr or '').encode()),'geometry_selected':False}
    except subprocess.TimeoutExpired: return {'parcel_id':pid,'attempted':True,'success':False,'timed_out':True,'row_count':0,'rows':[],'geometry_selected':False}
def selftest():
    assert bbox(-.0407406,51.6769078)==[-.0410906,51.6765578,-.0403906,51.6772578]; assert latest({'latest':'2026-06-17.0'})=='2026-06-17.0'; print('SELF_TEST_PASS')
def main():
    a=argparse.ArgumentParser(); a.add_argument('--canonical'); a.add_argument('--fixture'); a.add_argument('--output'); a.add_argument('--timeout',type=int,default=45); a.add_argument('--install-timeout',type=int,default=120); a.add_argument('--stac-timeout',type=int,default=30); a.add_argument('--accessed-at'); a.add_argument('--self-test',action='store_true'); x=a.parse_args()
    if x.self_test: selftest(); return
    can=json.load(open(x.canonical)); fix=json.load(open(x.fixture)); pts=[]
    for r in can['rows'][:3]:
        p=r['properties']; pts.append({'parcel_id':p['parcel_id'],'hmlr_inspire_id':p['hmlr_inspire_id'],'longitude':p['hmlr_lon'],'latitude':p['hmlr_lat'],'bbox':bbox(p['hmlr_lon'],p['hmlr_lat'])})
    sr=stac_get(x.stac_timeout); rel=latest(sr.get('json',{})) if sr['ok'] else None; pre=importlib.util.find_spec('duckdb') is not None
    with tempfile.TemporaryDirectory(prefix='aays_w353_') as d:
        ir={'attempted':False,'returncode':0,'installed':True,'temporary_only':True} if pre else install(d,x.install_timeout)
        if ir['installed'] and rel: qr=[query(d,rel,p['parcel_id'],p['bbox'],x.timeout) for p in pts]
        else: qr=[{'parcel_id':p['parcel_id'],'attempted':False,'success':False,'row_count':0,'rows':[],'reason':';'.join(([] if ir['installed'] else ['DUCKDB_NOT_INSTALLED'])+([] if rel else ['LATEST_RELEASE_NOT_RESOLVED'])),'geometry_selected':False} for p in pts]
    ok=sum(q['success'] for q in qr); n=sum(q['row_count'] for q in qr); bl=[]
    if not sr['ok']: bl+=['OVERTURE_STAC_LATEST_RELEASE_NOT_LIVE_ACQUIRED']
    if not ir['installed']: bl+=['DUCKDB_NOT_INSTALLABLE_FROM_CONFIGURED_PACKAGE_INDEX']
    if ok<3: bl+=['THREE_BOUNDED_DUCKDB_HTTPFS_OVERTURE_S3_BBOX_QUERIES_NOT_COMPLETED']
    if n==0: bl+=['THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED']
    bl+=['THREE_EXACT_UPRNS_NOT_ACQUIRED','EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE']
    ex=f"stac_ok={sr['ok']};release={rel};installed={ir['installed']};queries={ok};candidates={n}"
    rt={'source_url':STAC,'accessed_at':x.accessed_at,'content_sha256':h(ex.encode()),'hash_scope':'stac_install_three_bbox_receipts','record_scope':'STAC, temporary DuckDB install and three bounded S3 bbox queries.','relevant_record_ids_or_excerpt':ex,'supports_fields':['latest_release','duckdb_installability','httpfs','candidate_count','no_geometry_selection'],'license_or_terms_url':'https://docs.overturemaps.org/attribution/'}
    write(x.output,{'schema_version':1,'architecture_version':3,'slot_id':'gas_emissions_2','wave':353,'accessed_at':x.accessed_at,'assessments':pts,'stac_receipt':{k:v for k,v in sr.items() if k!='json'},'resolved_release':rel,'temporary_duckdb_install':ir,'bbox_query_results':qr,'successful_bbox_query_count':ok,'candidate_feature_count':n,'business_rows_produced':0,'parcel_rows_bound':0,'completed_count':0,'target_count':30761,'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'decision':'DUCKDB_HTTPFS_DIRECT_OVERTURE_S3_THREE_BBOX_QUERY_GATE_ASSESSED','state':'NO_DATA_CONTINUE','blocker':';'.join(bl),'first_unverified_step':'ASSESS_OVERTURE_EXPLORER_VISIBLE_GEOJSON_THREE_POINT_BUILDING_CANDIDATE_GATE_OR_NO_DATA_CONTINUE','source_evidence_manifest':fix['source_evidence_manifest'],'runtime_source_evidence':[rt],'fake_data':False,'final_ready':False})
if __name__=='__main__': main()
