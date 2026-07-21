#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('o035',ROOT/'035_run_review_acceptance_with_polygon.py');assert spec and spec.loader;m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def main()->int:
 r=Path('/repo');c=m.build_commands(r,'HEAD',False,'http://127.0.0.1:8012/',False);out=[]
 assert len(c)==2;out.append('two_without_polygon');assert c[0][0]==sys.executable;out.append('python_executable');assert '029_run_validate_import_and_accept_web.py' in c[0][1];out.append('existing_chain_once');assert '--validate-existing-only' not in c[0];out.append('normal_mode');assert '031_discover_polygon_popup_contract.py' in c[1][1];out.append('discovery_second')
 c=m.build_commands(r,'abc',True,'http://x/',True);assert len(c)==3;out.append('three_with_polygon');assert '--validate-existing-only' in c[0];out.append('validate_existing');assert c[0][c[0].index('--git-ref')+1]=='abc';out.append('git_ref');assert '033_polygon_popup_acceptance.py' in c[2][1];out.append('polygon_third');assert c[2][c[2].index('--base-url')+1]=='http://x/';out.append('base_url');print(f'PASS {len(out)}/{len(out)}');return 0
if __name__=='__main__':raise SystemExit(main())
