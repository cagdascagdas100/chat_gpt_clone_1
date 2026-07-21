#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, tempfile
from pathlib import Path

def load(path: Path):
    spec=importlib.util.spec_from_file_location("preflight",path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
class Resp:
    def __init__(self,status=200,ctype="application/json",body=b"{}"):
        self.status=status; self.headers={"content-type":ctype}; self.body=body
    def read(self,n=-1): return self.body[:n] if n>=0 else self.body
    def __enter__(self): return self
    def __exit__(self,*args): return False

def main() -> int:
    import json
    p=argparse.ArgumentParser(); p.add_argument("--preflight",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); mod=load(a.preflight); checks=[]
    def check(name, fn):
        try: fn(); checks.append({"check":name,"passed":True,"detail":""})
        except Exception as exc: checks.append({"check":name,"passed":False,"detail":f"{type(exc).__name__}: {exc}"})
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); f=root/'canonical.geojson'; f.write_bytes(b'abcdef')
        sha=mod.git_blob_sha(f)
        check('canonical_valid',lambda: (_ for _ in ()).throw(AssertionError()) if not mod.validate_canonical(f,sha,1)['ready'] else None)
        check('canonical_missing',lambda: (_ for _ in ()).throw(AssertionError()) if mod.validate_canonical(root/'missing',sha,1)['state']!='MISSING' else None)
        check('canonical_too_small',lambda: (_ for _ in ()).throw(AssertionError()) if mod.validate_canonical(f,sha,100)['state']!='TOO_SMALL' else None)
        check('canonical_hash_mismatch',lambda: (_ for _ in ()).throw(AssertionError()) if mod.validate_canonical(f,'0'*40,1)['state']!='GIT_BLOB_SHA_MISMATCH' else None)
        resolver=lambda host,port:[(None,None,None,None,('127.0.0.1',port))]
        dnsfail=lambda host,port: (_ for _ in ()).throw(OSError('dns'))
        opener_json=lambda req,timeout:Resp(200,'application/json',b'{}')
        opener_html=lambda req,timeout:Resp(200,'text/html',b'<html/>')
        opener_500=lambda req,timeout:Resp(500,'application/json',b'{}')
        check('url_policy_rejects_http',lambda: (_ for _ in ()).throw(AssertionError()) if mod.probe_https('http://www.planning.data.gov.uk/x',mod.PLANNING_HOST,('application/json',),resolver=resolver,opener=opener_json)['state']!='URL_POLICY_REJECTED' else None)
        check('url_policy_rejects_wrong_host',lambda: (_ for _ in ()).throw(AssertionError()) if mod.probe_https('https://evil.test/x',mod.PLANNING_HOST,('application/json',),resolver=resolver,opener=opener_json)['state']!='URL_POLICY_REJECTED' else None)
        check('dns_blocked',lambda: (_ for _ in ()).throw(AssertionError()) if mod.probe_https(mod.PLANNING_URL,mod.PLANNING_HOST,('application/json',),resolver=dnsfail,opener=opener_json)['state']!='DNS_BLOCKED' else None)
        check('http_status_rejected',lambda: (_ for _ in ()).throw(AssertionError()) if mod.probe_https(mod.PLANNING_URL,mod.PLANNING_HOST,('application/json',),resolver=resolver,opener=opener_500)['state']!='HTTP_STATUS_REJECTED' else None)
        check('planning_content_type_rejected',lambda: (_ for _ in ()).throw(AssertionError()) if mod.probe_https(mod.PLANNING_URL,mod.PLANNING_HOST,('application/json',),resolver=resolver,opener=opener_html)['state']!='CONTENT_TYPE_REJECTED' else None)
        check('planning_json_valid',lambda: (_ for _ in ()).throw(AssertionError()) if not mod.probe_https(mod.PLANNING_URL,mod.PLANNING_HOST,('application/json',),resolver=resolver,opener=opener_json)['ready'] else None)
        check('hmlr_html_valid',lambda: (_ for _ in ()).throw(AssertionError()) if not mod.probe_https(mod.HMLR_URL,mod.HMLR_HOST,('text/html',),resolver=resolver,opener=opener_html)['ready'] else None)
        check('hmlr_json_rejected',lambda: (_ for _ in ()).throw(AssertionError()) if mod.probe_https(mod.HMLR_URL,mod.HMLR_HOST,('text/html',),resolver=resolver,opener=opener_json)['state']!='CONTENT_TYPE_REJECTED' else None)
        valid={'ready':True}; invalid={'ready':False}
        check('chain_ready_all_three',lambda: (_ for _ in ()).throw(AssertionError()) if not mod.build_result(valid,valid,valid)['ready_for_live_chain'] else None)
        check('chain_blocks_missing_canonical',lambda: (_ for _ in ()).throw(AssertionError()) if mod.build_result(invalid,valid,valid)['ready_for_live_chain'] else None)
        check('chain_blocks_planning',lambda: (_ for _ in ()).throw(AssertionError()) if mod.build_result(valid,invalid,valid)['ready_for_live_chain'] else None)
        check('chain_blocks_hmlr',lambda: (_ for _ in ()).throw(AssertionError()) if mod.build_result(valid,valid,invalid)['ready_for_live_chain'] else None)
        result=mod.build_result(invalid,invalid,invalid)
        check('product_outputs_zero',lambda: (_ for _ in ()).throw(AssertionError(result)) if any(result[k] for k in ('actual_period_current_api_responses','actual_hmlr_downloads','actual_exact_intersections','canonical_rows_exported','canonical_parcel_matches','future_growth_scores_produced','actual_business_data_rows_written')) else None)
        check('safety_flags_false',lambda: (_ for _ in ()).throw(AssertionError(result)) if any(result[k] for k in ('final_ready','fake_data','db_write','migration','production_deploy')) else None)
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"test_type":"live_runtime_dependency_preflight","checks_passed":sum(x['passed'] for x in checks),"checks_total":len(checks),"all_passed":all(x['passed'] for x in checks),"checks":checks,"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(out)); return 0 if out['all_passed'] else 1
if __name__=='__main__': raise SystemExit(main())
