#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,tempfile
from pathlib import Path
SCRIPT=Path(__file__).with_name('040_verify_dispatch_bound_single_run_provenance.py');spec=importlib.util.spec_from_file_location('finalprov',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='a'*40;passed=[]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def base_audit(work,web,out=None):return {'slot_id':'internet_access_2','status':'PASS_EXTENDED_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY','provenance_artifact_count':20,'provenance_chain_sha256':'b'*64,'canonical_rows':4,'execution_code_artifact_count':4,'actual_business_data_rows_written':0,'scores_written':0,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False}
m.extended.audit=base_audit
def fixture(root):
 work=root/'work';web=root/'web';dump(web/'dispatch_execution_gate_latest.json',{'slot_id':'internet_access_2','status':'PASS_FRESH_13_OF_13_DISPATCH_EXECUTION_GATE','dispatch_permitted':True,'gate_count':13,'passed_gate_count':13,'blocked_gate_count':0,'evidence_file_count':8,'evidence_chain_sha256':'c'*64,'review_pr_head_sha':HEAD,'expected_review_head_sha':HEAD,'actual_business_data_rows_written':0,'final_ready':False});return work,web
def check(n,v):
 if not v:raise AssertionError(n)
 passed.append(n)
def fail(n,mut,text,head=HEAD):
 with tempfile.TemporaryDirectory() as t:
  w,v=fixture(Path(t));p=v/'dispatch_execution_gate_latest.json';x=json.loads(p.read_text());mut(x);dump(p,x)
  try:m.audit(w,v,head)
  except ValueError as e:
   if text not in str(e):raise AssertionError(f'{n}:{e}')
   passed.append(n)
  else:raise AssertionError(n)
with tempfile.TemporaryDirectory() as t:
 w,v=fixture(Path(t));out=v/'runner_provenance_audit_latest.json';r=m.audit(w,v,HEAD,out)
 for n,x in [('status',r['status']=='PASS_DISPATCH_BOUND_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY'),('artifact_count',r['provenance_artifact_count']==21),('base_count',r['base_extended_provenance_artifact_count']==20),('gate_count',r['dispatch_execution_gate_artifact_count']==1),('chain',len(r['provenance_chain_sha256'])==64),('gate_sha',len(r['dispatch_execution_gate_sha256'])==64),('evidence_chain',r['dispatch_evidence_chain_sha256']=='c'*64),('head',r['dispatch_review_pr_head_sha']==HEAD),('output',out.is_file()),('review_only',r['actual_business_data_rows_written']==0 and r['final_ready'] is False)]:check(n,x)
fail('status_rejected',lambda x:x.update(status='FAIL'),'gate status')
fail('dispatch_false',lambda x:x.update(dispatch_permitted=False),'gate status')
fail('gate_count_rejected',lambda x:x.update(passed_gate_count=12),'gate count')
fail('evidence_count_rejected',lambda x:x.update(evidence_file_count=7),'evidence file count')
fail('evidence_hash_rejected',lambda x:x.update(evidence_chain_sha256='X'),'evidence chain')
fail('head_rejected',lambda x:x.update(review_pr_head_sha='d'*40),'review head SHA')
fail('business_rejected',lambda x:x.update(actual_business_data_rows_written=1),'review-only boundary')
fail('final_rejected',lambda x:x.update(final_ready=True),'review-only boundary')
assert len(passed)==18,(len(passed),passed)
print(json.dumps({'status':'PASS','tests_passed':18,'tests_total':18,'test_names':passed,'actual_business_data_rows_written':0,'final_ready':False},sort_keys=True))
