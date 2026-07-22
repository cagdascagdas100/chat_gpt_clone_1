#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);return p.parse_args()
def mod():
 p=Path(__file__).with_name('089_revision17_runtime_acceptance.py');s=importlib.util.spec_from_file_location('m',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def base():
 safety={'state':'runtime_validation_passed','fake_data':False,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False,'parcel_relations_promoted':0,'actual_business_data_rows_written':0}
 pre={**safety,'packages_expected':4};ledger={**safety,'packages_bound':4,'packages':[{'identity_sha256':'a'*64} for _ in range(4)]};hydr={**safety,'packages_hydrated':4,'packages':[{'actual_sha256':'b'*64,'size_verified':True,'expected_md5':'c'*32,'md5_verified':True,'media_type':'application/zip','zip_integrity_passed':True} for _ in range(4)]};join={**safety,'stages_total':4,'stages_resumed':2,'stages_executed':2,'input_manifest_sha256':'d'*64,'join_stats':{'nsul':{'join_ratio':.98},'onsud':{'join_ratio':.99}},'common_exact_ratio':.95,'cross_source_postcode_conflicts':0,'preview_rows_written':40};return pre,ledger,hydr,join
def main():
 m=mod();tests=[]
 def t(n,mut,expect):
  docs=list(base());mut(docs);got=m.validate(*docs);tests.append({'name':n,'passed':(not got)==expect,'blockers':got})
 t('valid',lambda d:None,True);t('preflight_state',lambda d:d[0].update(state='blocked'),False);t('ledger_count',lambda d:d[1].update(packages_bound=3),False);t('ledger_hash',lambda d:d[1]['packages'][0].update(identity_sha256='x'),False);t('hydrate_count',lambda d:d[2].update(packages_hydrated=3),False);t('hydrate_sha',lambda d:d[2]['packages'][0].update(actual_sha256='x'),False);t('hydrate_size',lambda d:d[2]['packages'][0].update(size_verified=False),False);t('hydrate_md5',lambda d:d[2]['packages'][0].update(md5_verified=False),False);t('hydrate_zip',lambda d:d[2]['packages'][0].update(zip_integrity_passed=False),False);t('stage_coverage',lambda d:d[3].update(stages_executed=1),False);t('join_manifest',lambda d:d[3].update(input_manifest_sha256='x'),False);t('nsul_ratio',lambda d:d[3]['join_stats']['nsul'].update(join_ratio=.97),False);t('onsud_ratio',lambda d:d[3]['join_stats']['onsud'].update(join_ratio=.97),False);t('common_ratio',lambda d:d[3].update(common_exact_ratio=.94),False);t('conflict',lambda d:d[3].update(cross_source_postcode_conflicts=1),False);t('preview',lambda d:d[3].update(preview_rows_written=39),False);t('safety',lambda d:d[3].update(final_ready=True),False)
 passed=sum(x['passed'] for x in tests);print(json.dumps({'tests':tests,'passed':passed,'failed':len(tests)-passed},indent=2));return 0 if passed==len(tests) else 1
if __name__=='__main__':raise SystemExit(main())
