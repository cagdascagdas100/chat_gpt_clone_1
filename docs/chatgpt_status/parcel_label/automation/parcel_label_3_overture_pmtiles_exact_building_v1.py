#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,hashlib,json,math,pathlib,struct,tempfile,urllib.request
from datetime import datetime,timezone
from shapely.geometry import Point,Polygon,mapping
from shapely.ops import unary_union

INPUT=pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
OUTPUTS=[pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/overture_pmtiles_exact_building_result_latest.json'),pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/overture_pmtiles_exact_building_latest.json')]
RELEASE='2026-06-17.0'; ZOOM=14
URL=f'https://overturemaps-extras-us-west-2.s3.us-west-2.amazonaws.com/tiles/{RELEASE}/buildings.pmtiles'
DOC='https://docs.overturemaps.org/examples/overture-tiles/'; BUILD='https://docs.overturemaps.org/guides/buildings/'; REL='https://docs.overturemaps.org/blog/2026/06/17/release-notes/'; ATTR='https://docs.overturemaps.org/attribution/'; SPEC='https://github.com/protomaps/PMTiles/blob/master/spec/v3/spec.md'; LIC='https://opendatacommons.org/licenses/odbl/1-0/'
MAX=16*1024*1024

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(b): return hashlib.sha256(b).hexdigest()
def write(p,t):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as f:f.write(t); q=pathlib.Path(f.name)
 q.replace(p)
def rows():
 a=json.loads(INPUT.read_text())['records']; req={'parcel_id','UPRN','FULLADDRESS','longitude','latitude'}
 if len(a)!=3: raise RuntimeError(f'EXPECTED_3_ROWS:{len(a)}')
 out=[]
 for r in a:
  miss=req-set(r)
  if miss or not r.get('exact_uprn_bound'): raise RuntimeError(f'INVALID_INPUT:{r.get("parcel_id")}:{sorted(miss)}')
  out.append({'parcel_id':str(r['parcel_id']),'UPRN':str(r['UPRN']),'FULLADDRESS':str(r['FULLADDRESS']),'longitude':float(r['longitude']),'latitude':float(r['latitude']),'exact_uprn_bound':True})
 return out
def zxy(lon,lat,z=ZOOM):
 n=1<<z; lat=max(-85.05112878,min(85.05112878,lat)); return int((lon+180)/360*n),int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
def tileid(z,x,y):
 acc=((1<<(2*z))-1)//3; n=1<<z; d=0; s=n>>1
 while s:
  rx=1 if x&s else 0; ry=1 if y&s else 0; d+=s*s*((3*rx)^ry)
  if not ry:
   if rx:x=n-1-x;y=n-1-y
   x,y=y,x
  s>>=1
 return acc+d
def vi(b,p=0):
 v=s=0
 while True:
  if p>=len(b) or s>63: raise RuntimeError('INVALID_VARINT')
  c=b[p];p+=1;v|=(c&127)<<s
  if c<128:return v,p
  s+=7
def zz(v): return (v>>1)^-(v&1)
def ungzip(b,c,label):
 if c==1:return b
 if c==2:return gzip.decompress(b)
 raise RuntimeError(f'UNSUPPORTED_{label}_COMPRESSION:{c}')
def directory(raw,c):
 b=ungzip(raw,c,'DIRECTORY');n,p=vi(b);ids=[];last=0
 for _ in range(n):d,p=vi(b,p);last+=d;ids.append(last)
 run=[]
 for _ in range(n):v,p=vi(b,p);run.append(v)
 ln=[]
 for _ in range(n):v,p=vi(b,p);ln.append(v)
 off=[];nxt=0
 for i in range(n):v,p=vi(b,p);o=nxt if i and v==0 else v-1;off.append(o);nxt=o+ln[i]
 return [{'tile_id':ids[i],'run':run[i],'length':ln[i],'offset':off[i]} for i in range(n)]
