#!/usr/bin/env python3
import argparse, hashlib, json, os, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT='future_growth_2'; WS='AAYS_21_SLOT_SAFE_PARALLEL_V1'
SRC_KEY='5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462'
TARGETS={30762:17,46142:20,61522:33}; HOST='services.arcgis.com'
FIELDS='objectid,sitename,status,designation,classification,notes,source'

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def load(p):
    v=json.loads(Path(p).read_text(encoding='utf-8'))
    if not isinstance(v,dict): raise ValueError('JSON root must be object')
    return v

def save(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=str(p.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:
            json.dump(v,f,ensure_ascii=False,sort_keys=True,separators=(',',':')); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def url(row,layer):
    base=str(row['service']).rstrip('/'); u=urllib.parse.urlparse(base)
    if u.scheme!='https' or u.hostname!=HOST or not u.path.endswith('/FeatureServer'): raise ValueError('unapproved service')
    q={'f':'json','geometry':f"{float(row['lon']):.7f},{float(row['lat']):.7f}",'geometryType':'esriGeometryPoint','inSR':'4326','spatialRel':'esriSpatialRelIntersects','outFields':FIELDS,'returnGeometry':'false','resultRecordCount':'5'}
    return f'{base}/{layer}/query?{urllib.parse.urlencode(q)}'

def check(man,meta):
    if man.get('slot_id')!=SLOT or man.get('continuation_key')!=SRC_KEY: raise ValueError('manifest lineage')
    rows={int(x['row_no']):x for x in man.get('rows',[])}
    if set(rows)!=set(TARGETS): raise ValueError('anchor rows')
    if meta.get('slot_id')!=SLOT or meta.get('continuation_key')!=SRC_KEY or meta.get('state')!='PUBLISHED' or meta.get('panel_status')!='PUBLISHED' or meta.get('fake_data') is not False or (meta.get('completed_count'),meta.get('target_count'))!=(3,3): raise ValueError('metadata gate')
    got={int(x['row_no']):x for x in meta.get('results',[])}
    if set(got)!=set(TARGETS): raise ValueError('metadata rows')
    for n,l in TARGETS.items():
        layers={int(x[0]) for x in rows[n].get('layers',[])}
        if l not in layers or got[n].get('layer_id')!=l or got[n].get('data_status')!='VERIFIED_METADATA' or got[n].get('http_status')!=200 or not got[n].get('raw_sha256'): raise ValueError('metadata row gate')
    return rows

def fetch(u,t):
    r=urllib.request.Request(u,headers={'Accept':'application/json','User-Agent':'TerraYield-AAYS/1.0 future_growth_2'})
    with urllib.request.urlopen(r,timeout=t) as x: status=int(x.status); body=x.read()
    data=json.loads(body.decode('utf-8'))
    if not isinstance(data,dict): raise ValueError('response root')
    return status,body,data

def run(man,meta,key,t,fn=fetch):
    if len(key)!=64 or any(c not in '0123456789abcdef' for c in key): raise ValueError('continuation key')
    rows=check(man,meta); out=[]; ok=zero=fail=0
    for n in sorted(TARGETS):
        row=rows[n]; u=url(row,TARGETS[n]); base={'row_no':n,'parcel_id':str(row['parcel_id']),'lpa':str(row['lpa']),'lon':float(row['lon']),'lat':float(row['lat']),'layer_id':TARGETS[n],'query_url':u,'fetched_at_utc':now(),'query_scope':'ANCHOR_POINT_INTERSECTS_ONLY_NOT_PARCEL_POLYGON','future_growth_membership':None,'future_growth_score':None,'confidence':None,'fake_data':False}
        try:
            status,body,data=fn(u,t); feats=data.get('features'); err=data.get('error'); digest=hashlib.sha256(body).hexdigest()
            if status!=200 or err is not None or not isinstance(feats,list):
                fail+=1; out.append({**base,'http_status':status,'byte_count':len(body),'content_sha256':digest,'feature_count':None,'features':[],'data_status':'SOURCE_QUERY_ERROR','error':str(err or 'missing features')[:500]}); continue
            clean=[]
            for f in feats[:5]:
                a=f.get('attributes',{}) if isinstance(f,dict) else {}
                clean.append({'attributes':{str(k):v if v is None or isinstance(v,(bool,int,float)) else str(v)[:1024] for k,v in a.items() if str(k).lower() in FIELDS.split(',')}})
            ok+=1; zero+=len(feats)==0
            out.append({**base,'http_status':status,'byte_count':len(body),'content_sha256':digest,'feature_count':len(feats),'features':clean,'exceeded_transfer_limit':bool(data.get('exceededTransferLimit',False)),'data_status':'VERIFIED_ZERO_FEATURE_AT_ANCHOR_POINT' if not feats else 'VERIFIED_FEATURES_AT_ANCHOR_POINT_NOT_PARCEL_BOUND','error':None})
        except Exception as e:
            fail+=1; out.append({**base,'http_status':None,'byte_count':0,'content_sha256':None,'feature_count':None,'features':[],'data_status':'SOURCE_READ_FAILED','error':f'{type(e).__name__}:{str(e)[:500]}'})
    state='PUBLISHED' if fail==0 else 'NO_DATA_CONTINUE'
    return {'schema_version':3,'architecture_version':3,'workstream_id':WS,'slot_id':SLOT,'task_continuation_key':key,'source_continuation_key':SRC_KEY,'state':state,'panel_status':'PUBLISHED' if state=='PUBLISHED' else 'BİLGİ TOPLANIYOR','generated_at':now(),'completed_count':len(out),'target_count':3,'progress_percent':round(len(out)/3*100,6),'successful_query_count':ok,'no_feature_count':zero,'source_read_failed_count':fail,'global_business_completed_count':0,'global_business_target_count':30761,'global_progress_percent':0.0,'records':out,'raw_bodies_copied':False,'geometry_copied':False,'membership_inferred':False,'scores_written':False,'large_raw_files_written':False,'fake_data':False}

def fixtures():
    root='https://services.arcgis.com/drifeOPKLpgnJ8Qa/arcgis/rest/services'; specs=[(30762,'parcel_30762','Enfield',-0.0407406,51.6769078,'planning_local_plan_data_10',17),(46142,'parcel_46142','Havering',0.1928191,51.593114,'planning_local_plan_data_16',20),(61522,'parcel_61522','Lambeth',-0.139263,51.4153374,'planning_local_plan_data_22',33)]
    rows=[]; res=[]
    for n,p,l,x,y,s,layer in specs:
        rows.append({'row_no':n,'parcel_id':p,'lpa':l,'lon':x,'lat':y,'service':f'{root}/{s}/FeatureServer','layers':[[layer,'fixture']]}); res.append({'row_no':n,'layer_id':layer,'data_status':'VERIFIED_METADATA','http_status':200,'raw_sha256':'a'*64})
    return {'slot_id':SLOT,'continuation_key':SRC_KEY,'rows':rows},{'slot_id':SLOT,'continuation_key':SRC_KEY,'state':'PUBLISHED','panel_status':'PUBLISHED','fake_data':False,'completed_count':3,'target_count':3,'results':res}

def fake(u,t):
    del t
    feats=[] if 'data_16' in u else [{'attributes':{'objectid':1,'sitename':'fixture'}}]
    data={'features':feats}; body=json.dumps(data,sort_keys=True,separators=(',',':')).encode(); return 200,body,data

def main():
    p=argparse.ArgumentParser(); p.add_argument('--manifest',type=Path); p.add_argument('--metadata-receipt',type=Path); p.add_argument('--output',type=Path,required=True); p.add_argument('--task-continuation-key',required=True); p.add_argument('--timeout-seconds',type=int,default=30); p.add_argument('--self-test',action='store_true'); a=p.parse_args()
    if not 5<=a.timeout_seconds<=120: raise ValueError('timeout')
    if a.self_test: man,meta=fixtures(); fn=fake
    else:
        if a.manifest is None or a.metadata_receipt is None: raise ValueError('inputs required')
        man,meta,fn=load(a.manifest),load(a.metadata_receipt),fetch
    v=run(man,meta,a.task_continuation_key,a.timeout_seconds,fn); save(a.output,v)
    print(json.dumps({'state':v['state'],'completed_count':v['completed_count'],'target_count':v['target_count'],'successful_query_count':v['successful_query_count'],'source_read_failed_count':v['source_read_failed_count'],'output':str(a.output)},sort_keys=True,separators=(',',':')))
if __name__=='__main__': main()
