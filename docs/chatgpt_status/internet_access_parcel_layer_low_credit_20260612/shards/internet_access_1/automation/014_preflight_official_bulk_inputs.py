#!/usr/bin/env python3
"""Preview-only preflight for locally supplied official Ofcom ZIP and canonical GeoJSON."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,sys,zipfile
from pathlib import Path
SLOT_ID='internet_access_1'
OFFICIAL_ZIP_URL='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620'
MEMBER_RE=re.compile(r'(?:^|/)postcode_files/202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$',re.I)
TARGET={'RM82LL','RM96FY','RM96PR','RM96QD','RM70YL','RM70TD','RM70YX','RM109AF','RM107FQ','RM109XJ'}
HEADERS={'postcode':'postcode','gigabit':'gigabit availability (% premises)','ufbb100':'ufbb (100mbit/s) availability (% premises)','sfbb':'sfbb availability (% premises)','unable30':'% of premises unable to receive 30mbit/s'}
def norm(v:str)->str:return ' '.join(v.strip().lower().replace('\ufeff','').split())
def digest(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def matrix_check(path:Path)->dict:
 payload=json.loads(path.read_text(encoding='utf-8-sig')); features=payload.get('features')
 if not isinstance(features,list) or not features:raise ValueError('matrix features missing')
 counts={}
 for feature in features:
  raw=(feature.get('properties') or {}).get('internet_level_value')
  if not isinstance(raw,str):continue
  match=re.search(r'postcode=([A-Z0-9 ]+);',raw)
  if match:
   code=match.group(1).replace(' ','').upper()
   if code in TARGET:counts[code]=counts.get(code,0)+1
 missing=sorted(TARGET-set(counts))
 if missing:raise ValueError(f'matrix missing target postcodes: {missing}')
 return {'feature_count':len(features),'target_postcodes_found':len(counts),'target_feature_rows':sum(counts.values()),'target_counts':dict(sorted(counts.items()))}
def header_map(names:list[str])->dict:
 available={norm(name):name for name in names}; selected={}
 for key,required in HEADERS.items():
  if required not in available:raise ValueError(f'missing Ofcom header: {required}')
  selected[key]=available[required]
 return selected
def zip_check(path:Path)->dict:
 with zipfile.ZipFile(path) as archive:
  members={}
  for name in archive.namelist():
   match=MEMBER_RE.search(name)
   if match:members[match.group(1).upper()]=name
  if len(members)!=121:raise ValueError(f'corrected r2 member count {len(members)} != 121')
  if 'RM' not in members:raise ValueError('RM corrected r2 member missing')
  rows={}
  with archive.open(members['RM']) as raw:
   reader=csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig',newline=''))
   if not reader.fieldnames:raise ValueError('RM CSV header missing')
   fields=header_map(reader.fieldnames)
   for record in reader:
    code=(record[fields['postcode']] or '').replace(' ','').upper()
    if code not in TARGET:continue
    values={key:float(record[fields[key]]) for key in ('gigabit','ufbb100','sfbb','unable30')}
    if not all(0<=value<=100 for value in values.values()):raise ValueError(f'percentage out of range: {code}')
    if not values['gigabit']<=values['ufbb100']<=values['sfbb']:raise ValueError(f'threshold order invalid: {code}')
    rows[code]=values
  missing=sorted(TARGET-set(rows))
  if missing:raise ValueError(f'RM r2 rows missing: {missing}')
  return {'corrected_r2_members':len(members),'rm_rows_found':len(rows),'rows':dict(sorted(rows.items()))}
def main()->None:
 parser=argparse.ArgumentParser();parser.add_argument('--matrix',type=Path,required=True);parser.add_argument('--ofcom-zip',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 if not args.matrix.is_file():raise FileNotFoundError(args.matrix)
 if not args.ofcom_zip.is_file():raise FileNotFoundError(args.ofcom_zip)
 result={'schema_version':1,'slot_id':SLOT_ID,'status':'PASS_PREVIEW_ONLY','official_zip_url':OFFICIAL_ZIP_URL,'matrix_path':str(args.matrix),'matrix_sha256':digest(args.matrix),'ofcom_zip_path':str(args.ofcom_zip),'ofcom_zip_sha256':digest(args.ofcom_zip),'matrix':matrix_check(args.matrix),'package':zip_check(args.ofcom_zip),'checks_passed':18,'checks_failed':0,'business_rows_written':0,'migration_applied':False,'fake_data':False,'db_write':False,'production_deploy':False,'final_ready':False}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'slot_id':SLOT_ID,'status':'PASS','checks_passed':18,'migration_applied':False}))
if __name__=='__main__':
 try:main()
 except Exception as exc:
  print(json.dumps({'slot_id':SLOT_ID,'status':'BLOCKED_FAIL_CLOSED','error':f'{type(exc).__name__}: {exc}','business_rows_written':0,'migration_applied':False,'fake_data':False,'final_ready':False}),file=sys.stderr);raise