def entry(es,t):
 lo=0;hi=len(es)-1;best=None
 while lo<=hi:
  m=(lo+hi)//2
  if es[m]['tile_id']<=t:best=es[m];lo=m+1
  else:hi=m-1
 return best if best and (best['run']==0 or t<best['tile_id']+best['run']) else None
def fetch(start,length,timeout):
 if length<1 or length>MAX: raise RuntimeError(f'BAD_RANGE:{length}')
 q=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{start+length-1}','User-Agent':'AAYS-parcel-label-3/1.0'})
 with urllib.request.urlopen(q,timeout=timeout) as r:
  b=r.read(MAX+1); status=int(getattr(r,'status',200))
  if len(b)!=length or status not in (200,206): raise RuntimeError(f'RANGE_FAILED:{status}:{len(b)}:{length}')
  return b,{'start':start,'length':length,'http_status':status,'content_range':r.headers.get('Content-Range'),'content_sha256':sha(b)}
def header(b):
 if len(b)!=127 or b[:7]!=b'PMTiles' or b[7]!=3: raise RuntimeError('INVALID_PMTILES_V3_HEADER')
 u=lambda o:struct.unpack_from('<Q',b,o)[0]
 return {'root_offset':u(8),'root_length':u(16),'leaf_offset':u(40),'tile_data_offset':u(56),'internal_compression':b[97],'tile_compression':b[98],'tile_type':b[99],'min_zoom':b[100],'max_zoom':b[101]}
def gettile(z,x,y,timeout):
 t=tileid(z,x,y); ev={'url':URL,'z':z,'x':x,'y':y,'tile_id':t,'ranges':[]}
 b,r=fetch(0,127,timeout);ev['ranges'].append({'kind':'header',**r});h=header(b);ev['header']=h
 if h['tile_type']!=1 or not h['min_zoom']<=z<=h['max_zoom']: raise RuntimeError('PMTILES_HEADER_REJECTED')
 b,r=fetch(h['root_offset'],h['root_length'],timeout);ev['ranges'].append({'kind':'root',**r});e=entry(directory(b,h['internal_compression']),t);depth=0
 while e and e['run']==0:
  depth+=1
  if depth>4:raise RuntimeError('DIRECTORY_DEPTH')
  b,r=fetch(h['leaf_offset']+e['offset'],e['length'],timeout);ev['ranges'].append({'kind':f'leaf_{depth}',**r});e=entry(directory(b,h['internal_compression']),t)
 if not e:raise RuntimeError('TILE_NOT_FOUND')
 b,r=fetch(h['tile_data_offset']+e['offset'],e['length'],timeout);ev['ranges'].append({'kind':'tile',**r});tile=ungzip(b,h['tile_compression'],'TILE')
 if len(tile)>MAX:raise RuntimeError('TILE_TOO_LARGE')
 ev['tile_decompressed_bytes']=len(tile);ev['tile_decompressed_sha256']=sha(tile);return tile,ev
def fields(b):
 p=0
 while p<len(b):
  k,p=vi(b,p);f=k>>3;w=k&7
  if w==0:v,p=vi(b,p)
  elif w==2:n,p=vi(b,p);v=b[p:p+n];p+=n
  elif w==1:v=b[p:p+8];p+=8
  elif w==5:v=b[p:p+4];p+=4
  else:raise RuntimeError(f'WIRE:{w}')
  yield f,w,v
def packed(b):
 out=[];p=0
 while p<len(b):v,p=vi(b,p);out.append(v)
 return out
def feature(b):
 i=None;t=0;g=[]
 for f,w,v in fields(b):
  if f==1 and w==0:i=v
  elif f==3 and w==0:t=v
  elif f==4 and w==2:g+=packed(v)
 return i,t,g
def layer(b):
 name='';extent=4096;fs=[]
 for f,w,v in fields(b):
  if f==1 and w==2:name=v.decode(errors='replace')
  elif f==2 and w==2:fs.append(feature(v))
  elif f==5 and w==0:extent=v
 return name,extent,fs
