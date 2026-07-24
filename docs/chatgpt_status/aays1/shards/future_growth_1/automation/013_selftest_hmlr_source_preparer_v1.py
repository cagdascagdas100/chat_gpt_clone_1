#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name('012_prepare_hmlr_inspire_sources.py')

def main() -> int:
    checks = {}
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        starter = root / 'starter.json'
        starter.write_text(json.dumps({'slot_id':'future_growth_1','candidates':[{'hmlr_inspire_id':str(i),'local_authority_name':'London Borough of Barking and Dagenham'} for i in range(3)]}), encoding='utf-8')
        fixture = root / 'index.html'
        fixture.write_text('<table><tr><td>London Borough of Barking and Dagenham</td><td><a href="/files/lbbd.gml">Download .gml</a></td></tr></table>', encoding='utf-8')
        out = root / 'out'
        run = subprocess.run([sys.executable,str(SCRIPT),'--starter-manifest',str(starter),'--output-dir',str(out),'--resolve-only','--page-html',str(fixture)],capture_output=True,text=True,check=False)
        payload = json.loads((out/'hmlr_source_manifest.json').read_text(encoding='utf-8'))
        checks['positive_exit_zero'] = run.returncode == 0
        checks['positive_slot_id'] = payload.get('slot_id') == 'future_growth_1'
        checks['positive_status'] = payload.get('status') == 'READY_HMLR_URLS_RESOLVED'
        checks['positive_unique_record'] = len(payload.get('records') or []) == 1
        checks['positive_exact_url'] = payload['records'][0]['download_link']['url'].endswith('/files/lbbd.gml')
        checks['positive_no_fuzzy'] = payload.get('nearest_or_fuzzy_authority_match_used') is False
        fixture.write_text('<ul><li>London Borough of Barking and Dagenham <a href="/a.gml">Download .gml</a><a href="/b.gml">Download .gml</a></li></ul>', encoding='utf-8')
        out2 = root / 'out2'
        run2 = subprocess.run([sys.executable,str(SCRIPT),'--starter-manifest',str(starter),'--output-dir',str(out2),'--resolve-only','--page-html',str(fixture)],capture_output=True,text=True,check=False)
        payload2 = json.loads((out2/'hmlr_source_manifest.json').read_text(encoding='utf-8'))
        checks['duplicate_exit_two'] = run2.returncode == 2
        checks['duplicate_fail_closed'] = payload2.get('status') == 'BLOCKED_HMLR_SOURCE_PREPARATION' and payload2.get('blocked',[{}])[0].get('status') == 'NO_UNIQUE_EXACT_DOWNLOAD_LINK'
    result = {'schema_version':1,'slot_id':'future_growth_1','result':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'passed':sum(checks.values()),'total':len(checks),'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if all(checks.values()) else 2

if __name__=='__main__': raise SystemExit(main())
