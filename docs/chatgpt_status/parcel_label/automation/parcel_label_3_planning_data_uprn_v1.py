#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request

INPUT = pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
OUTPUTS = [
 pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/planning_data_uprn_result_latest.json'),
 pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/planning_data_uprn_latest.json')]
BASE='https://www.planning.data.gov.uk/entity.json'

def atomic(path, text):
 path.parent.mkdir(parents=True, exist_ok=True)
 with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
  f.write(text); tmp=pathlib.Path(f.name)
 tmp.replace(path)

def main():
 p=argparse.ArgumentParser(); p.add_argument('--timeout',type=int,default=10); p.add_argument('--validate-only',action='store_true'); a=p.parse_args()
 if not INPUT.is_file(): raise SystemExit(f'missing input: {INPUT}')
 src=json.loads(INPUT.read_text(encoding='utf-8')); rows=src.get('records',[])
 if len(rows)!=3 or any(not r.get('UPRN') for r in rows): raise SystemExit('expected exactly 3 UPRN rows')
 if a.validate_only:
  print(json.dumps({'valid':True,'input_count':3,'write_paths':[str(x) for x in OUTPUTS]})); return
 out=[]
 for r in rows:
  q=urllib.parse.urlencode([('q',str(r['UPRN'])),('dataset','planning-application'),('limit','10')])
  url=BASE+'?'+q
  rec={'parcel_id':r['parcel_id'],'UPRN':str(r['UPRN']),'FULLADDRESS':r['FULLADDRESS'],'source_url':url}
  try:
   with urllib.request.urlopen(url,timeout=a.timeout) as resp:
    body=resp.read(1048576); rec.update(http_status=resp.status,content_sha256=hashlib.sha256(body).hexdigest())
    data=json.loads(body); entities=data.get('entities',[]) if isinstance(data,dict) else []
    rec['planning_application_count']=len(entities); rec['entities']=entities[:10]
  except Exception as e:
   rec.update(state='NO_DATA',error=f'{type(e).__name__}:{e}',planning_application_count=0,entities=[])
  out.append(rec)
 result={'schema_version':1,'slot_id':'parcel_label_3','source':'Planning Data API','completed_count':len(out),'target_count':3,'progress_percent':100.0,'records':out,'fake_data':False}
 text=json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n'
 for path in OUTPUTS: atomic(path,text)
 print(json.dumps({'completed_count':3,'target_count':3,'output_sha256':hashlib.sha256(text.encode()).hexdigest()}))
if __name__=='__main__': main()