def ll(px,py,z,x,y,e):
 n=1<<z;wx=(x+px/e)/n;wy=(y+py/e)/n;return wx*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*wy))))
def polygon(cmd,z,x,y,e):
 p=cx=cy=0;rings=[];cur=[]
 while p<len(cmd):
  c=cmd[p];p+=1;op=c&7;n=c>>3
  if op in (1,2):
   for _ in range(n):cx+=zz(cmd[p]);cy+=zz(cmd[p+1]);p+=2;cur=[(cx,cy)] if op==1 else cur+[(cx,cy)]
  elif op==7:
   if cur:
    if cur[0]!=cur[-1]:cur.append(cur[0])
    rings.append(cur);cur=[]
  else:raise RuntimeError(f'GEOM_CMD:{op}')
 ext=None;holes=[];polys=[]
 for r in rings:
  area=sum(r[i][0]*r[i+1][1]-r[i+1][0]*r[i][1] for i in range(len(r)-1))/2;geo=[ll(a,b,z,x,y,e) for a,b in r]
  if area>0:
   if ext:polys.append(Polygon(ext,holes))
   ext=geo;holes=[]
  elif ext:holes.append(geo)
 if ext:polys.append(Polygon(ext,holes))
 clean=[]
 for q in polys:
  if not q.is_valid:q=q.buffer(0)
  if not q.is_empty:clean.append(q)
 return unary_union(clean) if clean else None
def mvt(b,z,x,y):
 out=[]
 for f,w,v in fields(b):
  if f!=3 or w!=2:continue
  name,e,fs=layer(v)
  if name not in ('building','buildings'):continue
  for idx,(fid,t,g) in enumerate(fs,1):
   if t==3:
    q=polygon(g,z,x,y,e)
    if q is not None and not q.is_empty:out.append({'id':fid,'geometry':q,'layer':name,'feature_index':idx})
 return out
def match(fs,rs):
 cand={r['UPRN']:[] for r in rs}
 for f in fs:
  obj=mapping(f['geometry']);h=sha(json.dumps(obj,separators=(',',':'),sort_keys=True).encode())
  for r in rs:
   if len(cand[r['UPRN']])<=1 and f['geometry'].covers(Point(r['longitude'],r['latitude'])):cand[r['UPRN']].append({'overture_id':f['id'],'layer':f['layer'],'feature_index':f['feature_index'],'geometry':obj,'geometry_sha256':h,'area_degrees2':round(float(f['geometry'].area),12)})
 out=[];matched=0
 for r in rs:
  c=cand[r['UPRN']];d={**r,'candidate_count':len(c),'source_url':URL,'overture_release':RELEASE,'inferred':False}
  if len(c)==1:d.update({'state':'MATCHED_UNIQUE_POINT_CONTAINING_OVERTURE_PMTILES_BUILDING',**c[0]});matched+=1
  elif len(c)>1:d.update({'state':'NO_DATA','reason':'AMBIGUOUS_MULTIPLE_POINT_CONTAINING_OVERTURE_PMTILES_BUILDINGS'})
  else:d.update({'state':'NO_DATA','reason':'NO_POINT_CONTAINING_OVERTURE_PMTILES_BUILDING'})
  out.append(d)
 return out,matched
def enc(v):
 o=bytearray()
 while 1:
  c=v&127;v>>=7;o.append(c|128 if v else c)
  if not v:return bytes(o)
def fld(n,w,v):
 k=enc(n<<3|w)
 if w==0:return k+enc(v)
 return k+enc(len(v))+v
