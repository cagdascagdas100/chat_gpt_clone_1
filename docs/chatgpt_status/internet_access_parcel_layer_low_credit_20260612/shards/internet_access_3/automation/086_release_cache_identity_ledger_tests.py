#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,tempfile
from pathlib import Path

def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);return p.parse_args()
def loadmod():
 p=Path(__file__).with_name('085_release_cache_identity_ledger.py');s=importlib.util.spec_from_file_location('m',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ok(name,fn,out):
 try:fn();out.append({'name':name,'passed':True})
 except Exception as e:out.append({'name':name,'passed':False,'error':f'{type(e).__name__}:{e}'})
def main():
 m=loadmod();out=[];spec={'package_id':'nsul','authority':'ONS','product_id':'NSUL','title':'x','download_url':'https://x/data','expected_size':10,'expected_md5':None,'release_label':'May 2026','arcgis_item_id':'a'}
 ok('safe_name',lambda:(_ for _ in ()).throw(AssertionError()) if m.safe('a b')!='a_b' else None,out)
 ident=m.canonical_identity(spec);digest=m.identity_sha(ident)
 ok('identity_length',lambda:(_ for _ in ()).throw(AssertionError()) if len(digest)!=64 else None,out)
 ok('identity_stable',lambda:(_ for _ in ()).throw(AssertionError()) if digest!=m.identity_sha(dict(reversed(list(ident.items())))) else None,out)
 changed=dict(spec);changed['expected_size']=11
 ok('identity_changes_size',lambda:(_ for _ in ()).throw(AssertionError()) if digest==m.identity_sha(m.canonical_identity(changed)) else None,out)
 changed=dict(spec);changed['download_url']='https://y/data'
 ok('identity_changes_url',lambda:(_ for _ in ()).throw(AssertionError()) if digest==m.identity_sha(m.canonical_identity(changed)) else None,out)
 with tempfile.TemporaryDirectory() as td:
  c=Path(td);f,p,l=m.package_paths(c,spec)
  ok('ons_extension',lambda:(_ for _ in ()).throw(AssertionError()) if f.suffix!='.download' else None,out)
  ok('partial_suffix',lambda:(_ for _ in ()).throw(AssertionError()) if not str(p).endswith('.download.part') else None,out)
  ok('ledger_suffix',lambda:(_ for _ in ()).throw(AssertionError()) if not str(l).endswith('.download.identity.json') else None,out)
  f.write_bytes(b'x');q=m.quarantine(f,c/'q','STALE',digest[:12])
  ok('quarantine_moves',lambda:(_ for _ in ()).throw(AssertionError()) if f.exists() or q is None or not q.exists() else None,out)
  ok('quarantine_missing_none',lambda:(_ for _ in ()).throw(AssertionError()) if m.quarantine(f,c/'q','STALE',digest[:12]) is not None else None,out)
 spec2=dict(spec);spec2['package_id']='os_open_uprn'
 with tempfile.TemporaryDirectory() as td:
  f,p,l=m.package_paths(Path(td),spec2)
  ok('os_extension',lambda:(_ for _ in ()).throw(AssertionError()) if f.suffix!='.zip' else None,out)
 ok('identity_contains_release',lambda:(_ for _ in ()).throw(AssertionError()) if ident['release_label']!='May 2026' else None,out)
 ok('identity_contains_item',lambda:(_ for _ in ()).throw(AssertionError()) if ident['arcgis_item_id']!='a' else None,out)
 ok('identity_excludes_unknown',lambda:(_ for _ in ()).throw(AssertionError()) if 'unknown' in ident else None,out)
 ok('https_preserved',lambda:(_ for _ in ()).throw(AssertionError()) if ident['download_url']!='https://x/data' else None,out)
 ok('package_id_preserved',lambda:(_ for _ in ()).throw(AssertionError()) if ident['package_id']!='nsul' else None,out)
 ok('test_count',lambda:(_ for _ in ()).throw(AssertionError()) if len(out)!=16 else None,out)
 passed=sum(x['passed'] for x in out);print(json.dumps({'tests':out,'passed':passed,'failed':len(out)-passed},indent=2));return 0 if passed==len(out) else 1
if __name__=='__main__':raise SystemExit(main())
