#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,tempfile,zipfile
from pathlib import Path

def args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);return p.parse_args()
def module():
 path=Path(__file__).parent/'071_full_release_hydration_manifest.py';spec=importlib.util.spec_from_file_location('hydration',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 m=module();checks=[]
 def ck(name,value):checks.append({'name':name,'passed':bool(value)})
 ck('SAFE_NAME',m.safe_name('A B/C')=='A_B_C')
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);csv=d/'a.csv';csv.write_text('UPRN,X_COORDINATE\n1,2\n');info=m.inspect_package(csv);ck('CSV_MEDIA',info['media_type']=='text/csv-or-text');z=d/'a.zip'
  with zipfile.ZipFile(z,'w') as a:a.writestr('x.csv','UPRN,PCDS\n1,AA11AA\n')
  zi=m.inspect_package(z);ck('ZIP_MEDIA',zi['media_type']=='application/zip');ck('ZIP_INTEGRITY',zi['zip_integrity_passed']);ck('ZIP_MEMBER_COUNT',zi['zip_member_count']==1);ck('ZIP_CSV_COUNT',zi['zip_csv_member_count']==1);ck('MD5_LENGTH',len(m.file_hash(csv,'md5'))==32);ck('SHA256_LENGTH',len(m.file_hash(csv,'sha256'))==64)
 osr={'state':'resolved','selected':{'open_uprn':{'fileName':'open.zip','url':'https://x/open','size':10,'md5':'0'*32},'uprn_topographic_area':{'fileName':'lids.zip','url':'https://x/lids','size':20,'md5':'1'*32}}};ons={'state':'runtime_validation_passed','release_label':'May 2026','products':[{'product_id':'nsul','selected':{'id':'abc','title':'NSUL','size':30}},{'product_id':'onsud','selected':{'id':'def','title':'ONSUD','size':40}}]}
 packages=m.build_packages(osr,ons);ck('PACKAGE_COUNT',len(packages)==4);ck('OS_UPRN_ID',packages[0]['package_id']=='os_open_uprn');ck('OS_LIDS_ID',packages[1]['package_id']=='os_lids_uprn_topographic_area');ck('NSUL_ID',packages[2]['package_id']=='nsul');ck('ONSUD_ID',packages[3]['package_id']=='onsud');ck('ARCGIS_NSUL_URL',packages[2]['download_url'].endswith('/abc/data'));ck('ARCGIS_ONSUD_URL',packages[3]['download_url'].endswith('/def/data'));ck('OS_MD5_REQUIRED',packages[0]['expected_md5']=='0'*32);ck('ONS_MD5_OPTIONAL',packages[2]['expected_md5'] is None)
 try:m.build_packages({'state':'blocked'},ons);blocked=False
 except ValueError:blocked=True
 ck('BLOCK_UNRESOLVED_OS',blocked);payload={'schema_version':1,'slot_id':'internet_access_3','tests_total':len(checks),'tests_passed':sum(x['passed'] for x in checks),'tests_failed':sum(not x['passed'] for x in checks),'checks':checks,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};print(json.dumps(payload,indent=2));return 0 if payload['tests_failed']==0 and payload['tests_total']==18 else 2
if __name__=='__main__':raise SystemExit(main())
