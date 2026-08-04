#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from typing import Any
from shapely.geometry import Point, shape

INPUT=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
MANIFEST=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/planning_data_conservation_area_point_containment_source_manifest_20260804.json')
OUTPUTS=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/planning_data_conservation_area_point_containment_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/planning_data_conservation_area_point_containment_latest.json')]
API='https://www.planning.data.gov.uk/entity.geojson'
HOST='www.planning.data.gov.uk'
MAX_RESPONSE=8*1024*1024

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(b:bytes): return hashlib.sha256(b).hexdigest()
def cjson(v:Any): return json.dumps(v,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def atomic(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as h:
        h.write(text); tmp=pathlib.Path(h.name)
    tmp.replace(path)
def safe(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or (p.hostname or '').casefold()!=HOST or p.username or p.password or p.fragment: raise RuntimeError('UNSAFE_URL')
    return url
def fetch(url,timeout):
    safe(url)
    req=urllib.request.Request(url,headers={'User-Agent':'AAYS-parcel-label-3/1.0','Accept':'application/geo+json,application/json;q=0.9'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        final=r.geturl(); safe(final); body=r.read(MAX_RESPONSE+1)
        if len(body)>MAX_RESPONSE: raise RuntimeError('RESPONSE_TOO_LARGE')
        return body,final,int(getattr(r,'status',200))
def manifest():
    p=json.loads(MANIFEST.read_text())
    if p.get('api_url')!=API or len(p.get('target_uprns',[]))!=3: raise RuntimeError('BAD_MANIFEST')
    for s in p.get('sources',[]):
        e=s.get('retained_excerpt','')
        if not e or sha(e.encode())!=s.get('retained_excerpt_sha256'): raise RuntimeError('MANIFEST_EXCERPT_SHA_MISMATCH')
    return p
def rows():
    p=json.loads(INPUT.read_text()); recs=p.get('records',[]); m=manifest(); targets=set(m['target_uprns'])
    if len(recs)!=3: raise RuntimeError('EXPECTED_3_ROWS')
    out=[]
    for r in recs:
        keys=('parcel_id','UPRN','FULLADDRESS','POSTCODE','longitude','latitude')
        if not r.get('exact_uprn_bound') or any(k not in r for k in keys): raise RuntimeError('INVALID_ROW')
        x={k:r[k] for k in keys}; x['UPRN']=str(x['UPRN']); x['exact_uprn_bound']=True
        if x['UPRN'] not in targets: raise RuntimeError('UPRN_NOT_IN_MANIFEST')
        out.append(x)
    if len({r['UPRN'] for r in out})!=3: raise RuntimeError('DUP_UPRN')
    return out
def url_for(r):
    return API+'?'+urllib.parse.urlencode({'latitude':f"{float(r['latitude']):.12f}",'longitude':f"{float(r['longitude']):.12f}",'dataset':'conservation-area','limit':'50'})
def parse(body,r):
    p=json.loads(body)
    if p.get('type')!='FeatureCollection' or not isinstance(p.get('features'),list): raise RuntimeError('NOT_FEATURE_COLLECTION')
    pt=Point(float(r['longitude']),float(r['latitude'])); cand=[]
    for f in p['features']:
        if not isinstance(f,dict) or not f.get('geometry'): continue
        prop=f.get('properties') if isinstance(f.get('properties'),dict) else {}
        if prop.get('dataset')!='conservation-area': continue
        g=shape(f['geometry'])
        if g.geom_type not in {'Polygon','MultiPolygon'} or g.is_empty: continue
        if not g.is_valid: g=g.buffer(0)
        if g.is_empty or not g.covers(pt): continue
        cand.append({'entity':prop.get('entity'),'reference':prop.get('reference'),'name':prop.get('name'),'quality':prop.get('quality'),'organisation_curie':prop.get('organisation-curie'),'geometry_sha256':sha(cjson(f['geometry']).encode()),'properties_sha256':sha(cjson(prop).encode())})
    return cand,len(p['features'])
def synthetic_body(r,i,amb=False):
    lon=float(r['longitude']); lat=float(r['latitude']); d=.00008
    def feat(n,off=0):
        x=lon+off;y=lat+off; ring=[[x-d,y-d],[x+d,y-d],[x+d,y+d],[x-d,y+d],[x-d,y-d]]
        return {'type':'Feature','properties':{'dataset':'conservation-area','entity':990000+i+n,'reference':f'CA-{i}-{n}','name':f'Synthetic conservation area {i}','quality':'authoritative','organisation-curie':'local-authority:LAM'},'geometry':{'type':'Polygon','coordinates':[ring]}}
    fs=[feat(1)]
    if amb: fs.append(feat(2,.00001))
    return cjson({'type':'FeatureCollection','features':fs}).encode()
def run(rs,timeout,synthetic=False,ambiguous=False):
    ev={'accessed_at':now(),'api_url':API,'request_count':0,'requests':[]}; out=[]; matched=0
    for i,r in enumerate(rs,1):
        u=url_for(r); ev['request_count']+=1
        try:
            if synthetic: body=synthetic_body(r,i,ambiguous and i==2); final=u; status=200
            else: body,final,status=fetch(u,timeout)
            cs,total=parse(body,r); valid=[c for c in cs if c.get('quality')=='authoritative' and str(c.get('organisation_curie') or '').startswith('local-authority:')]
            ev['requests'].append({'UPRN':r['UPRN'],'request_url':u,'final_url':final,'http_status':status,'bytes':len(body),'response_sha256':sha(body),'returned_feature_count':total,'covering_candidate_count':len(cs),'authoritative_local_candidate_count':len(valid),'state':'RESPONSE'})
            o={**r,'source_url':final,'candidate_count':len(cs),'authoritative_local_candidate_count':len(valid),'inferred':False}
            if len(cs)==1 and len(valid)==1:
                o.update({'state':'MATCHED_UNIQUE_AUTHORITATIVE_CONSERVATION_AREA','official_conservation_area_designation':True,'official_conservation_area_label':'Conservation area',**valid[0]}); matched+=1
            elif len(cs)>1: o.update({'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_POINT_CONTAINING_CONSERVATION_AREAS'})
            elif len(cs)==1: o.update({'state':'NO_DATA','reason':'POINT_CONTAINING_CONSERVATION_AREA_NOT_AUTHORITATIVE_LOCAL_AUTHORITY'})
            else: o.update({'state':'NO_DATA','reason':'NO_POINT_CONTAINING_CONSERVATION_AREA'})
        except Exception as e:
            err=f'{type(e).__name__}:{e}'; ev['requests'].append({'UPRN':r['UPRN'],'request_url':u,'state':'ERROR','error':err})
            o={**r,'source_url':API,'candidate_count':0,'authoritative_local_candidate_count':0,'state':'NO_DATA','reason':err,'inferred':False}
        out.append(o)
    return ev,out,matched
def main():
    a=argparse.ArgumentParser(); a.add_argument('--timeout',type=int,default=20); a.add_argument('--validate-only',action='store_true'); a.add_argument('--synthetic-test',action='store_true'); a.add_argument('--synthetic-ambiguous-test',action='store_true'); z=a.parse_args()
    if not 1<=z.timeout<=300: raise RuntimeError('INVALID_TIMEOUT')
    rs=rows()
    if z.validate_only:
        print(json.dumps({'valid':True,'input_count':3,'target_uprns':[r['UPRN'] for r in rs],'request_limit':3,'max_response_bytes':MAX_RESPONSE,'resource_class':'network','write_paths':[str(p) for p in OUTPUTS]},sort_keys=True)); return 0
    ev,recs,matched=run(rs,z.timeout,z.synthetic_test or z.synthetic_ambiguous_test,z.synthetic_ambiguous_test)
    if z.synthetic_test:
        if matched!=3: raise RuntimeError(f'SYNTH_UNIQUE_FAILED:{matched}')
        print(json.dumps({'valid':True,'matched_rows':matched},sort_keys=True)); return 0
    if z.synthetic_ambiguous_test:
        if matched!=2 or recs[1].get('reason')!='AMBIGUOUS_MULTIPLE_POINT_CONTAINING_CONSERVATION_AREAS': raise RuntimeError('SYNTH_AMBIG_FAILED')
        print(json.dumps({'valid':True,'matched_rows':matched,'ambiguous_state':recs[1]['state']},sort_keys=True)); return 0
    state='PUBLISHED' if matched else 'NO_DATA_CONTINUE'
    result={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-planning-data-conservation-area-point-containment-v1-20260804','state':state,'panel_status':'PUBLISHED','completed_count':len(recs),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(recs)/3*100,6),'percent_increase':round(len(recs)/3*100,6),'matched_unique_authoritative_conservation_area_rows':matched,'evidence_records':len(recs),'source_evidence':ev,'records':recs,'non_authoritative_promoted':False,'fake_data':False,'generated_at':now()}
    text=cjson(result)+'\n'
    for p in OUTPUTS: atomic(p,text)
    print(json.dumps({'completed_count':len(recs),'target_count':3,'matched_unique_authoritative_conservation_area_rows':matched,'state':state,'output_sha256':sha(text.encode())},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
