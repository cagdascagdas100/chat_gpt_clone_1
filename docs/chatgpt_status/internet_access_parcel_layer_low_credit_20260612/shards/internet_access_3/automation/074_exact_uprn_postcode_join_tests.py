#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,sqlite3,tempfile,zipfile
from pathlib import Path

def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);return p.parse_args()
def module():
 p=Path(__file__).parent/'073_exact_uprn_postcode_join.py';s=importlib.util.spec_from_file_location('join',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 m=module();checks=[]
 def ck(n,x):checks.append({'name':n,'passed':bool(x)})
 ck('HEADER_NORMALIZE',m.norm_header('X_COORDINATE')=='XCOORDINATE');ck('UPRN_VALID',m.normalize_uprn(' 123 ')=='123');ck('UPRN_INVALID',m.normalize_uprn('abc') is None);ck('POSTCODE_VALID',m.normalize_postcode('sw1a 1aa')=='SW1A1AA');ck('POSTCODE_INVALID',m.normalize_postcode('bad') is None)
 fm=m.field_map(['UPRN','X_COORDINATE','Y_COORDINATE','LATITUDE','LONGITUDE','PCDS']);ck('FIELD_UPRN',fm['uprn']=='UPRN');ck('FIELD_X',fm['x']=='X_COORDINATE');ck('FIELD_POSTCODE',fm['postcode']=='PCDS');ck('FIELD_LONGITUDE',fm['lon']=='LONGITUDE')
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);osz=d/'os.zip';nsz=d/'ns.zip';odz=d/'od.zip'
  with zipfile.ZipFile(osz,'w') as z:z.writestr('open.csv','UPRN,X_COORDINATE,Y_COORDINATE,LATITUDE,LONGITUDE\n1,100,200,51,-1\n2,101,201,52,-2\n3,102,202,53,-3\n')
  with zipfile.ZipFile(nsz,'w') as z:z.writestr('nsul.csv','UPRN,PCDS\n1,AA1 1AA\n2,BB1 1BB\n3,CC1 1CC\n')
  with zipfile.ZipFile(odz,'w') as z:z.writestr('onsud.csv','UPRN,POSTCODE\n1,AA1 1AA\n2,BB1 1BB\n3,CC1 1CC\n')
  conn=sqlite3.connect(':memory:');m.setup(conn);oa=m.import_os(conn,osz,batch_size=2);na=m.import_relation(conn,nsz,'nsul',batch_size=2);da=m.import_relation(conn,odz,'onsud',batch_size=2);ns=m.source_stats(conn,'nsul');ods=m.source_stats(conn,'onsud');pv=m.preview(conn,3)
  ck('OS_ROWS',oa['rows_inserted']==3);ck('OS_DUPLICATES_ZERO',oa['duplicate_uprns']==0);ck('NSUL_ROWS',na['rows_inserted']==3);ck('ONSUD_ROWS',da['rows_inserted']==3);ck('NSUL_RATIO',ns['join_ratio']==1.0);ck('ONSUD_RATIO',ods['join_ratio']==1.0);ck('CONFLICTS_ZERO',ns['duplicate_postcode_conflicts']==0 and ods['duplicate_postcode_conflicts']==0);ck('PREVIEW_THREE',len(pv)==3);ck('PREVIEW_NOT_PROMOTED',all(not x['parcel_relation_promoted'] for x in pv));conn.close()
 payload={'schema_version':1,'slot_id':'internet_access_3','tests_total':len(checks),'tests_passed':sum(x['passed'] for x in checks),'tests_failed':sum(not x['passed'] for x in checks),'checks':checks,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};print(json.dumps(payload,indent=2));return 0 if payload['tests_failed']==0 and payload['tests_total']==18 else 2
if __name__=='__main__':raise SystemExit(main())
