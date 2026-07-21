#!/usr/bin/env python3
from __future__ import annotations
import copy, importlib.util
from pathlib import Path
from typing import Any, Callable
ROOT=Path(__file__).parent

def load()->Any:
 spec=importlib.util.spec_from_file_location('p033',ROOT/'033_polygon_popup_acceptance.py');assert spec and spec.loader;mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def fail(fn:Callable[[],Any])->None:
 try:fn()
 except Exception:return
 raise AssertionError('expected failure')

def runtime()->dict[str,Any]:
 return {'slot_id':'internet_access_3','status':'REAL_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY','real_runtime_rows_validated':30761,'row_partition':{'start':61523,'end':92283,'rows':30761},'samples':[{'canonical_row_no':61523,'canonical_program_parcel_id':'parcel_61523','status':'CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW','postcode':'AB1 2CD','business_row_written':False,'internet_availability_quality_percent':None},{'canonical_row_no':61524,'canonical_program_parcel_id':'parcel_61524','status':'NO_VERIFIED_POSTCODE_NO_DATA','postcode':None,'business_row_written':False,'internet_availability_quality_percent':None}]}

def discovery()->dict[str,Any]:
 return {'slot_id':'internet_access_3','state':'PASS_UNIQUE_MAIN_MAP_POPUP_CONTRACT_DISCOVERED','nearest_feature_fallback_allowed':False,'manual_coordinate_fallback_allowed':False,'selected':{'html_path':'england_map_web/index.html','engine':'leaflet','popup_evidence':True,'internet_evidence':True,'identity_evidence':True}}

def main()->int:
 m=load();out=[];s=m.validate_runtime(runtime());assert s['canonical_row_no']==61523;out.append('proxy_priority')
 d=m.validate_discovery(discovery());assert d['engine']=='leaflet';out.append('valid_discovery')
 req=m.popup_requirements(s);assert req['postcode']=='AB1 2CD';out.append('proxy_requirements')
 c=m.validate_popup_text('Parcel parcel_61523 Postcode AB1 2CD Internet availability',req);assert c['pass'];out.append('proxy_popup_pass')
 c=m.validate_popup_text('row 61523 broadband AB1 2CD',req);assert c['pass'];out.append('row_identity_pass')
 c=m.validate_popup_text('parcel_61523 internet',req);assert not c['pass'];out.append('postcode_required')
 c=m.validate_popup_text('AB1 2CD internet',req);assert not c['pass'];out.append('identity_required')
 no=runtime();no['samples']=no['samples'][1:];ns=m.validate_runtime(no);nreq=m.popup_requirements(ns);out.append('no_data_sample')
 assert m.validate_popup_text('parcel_61524 no data internet',nreq)['pass'];out.append('no_data_popup_pass')
 assert not m.validate_popup_text('parcel_61524 other',nreq)['pass'];out.append('no_data_semantic_required')
 for name,mut in [
 ('wrong_slot',lambda x:x.update(slot_id='x')),('wrong_status',lambda x:x.update(status='WAITING')),('wrong_rows',lambda x:x.update(real_runtime_rows_validated=1)),('wrong_partition',lambda x:x['row_partition'].update(start=1)),('no_samples',lambda x:x.update(samples=[])),('bad_parcel',lambda x:x['samples'][0].update(canonical_program_parcel_id='parcel_x')),('business_write',lambda x:x['samples'][0].update(business_row_written=True)),('score',lambda x:x['samples'][0].update(internet_availability_quality_percent=55))]:
  v=runtime();mut(v);fail(lambda v=v:m.validate_runtime(v));out.append(name)
 for name,mut in [('discovery_waiting',lambda x:x.update(state='WAITING')),('bad_path',lambda x:x['selected'].update(html_path='x.html')),('bad_engine',lambda x:x['selected'].update(engine='x')),('nearest_allowed',lambda x:x.update(nearest_feature_fallback_allowed=True)),('manual_allowed',lambda x:x.update(manual_coordinate_fallback_allowed=True))]:
  v=discovery();mut(v);fail(lambda v=v:m.validate_discovery(v));out.append(name)
 print(f'PASS {len(out)}/{len(out)}');return 0
if __name__=='__main__':raise SystemExit(main())
