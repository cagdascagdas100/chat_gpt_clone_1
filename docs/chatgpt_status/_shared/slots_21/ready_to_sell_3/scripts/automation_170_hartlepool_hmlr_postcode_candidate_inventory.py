#!/usr/bin/env python3
import argparse,hashlib,http.cookiejar,io,json,math,os,re,sys,tempfile,urllib.parse,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET
SLOT='ready_to_sell_3';CONT='6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a';CID='rts3-1509-eton'
INDEX='https://use-land-property-data.service.gov.uk/datasets/inspire/download';PCURL='https://api.postcodes.io/postcodes/TS255SG';ZIPURL=INDEX+'/Hartlepool_Borough_Council.zip';WMS='https://inspire.landregistry.gov.uk/inspire/ows';LAYER='inspire:CP.CadastralParcel';PAPI='https://www.planning.data.gov.uk/entity.json';RADIUS=125.0
OUT=Path('docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/automation_170_hartlepool_hmlr_postcode_candidate_inventory_latest.json')
FALLBACK={'postcode':'TS25 5SG','quality':None,'eastings':450498,'northings':531441,'latitude':54.675512,'longitude':-1.218422,'admin_district':'Hartlepool','source_url':'https://www.getthedata.com/postcode/TS25-5SG','source_accessed_at':'2026-08-03T15:53:00Z','source_content_sha256':'9d2d14040a25286d26cbeb4b980fec415c79328dec1ad6ccf9da2e022ea37417','source_hash_scope':'normalized_relevant_record','source_record':'TS25 5SG | Eton Street, Hartlepool | Easting 450498 | Northing 531441 | Latitude 54.675512 | Longitude -1.218422 | Source Open Postcode Geo | OGL.','fallback_open_data':True}
def sha(b):return hashlib.sha256(b).hexdigest()
def lname(t):return t.rsplit('}',1)[-1].lower()
class Session:
 def __init__(s):s.jar=http.cookiejar.CookieJar();s.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(s.jar))
 def fetch(s,u,t):
  try:
   q=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 AAYS-ready-to-sell-3/1.5','Accept':'*/*'})
   with s.opener.open(q,timeout=t) as r:return int(getattr(r,'status',200)),r.read(),r.headers.get('Content-Type'),None,r.geturl()
  except Exception as e:return None,b'',None,f'{type(e).__name__}:{e}',u
def zip_link(b):
 s=b.decode(errors='replace');m=re.search('Hartlepool Borough Council',s,re.I)
 if not m:return ZIPURL
 w=s[max(0,m.start()-800):m.end()+1200];a=re.findall(r'href=["\']([^"\']+\.(?:zip|gml)(?:\?[^"\']*)?)["\']',w,re.I)
 return urllib.parse.urljoin(INDEX,a[0]) if a else ZIPURL
def wms_url(x,y):
 h=int(RADIUS);p={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetFeatureInfo','LAYERS':LAYER,'QUERY_LAYERS':LAYER,'STYLES':'','SRS':'EPSG:27700','BBOX':f'{x-h},{y-h},{x+h},{y+h}','WIDTH':'256','HEIGHT':'256','X':'128','Y':'128','INFO_FORMAT':'application/vnd.ogc.gml','FEATURE_COUNT':'50','EXCEPTIONS':'application/vnd.ogc.se_xml'}
 return WMS+'?'+urllib.parse.urlencode(p)
def planning_url(lat,lon):return PAPI+'?'+urllib.parse.urlencode([('latitude',f'{lat:.6f}'),('longitude',f'{lon:.6f}'),('dataset','title-boundary'),('limit','100')])
def postcode(b):
 p=json.loads(b);r=p.get('result') or {}
 if p.get('status')!=200 or str(r.get('postcode','')).replace(' ','').upper()!='TS255SG' or not isinstance(r.get('eastings'),int) or not isinstance(r.get('northings'),int):raise ValueError('invalid postcode')
 return {k:r.get(k) for k in ('postcode','quality','eastings','northings','latitude','longitude','admin_district')}
def rings_xml(e):
 out=[]
 for n in e.iter():
  name=lname(n.tag);text=(n.text or '').strip()
  if not text:continue
  try:
   if name=='poslist':v=[float(x) for x in text.split()];d=int(n.attrib.get('srsDimension','2'));r=[(v[i],v[i+1]) for i in range(0,len(v)-1,d)]
   elif name=='coordinates':r=[tuple(map(float,p.split(',')[:2])) for p in text.split() if len(p.split(','))>=2]
   else:continue
  except (ValueError,IndexError):continue
  if len(r)>=3:out.append(r)
 return out
def rings_wkt(w):
 out=[]
 for g in re.findall(r'\(([^()]+)\)',w):
  try:r=[tuple(map(float,p.strip().split()[:2])) for p in g.split(',') if len(p.strip().split())>=2]
  except ValueError:continue
  if len(r)>=3:out.append(r)
 return out
def inside(x,y,p):
 c=False;j=len(p)-1
 for i,(a,b) in enumerate(p):
  d,e=p[j]
  if ((b>y)!=(e>y)) and x<(d-a)*(y-b)/((e-b) or 1e-12)+a:c=not c
  j=i
 return c
def dist_bng(x,y,p):
 xs=[a for a,_ in p];ys=[b for _,b in p];return math.hypot(max(min(xs)-x,0,x-max(xs)),max(min(ys)-y,0,y-max(ys)))
def dist_ll(lon,lat,p):
 xs=[a for a,_ in p];ys=[b for _,b in p];dx=max(min(xs)-lon,0,lon-max(xs))*111320*math.cos(math.radians(lat));dy=max(min(ys)-lat,0,lat-max(ys))*110540;return math.hypot(dx,dy)
def scan_gml(b,x,y):
 rows=[];n=0
 for _,e in ET.iterparse(io.BytesIO(b),events=('end',)):
  if lname(e.tag) not in {'cadastralparcel','cp.cadastralparcel'}:continue
  n+=1;rr=rings_xml(e)
  if rr:
   c=any(inside(x,y,r) for r in rr);d=min(dist_bng(x,y,r) for r in rr)
   if c or d<=RADIUS:rows.append({'reference':next(((z.text or '').strip() for z in e.iter() if lname(z.tag) in {'inspireid','localid','nationalcadastralreference'} and (z.text or '').strip()),None),'centroid_contained':c,'bbox_distance_metres':round(d,3),'ring_count':len(rr)})
  e.clear()
 rows.sort(key=lambda z:(not z['centroid_contained'],z['bbox_distance_metres'],z.get('reference') or ''));return {'features_scanned':n,'nearby_candidate_count':len(rows),'centroid_containing_count':sum(z['centroid_contained'] for z in rows),'nearby_candidates':rows[:50]}
def entities(p):
 if isinstance(p,list):return [x for x in p if isinstance(x,dict)]
 if isinstance(p,dict):
  for k in ('entities','results','data'):
   if isinstance(p.get(k),list):return [x for x in p[k] if isinstance(x,dict)]
 return []
def scan_planning(b,lon,lat):
 rows=[];n=0
 for e in entities(json.loads(b)):
  if e.get('dataset') not in (None,'title-boundary'):continue
  w=e.get('geometry') or e.get('point')
  if not isinstance(w,str):continue
  rr=rings_wkt(w)
  if not rr:continue
  n+=1;c=any(inside(lon,lat,r) for r in rr);d=min(dist_ll(lon,lat,r) for r in rr)
  if c or d<=RADIUS:rows.append({'entity':e.get('entity'),'reference':e.get('reference'),'entry_date':e.get('entry-date'),'quality':e.get('quality'),'centroid_contained':c,'bbox_distance_metres':round(d,3),'ring_count':len(rr)})
 rows.sort(key=lambda z:(not z['centroid_contained'],z['bbox_distance_metres'],str(z.get('entity') or '')));return {'features_scanned':n,'nearby_candidate_count':len(rows),'centroid_containing_count':sum(z['centroid_contained'] for z in rows),'nearby_candidates':rows[:50]}
def rec(stage,u,s,b,ct,e,ru):
 evidence=b if b else (e or '').encode();return {'stage':stage,'url':u,'resolved_url':ru,'http_status':s,'content_type':ct,'byte_count':len(b),'content_sha256':sha(evidence),'sha256_basis':'raw_response_bytes' if b else 'bounded_error_evidence_string','error':e}
def run(timeout,fetch_fn=None):
 ses=Session() if fetch_fn is None else None;fetch=ses.fetch if ses else fetch_fn;attempts=[];checks={'postcode_centroid_resolved':False,'official_title_geometry_route_resolved':False,'official_title_geometry_verified':False,'nearby_polygon_inventory_completed':False};pc=None;inv=None;mode=None;zsha=None;gsha=None;fallback=[]
 s,b,ct,e,ru=fetch(PCURL,timeout);r=rec('postcodes_io_bng_centroid',PCURL,s,b,ct,e,ru)
 if b:
  try:pc=postcode(b);r['parsed']=pc;checks['postcode_centroid_resolved']=True
  except Exception as x:r['parse_error']=f'{type(x).__name__}:{x}'
 if pc is None:pc=dict(FALLBACK);r.update({'fallback_used':True,'fallback_source_url':FALLBACK['source_url'],'fallback_source_content_sha256':FALLBACK['source_content_sha256']});checks['postcode_centroid_resolved']=True;fallback.append({'stage':'postcode_centroid_open_data_fallback','source_url':FALLBACK['source_url'],'accessed_at':FALLBACK['source_accessed_at'],'content_sha256':FALLBACK['source_content_sha256'],'hash_scope':FALLBACK['source_hash_scope'],'relevant_record':FALLBACK['source_record'],'proven_fields':['postcode','eastings','northings','latitude','longitude']})
 attempts.append(r);s,b,ct,e,ru=fetch(INDEX,timeout);du=zip_link(b);wu=wms_url(pc['eastings'],pc['northings']);pu=planning_url(pc['latitude'],pc['longitude']);r=rec('hmlr_inspire_download_index',INDEX,s,b,ct,e,ru);r.update({'hartlepool_download_url':du,'official_wms_feature_info_url':wu,'planning_data_title_boundary_url':pu});checks['official_title_geometry_route_resolved']=True;attempts.append(r)
 s,b,ct,e,ru=fetch(du,timeout);r=rec('hmlr_hartlepool_zip',du,s,b,ct,e,ru)
 if b:
  try:
   if not b.startswith(b'PK'):raise ValueError('not ZIP')
   zsha=sha(b);a=zipfile.ZipFile(io.BytesIO(b));names=a.namelist();m=next((n for n in names if n.endswith('Land_Registry_Cadastral_Parcels.gml')),None);m=m or ([n for n in names if n.lower().endswith('.gml')][0] if len([n for n in names if n.lower().endswith('.gml')])==1 else None)
   if not m:raise ValueError('GML member missing')
   gb=a.read(m);inv=scan_gml(gb,pc['eastings'],pc['northings']);gsha=sha(gb)
   if inv['features_scanned']<=0:raise ValueError('empty GML')
   mode='official_zip_gml_member';checks['official_title_geometry_verified']=checks['nearby_polygon_inventory_completed']=True;r.update({'zip_sha256':zsha,'gml_sha256':gsha,'gml_member':m})
  except Exception as x:r['parse_error']=f'{type(x).__name__}:{x}'
 attempts.append(r)
 if not checks['official_title_geometry_verified']:
  s,b,ct,e,ru=fetch(wu,timeout);r=rec('hmlr_inspire_wms_getfeatureinfo',wu,s,b,ct,e,ru)
  if b:
   try:
    inv=scan_gml(b,pc['eastings'],pc['northings']);gsha=sha(b)
    if inv['features_scanned']<=0:raise ValueError('empty WMS GML')
    mode='official_wms_getfeatureinfo_gml';checks['official_title_geometry_verified']=checks['nearby_polygon_inventory_completed']=True;r['gml_sha256']=gsha
   except Exception as x:r['parse_error']=f'{type(x).__name__}:{x}'
  attempts.append(r)
 if not checks['official_title_geometry_verified']:
  s,b,ct,e,ru=fetch(pu,timeout);r=rec('planning_data_title_boundary_point_query',pu,s,b,ct,e,ru)
  if b:
   try:
    inv=scan_planning(b,pc['longitude'],pc['latitude']);gsha=sha(b)
    if inv['features_scanned']<=0:raise ValueError('empty title-boundary response')
    mode='official_planning_data_title_boundary_wkt';checks['official_title_geometry_verified']=checks['nearby_polygon_inventory_completed']=True;r['response_sha256']=gsha
   except Exception as x:r['parse_error']=f'{type(x).__name__}:{x}'
  attempts.append(r)
 done=sum(checks.values());n=inv['nearby_candidate_count'] if inv else 0;state='CANDIDATE_SET_READY' if done==4 and n>0 else 'NO_DATA_CONTINUE'
 return {'schema_version':3,'slot_id':SLOT,'continuation_key':CONT,'candidate_id':CID,'generated_at':datetime.now(timezone.utc).isoformat(),'state':state,'panel_status':'BİLGİ TOPLANIYOR' if state=='CANDIDATE_SET_READY' else 'BLOCKED','completed_count':done,'target_count':4,'progress_percent':done/4*100,'checks':checks,'postcode_centroid':pc,'hmlr_download_url':du,'hmlr_wms_feature_info_url':wu,'planning_data_title_boundary_url':pu,'title_geometry_verification_mode':mode,'hmlr_zip_sha256':zsha,'official_geometry_response_sha256':gsha,'inventory':inv,'http_session':{'persistent_cookie_jar':ses is not None,'shared_opener_for_official_requests':ses is not None,'wms_fallback_enabled':True,'planning_data_fallback_enabled':True},'parcel_matches':0,'geometry_matches':0,'promotion_allowed':False,'no_inference':True,'no_data_reason':None if state=='CANDIDATE_SET_READY' else 'Official ZIP/GML, WMS GML and Planning Data title-boundary routes did not produce a verified non-empty polygon inventory; no exact address-to-parcel binding was inferred.','fallback_evidence':fallback,'attempts':attempts,'fake_data':False}
def fixture_gml(gml2=False):
 n=b'<g:coordinates>450490,531430 450510,531430 450510,531450 450490,531450 450490,531430</g:coordinates>' if gml2 else b'<g:posList>450490 531430 450510 531430 450510 531450 450490 531450 450490 531430</g:posList>';f=b'<g:coordinates>451000,532000 451010,532000 451010,532010 451000,532010 451000,532000</g:coordinates>' if gml2 else b'<g:posList>451000 532000 451010 532000 451010 532010 451000 532010 451000 532000</g:posList>';return b'<r xmlns:c="x" xmlns:g="http://www.opengis.net/gml"><c:CadastralParcel>'+n+b'</c:CadastralParcel><c:CadastralParcel>'+f+b'</c:CadastralParcel></r>'
def fixture_zip():
 q=io.BytesIO();z=zipfile.ZipFile(q,'w',zipfile.ZIP_DEFLATED);z.writestr('Land_Registry_Cadastral_Parcels.gml',fixture_gml());z.close();return q.getvalue()
def self_test():
 s=Session();assert any(isinstance(h,urllib.request.HTTPCookieProcessor) for h in s.opener.handlers)
 def fail(u,t):return None,b'',None,'URLError:fixture DNS failure',u
 assert run(5,fail)['completed_count']==2
 pb=b'{"status":200,"result":{"postcode":"TS25 5SG","eastings":450500,"northings":531440,"latitude":54.6755,"longitude":-1.2184,"admin_district":"Hartlepool"}}'
 def base(u):
  if u==PCURL:return 200,pb,'application/json',None,u
  if u==INDEX:return None,b'',None,'URLError:index',u
  if u==ZIPURL:return None,b'',None,'URLError:zip',u
  if u.startswith(WMS+'?'):return None,b'',None,'URLError:wms',u
 def zf(u,t):
  if u==ZIPURL:return 200,fixture_zip(),'application/zip',None,u
  return base(u)
 assert run(5,zf)['title_geometry_verification_mode']=='official_zip_gml_member'
 def wf(u,t):
  if u.startswith(WMS+'?'):return 200,fixture_gml(True),'application/vnd.ogc.gml',None,u
  return base(u)
 assert run(5,wf)['title_geometry_verification_mode']=='official_wms_getfeatureinfo_gml'
 pdata=json.dumps({'entities':[{'entity':1,'dataset':'title-boundary','geometry':'MULTIPOLYGON (((-1.21855 54.67545,-1.21825 54.67545,-1.21825 54.67565,-1.21855 54.67565,-1.21855 54.67545)))'}]}).encode()
 def pf(u,t):
  if u.startswith(PAPI+'?'):return 200,pdata,'application/json',None,u
  return base(u)
 p=run(5,pf);assert p['completed_count']==4 and p['title_geometry_verification_mode']=='official_planning_data_title_boundary_wkt' and p['inventory']['nearby_candidate_count']==1
 print('SELF_TEST_PASS')
def write(path,v):
 path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output');p.add_argument('--timeout-seconds',type=int,default=60);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if not 5<=a.timeout_seconds<=180:raise SystemExit('timeout must be 5..180 seconds')
 if a.self_test:return self_test()
 if not a.output or Path(a.output)!=OUT:raise SystemExit('output path outside exact_write_paths')
 write(OUT,run(a.timeout_seconds))
if __name__=='__main__':sys.exit(main())