def syn(rs,x,y):
 extent=4096;msgs=[]
 for i,r in enumerate(rs,1):
  n=1<<ZOOM;wx=(r['longitude']+180)/360*n;wy=(1-math.asinh(math.tan(math.radians(r['latitude'])))/math.pi)/2*n;cx=round((wx-x)*extent);cy=round((wy-y)*extent);ring=[(cx-6,cy-6),(cx+6,cy-6),(cx+6,cy+6),(cx-6,cy+6)];cmd=[9];px=py=0
  for j,(a,b) in enumerate(ring):
   if j==1:cmd.append(26)
   cmd+=[(a-px)<<1 if a>=px else ((px-a)<<1)-1,(b-py)<<1 if b>=py else ((py-b)<<1)-1];px,py=a,b
  cmd.append(15);g=b''.join(enc(v) for v in cmd);msgs.append(fld(2,2,fld(1,0,i)+fld(3,0,3)+fld(4,2,g)))
 return fld(3,2,fld(15,0,2)+fld(1,2,b'buildings')+b''.join(msgs)+fld(5,0,extent))
def synthetic(rs,x,y):
 b=syn(rs,x,y);fs=mvt(b,ZOOM,x,y);out,n=match(fs,rs)
 if n!=3 or any(r['candidate_count']!=1 for r in out):raise RuntimeError('SYNTHETIC_MVT_FAILED')
 if [tileid(1,0,0),tileid(1,0,1),tileid(1,1,1),tileid(1,1,0)]!=[1,2,3,4]:raise RuntimeError('HILBERT_FAILED')
 return {'tile':[ZOOM,x,y],'tile_id':tileid(ZOOM,x,y),'synthetic_features':len(fs),'matched':n,'candidate_counts':[1,1,1],'mvt_sha256':sha(b)}
def main():
 a=argparse.ArgumentParser();a.add_argument('--timeout',type=int,default=20);a.add_argument('--validate-only',action='store_true');a.add_argument('--synthetic-test',action='store_true');o=a.parse_args();rs=rows();tiles={zxy(r['longitude'],r['latitude']) for r in rs}
 if len(tiles)!=1:raise RuntimeError(f'TARGETS_NOT_ONE_TILE:{tiles}')
 x,y=next(iter(tiles));tid=tileid(ZOOM,x,y)
 if o.validate_only:print(json.dumps({'valid':True,'input_count':3,'resource_class':'geometry','pmtiles_url':URL,'release':RELEASE,'tile':[ZOOM,x,y],'tile_id':tid,'write_paths':[str(p) for p in OUTPUTS],'max_range_bytes':MAX},sort_keys=True));return 0
 if o.synthetic_test:print(json.dumps(synthetic(rs,x,y),sort_keys=True));return 0
 ev={'documentation_url':DOC,'buildings_url':BUILD,'release_url':REL,'attribution_url':ATTR,'pmtiles_spec_url':SPEC,'license_url':LIC,'pmtiles_url':URL,'release':RELEASE,'accessed_at':now(),'tile':[ZOOM,x,y],'tile_id':tid};rec=[];n=0
 try:b,ev['pmtiles_read']=gettile(ZOOM,x,y,max(1,o.timeout));fs=mvt(b,ZOOM,x,y);ev['features_scanned']=len(fs);rec,n=match(fs,rs)
 except Exception as e:
  ev['error']=f'{type(e).__name__}:{e}';rec=[{**r,'candidate_count':0,'source_url':URL,'overture_release':RELEASE,'state':'NO_DATA','reason':ev['error'],'inferred':False} for r in rs]
 state='PUBLISHED' if n else 'NO_DATA_CONTINUE';res={'schema_version':1,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':'parcel_label_3','task_id':'parcel-label-3-overture-pmtiles-exact-building-v1-20260803','state':state,'panel_status':'PUBLISHED','completed_count':len(rec),'target_count':3,'previous_percent':0.0,'progress_percent':round(len(rec)/3*100,6),'percent_increase':round(len(rec)/3*100,6),'matched_exact_building_rows':n,'evidence_records':len(rec),'source_evidence':ev,'records':rec,'large_raw_files_committed':False,'fake_data':False,'generated_at':now()};t=json.dumps(res,ensure_ascii=False,separators=(',',':'),sort_keys=True)+'\n'
 for p in OUTPUTS:write(p,t)
 print(json.dumps({'completed_count':len(rec),'target_count':3,'matched_exact_building_rows':n,'state':state,'output_sha256':sha(t.encode())},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
