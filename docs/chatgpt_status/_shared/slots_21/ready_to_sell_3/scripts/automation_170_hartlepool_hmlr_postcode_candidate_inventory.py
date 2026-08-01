#!/usr/bin/env python3
import argparse,hashlib,io,json,math,re,sys,urllib.parse,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET
SLOT='ready_to_sell_3'; CONT='6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a'; CID='rts3-1509-eton'
INDEX='https://use-land-property-data.service.gov.uk/datasets/inspire/download'; PCURL='https://api.postcodes.io/postcodes/TS255SG'; LA='Hartlepool Borough Council'; R=125.0
OUT=Path('docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/automation_170_hartlepool_hmlr_postcode_candidate_inventory_latest.json')
def H(b):return hashlib.sha256(b).hexdigest()
def N(t):return t.rsplit('}',1)[-1].lower()
def get(u,t):
 try:
  q=urllib.request.Request(u,headers={'User-Agent':'AAYS-ready-to-sell-3-hmlr-inventory/1.0','Accept':'*/*'})
  with urllib.request.urlopen(q,timeout=t) as r:return getattr(r,'status',200),r.read(),r.headers.get('Content-Type'),None,r.geturl()
 except Exception as e:return None,b'',None,f'{type(e).__name__}:{e}',u
def href(b):
 s=b.decode(errors='replace'); m=re.search(re.escape(LA),s,re.I)
 if not m:return None
 z=s[max(0,m.start()-600):m.end()+600]; q=re.findall(r'href=["\']([^"\']+\.zip)["\']',z,re.I)
 return urllib.parse.urljoin(INDEX,q[0]) if q else INDEX+'/Hartlepool_Borough_Council.zip'
def postcode(b):
 x=json.loads(b); r=x.get('result') or {}
 if x.get('status')!=200 or str(r.get('postcode','')).replace(' ','').upper()!='TS255SG' or not isinstance(r.get('eastings'),int) or not isinstance(r.get('northings'),int):raise ValueError('invalid postcode lookup')
 return {k:r.get(k) for k in ('postcode','quality','eastings','northings','latitude','longitude','admin_district')}
def txt(e,names):
 for x in e.iter():
  if N(x.tag) in names and (x.text or '').strip():return re.sub(r'\s+',' ',x.text.strip())
def rings(e):
 out=[]
 for x in e.iter():
  if N(x.tag)!='poslist' or not (x.text or '').strip():continue
  try:v=[float(a) for a in x.text.split()];d=int(x.attrib.get('srsDimension','2'))
  except:continue
  p=[(v[i],v[i+1]) for i in range(0,len(v)-1,d)]
  if len(p)>=3:out.append(p)
 return out
def inside(x,y,p):
 c=False;j=len(p)-1
 for i,(a,b) in enumerate(p):
  d,e=p[j]
  if ((b>y)!=(e>y)) and x<(d-a)*(y-b)/((e-b) or 1e-12)+a:c=not c
  j=i
 return c
def dist(x,y,p):
 xs=[a for a,_ in p];ys=[b for _,b in p];dx=max(min(xs)-x,0,x-max(xs));dy=max(min(ys)-y,0,y-max(ys));return math.hypot(dx,dy)
def scan(g,x,y):
 a=[];n=0
 for _,e in ET.iterparse(io.BytesIO(g),events=('end',)):
  if N(e.tag)!='cadastralparcel':continue
  n+=1; rr=rings(e)
  if rr:
   c=any(inside(x,y,p) for p in rr);d=min(dist(x,y,p) for p in rr)
   if c or d<=R:a.append({'inspire_id':txt(e,{'inspireid','localid'}),'national_cadastral_reference':txt(e,{'nationalcadastralreference'}),'centroid_contained':c,'bbox_distance_metres':round(d,3),'ring_count':len(rr)})
  e.clear()
 a.sort(key=lambda z:(not z['centroid_contained'],z['bbox_distance_metres'],z.get('inspire_id') or ''))
 return {'features_scanned':n,'nearby_candidate_count':len(a),'centroid_containing_count':sum(z['centroid_contained'] for z in a),'nearby_candidates':a[:50]}
def rec(stage,u,s,b,ct,er,ru):
 q=b if b else (er or '').encode();return {'stage':stage,'url':u,'resolved_url':ru,'http_status':s,'content_type':ct,'byte_count':len(b),'content_sha256':H(q),'sha256_basis':'raw_response_bytes' if b else 'bounded_error_evidence_string','error':er}
