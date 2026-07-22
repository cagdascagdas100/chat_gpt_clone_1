#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,json,sqlite3,tempfile
from pathlib import Path

def args():p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);return p.parse_args()
def mod():
 p=Path(__file__).with_name('087_exact_uprn_postcode_join_revision17.py');s=importlib.util.spec_from_file_location('m',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def check(name,condition,out):out.append({'name':name,'passed':bool(condition)})
def main():
 m=mod();out=[]
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);rows=[]
  for k in ('os_open_uprn','nsul','onsud'):
   p=d/(k+'.zip');p.write_bytes(k.encode());rows.append((k,p))
  packages={k:{'actual_sha256':__import__('hashlib').sha256(p.read_bytes()).hexdigest(),'cache_path':str(p),'bytes_hydrated':p.stat().st_size} for k,p in rows}
  manifest,digest=m.package_manifest(packages);check('manifest_three',len(manifest)==3,out);check('digest_64',len(digest)==64,out);check('manifest_order',[x['package_id'] for x in manifest]==['os_open_uprn','nsul','onsud'],out);check('size_recorded',all(x['size']>0 for x in manifest),out);check('path_recorded',all(x['cache_path'] for x in manifest),out)
  p=rows[0][1];p.write_bytes(b'changed')
  try:m.package_manifest(packages);raised=False
  except ValueError:raised=True
  check('size_change_rejected',raised,out)
  bad=dict(packages);bad['nsul']=dict(bad['nsul']);bad['nsul']['actual_sha256']='x'
  try:m.package_manifest(bad);raised=False
  except ValueError:raised=True
  check('invalid_sha_rejected',raised,out)
 with tempfile.TemporaryDirectory() as td:
  db=Path(td)/'x.sqlite';c=sqlite3.connect(db);m.checkpoint_schema(c);check('checkpoint_table',m.table_count(c,'checkpoint')==0,out);m.put_cp(c,'s','a'*64,3,{'x':1});cp=m.get_cp(c,'s','a'*64);check('checkpoint_get',cp['row_count']==3 and cp['audit']['x']==1,out);c.execute('CREATE TABLE t(x INTEGER)');c.executemany('INSERT INTO t VALUES(?)',[(1,),(2,),(3,)]);c.commit();check('table_count',m.table_count(c,'t')==3,out);check('valid_checkpoint',m.valid_cp(c,'s','a'*64,'t') is not None,out);c.execute('DELETE FROM t WHERE x=3');c.commit();check('count_mismatch_invalidates',m.valid_cp(c,'s','a'*64,'t') is None,out);check('manifest_mismatch_invalidates',m.get_cp(c,'s','b'*64) is None,out);c.close()
 check('hex64_accept',bool(m.HEX64.fullmatch('a'*64)),out);check('hex64_reject',not m.HEX64.fullmatch('A'*64),out);text=Path(__file__).with_name('087_exact_uprn_postcode_join_revision17.py').read_text()
 for name,token in [('without_rowid','WITHOUT ROWID'),('stage_os','os_import'),('source_loop',"('nsul','onsud')"),('stage_common','common_build'),('no_parcel','parcel_relations_promoted'),('manifest_guard','manifest_sha256')]:check(name,token in text,out)
 check('test_count',len(out)==21,out);passed=sum(x['passed'] for x in out);print(json.dumps({'tests':out,'passed':passed,'failed':len(out)-passed},indent=2));return 0 if passed==len(out) else 1
if __name__=='__main__':raise SystemExit(main())