def run(t):
 A=[];C={'postcode_centroid_resolved':False,'hmlr_hartlepool_download_link_resolved':False,'hmlr_zip_gml_verified':False,'nearby_polygon_inventory_completed':False};P=U=Z=G=S=None
 s,b,ct,e,r=get(PCURL,t);q=rec('postcodes_io_bng_centroid',PCURL,s,b,ct,e,r)
 if b:
  try:P=postcode(b);q['parsed']=P;C['postcode_centroid_resolved']=True
  except Exception as x:q['parse_error']=f'{type(x).__name__}:{x}'
 A.append(q);s,b,ct,e,r=get(INDEX,t);q=rec('hmlr_inspire_download_index',INDEX,s,b,ct,e,r)
 if b:U=href(b);q['hartlepool_download_url']=U;C['hmlr_hartlepool_download_link_resolved']=bool(U)
 A.append(q)
 if U:
  s,b,ct,e,r=get(U,t);q=rec('hmlr_hartlepool_zip',U,s,b,ct,e,r)
  if b:
   try:
    if not b.startswith(b'PK'):raise ValueError('not ZIP')
    Z=H(b);z=zipfile.ZipFile(io.BytesIO(b));names=z.namelist();m=next((x for x in names if x.endswith('Land_Registry_Cadastral_Parcels.gml')),None) or (next((x for x in names if x.lower().endswith('.gml')),None) if sum(x.lower().endswith('.gml') for x in names)==1 else None)
    if not m:raise ValueError('GML member missing')
    g=z.read(m);G=H(g);q.update({'zip_sha256':Z,'gml_member':m,'gml_byte_count':len(g),'gml_sha256':G});C['hmlr_zip_gml_verified']=True
    if P:S=scan(g,P['eastings'],P['northings']);C['nearby_polygon_inventory_completed']=S['features_scanned']>0
   except Exception as x:q['parse_error']=f'{type(x).__name__}:{x}'
  A.append(q)
 else:A.append({'stage':'hmlr_hartlepool_zip','attempted':False,'reason':'download URL unresolved'})
 done=sum(C.values());cnt=S['nearby_candidate_count'] if S else 0;state='CANDIDATE_SET_READY' if done==4 and cnt>0 else 'NO_DATA_CONTINUE'
 return {'schema_version':3,'slot_id':SLOT,'continuation_key':CONT,'candidate_id':CID,'generated_at':datetime.now(timezone.utc).isoformat(),'state':state,'panel_status':'BİLGİ TOPLANIYOR' if state=='CANDIDATE_SET_READY' else 'BLOCKED','completed_count':done,'target_count':4,'progress_percent':done/4*100,'checks':C,'postcode_centroid':P,'hmlr_download_url':U,'hmlr_zip_sha256':Z,'hmlr_gml_sha256':G,'inventory':S,'parcel_matches':0,'geometry_matches':0,'promotion_allowed':False,'no_inference':True,'no_data_reason':None if state=='CANDIDATE_SET_READY' else 'Official postcode-centroid and HMLR ZIP/GML inventory gates did not all complete or produced no nearby polygons; no exact address-to-parcel binding was inferred.','attempts':A,'fake_data':False}
def test():
 assert href(b'<td>Hartlepool Borough Council</td><a href="/datasets/inspire/download/Hartlepool_Borough_Council.zip">Download .gml</a>').endswith('Hartlepool_Borough_Council.zip')
 p=postcode(b'{"status":200,"result":{"postcode":"TS25 5SG","quality":1,"eastings":450500,"northings":531440}}')
 g=b'<r xmlns:c="x" xmlns:g="http://www.opengis.net/gml/3.2"><c:CadastralParcel><c:inspireId>HP-1</c:inspireId><g:posList srsDimension="2">450490 531430 450510 531430 450510 531450 450490 531450 450490 531430</g:posList></c:CadastralParcel><c:CadastralParcel><c:inspireId>HP-2</c:inspireId><g:posList srsDimension="2">451000 532000 451010 532000 451010 532010 451000 532010 451000 532000</g:posList></c:CadastralParcel></r>'
 s=scan(g,p['eastings'],p['northings']);assert s['features_scanned']==2 and s['nearby_candidate_count']==1 and s['centroid_containing_count']==1;print('SELF_TEST_PASS')
def main():
 p=argparse.ArgumentParser();p.add_argument('--output');p.add_argument('--timeout-seconds',type=int,default=60);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if a.self_test:return test()
 if not a.output or Path(a.output)!=OUT:raise SystemExit('output path outside exact_write_paths')
 r=run(a.timeout_seconds);OUT.parent.mkdir(parents=True,exist_ok=True);q=OUT.with_suffix('.json.tmp');q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');q.replace(OUT)
if __name__=='__main__':sys.exit(main())
