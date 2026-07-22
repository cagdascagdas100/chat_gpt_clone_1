#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sqlite3,tempfile
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
  packages={k:{'actual_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cache_path':str(p),'bytes_hydrated':p.stat().st_size} for k,p in rows}
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
  db=Path(td)/'x.sqlite';c=sqlite3.connect(db);m.checkpoint_schema(c);c.execute('CREATE TABLE t(x INTEGER PRIMARY KEY,y TEXT)');c.executemany('INSERT INTO t VALUES(?,?)',[(1,'a'),(2,'b'),(3,'c')]);c.commit()
  fp=m.table_fingerprint(c,'t');check('fingerprint_sha64',len(fp['sha256'])==64,out);check('fingerprint_count',fp['rows_hashed']==3,out);check('fingerprint_columns',fp['columns']==['x','y'],out)
  m.put_cp(c,'s','a'*64,3,{'x':1},'t');cp=m.get_cp(c,'s','a'*64);check('checkpoint_get',cp['row_count']==3 and cp['audit']['x']==1,out);check('checkpoint_has_fingerprint',len(cp['audit']['_checkpoint_fingerprint']['sha256'])==64,out);check('valid_checkpoint',m.valid_cp(c,'s','a'*64,'t') is not None,out)
  c.execute("UPDATE t SET y='z' WHERE x=2");c.commit();check('same_count_content_change_invalidates',m.valid_cp(c,'s','a'*64,'t') is None,out)
  c.execute("UPDATE t SET y='b' WHERE x=2");c.commit();check('restored_content_revalidates',m.valid_cp(c,'s','a'*64,'t') is not None,out)
  c.execute("INSERT OR REPLACE INTO checkpoint VALUES(?,?,?,?,?)",('legacy','a'*64,'x',3,json.dumps({'x':1})));c.commit();check('legacy_count_only_checkpoint_invalid',m.valid_cp(c,'legacy','a'*64,'t') is None,out)
  c.execute('DELETE FROM t WHERE x=3');c.commit();check('count_mismatch_invalidates',m.valid_cp(c,'s','a'*64,'t') is None,out);check('manifest_mismatch_invalidates',m.get_cp(c,'s','b'*64) is None,out);c.close()
 with tempfile.TemporaryDirectory() as td:
  c=sqlite3.connect(Path(td)/'join.sqlite')
  c.executescript("""CREATE TABLE os_uprn(uprn TEXT PRIMARY KEY,x REAL,y REAL,lat REAL,lon REAL) WITHOUT ROWID;
  CREATE TABLE relation(source TEXT NOT NULL,uprn TEXT NOT NULL,postcode TEXT NOT NULL,PRIMARY KEY(source,uprn,postcode)) WITHOUT ROWID;""")
  c.executemany('INSERT INTO os_uprn VALUES(?,?,?,?,?)',[(str(i),i,i,i,i) for i in range(1,7)])
  c.executemany('INSERT INTO relation VALUES(?,?,?)',[
   ('nsul','1','AA11AA'),('onsud','1','AA11AA'),
   ('nsul','2','BB11BB'),('nsul','2','CC11CC'),('onsud','2','BB11BB'),
   ('nsul','3','DD11DD'),('onsud','3','EE11EE'),
   ('nsul','4','FF11FF'),
   ('nsul','5','GG11GG'),('onsud','5','GG11GG'),
   ('nsul','6','HH11HH'),('onsud','6','HH11HH'),('onsud','6','II11II')]);c.commit()
  count=m.build_common_safe(c);check('safe_common_count',count==2,out);check('safe_common_exact_rows',c.execute('SELECT uprn,postcode FROM common ORDER BY uprn').fetchall()==[('1','AA11AA'),('5','GG11GG')],out);check('multi_postcode_nsul_excluded',c.execute("SELECT COUNT(*) FROM common WHERE uprn='2'").fetchone()[0]==0,out);check('cross_source_conflict_excluded',c.execute("SELECT COUNT(*) FROM common WHERE uprn='3'").fetchone()[0]==0,out);check('single_source_excluded',c.execute("SELECT COUNT(*) FROM common WHERE uprn='4'").fetchone()[0]==0,out);check('multi_postcode_onsud_excluded',c.execute("SELECT COUNT(*) FROM common WHERE uprn='6'").fetchone()[0]==0,out)
  pv=m.preview(c,40);check('preview_count',len(pv)==2,out);check('preview_dual_source',all(set(x['sources'])=={'nsul','onsud'} for x in pv),out);check('preview_not_parcel',all('NOT_PARCEL_RELATION' in x['relation_semantics'] for x in pv),out)
  m.checkpoint_schema(c);m.put_cp(c,'common_build','f'*64,2,{'rows':2},'common');check('common_checkpoint_valid',m.valid_cp(c,'common_build','f'*64,'common') is not None,out);c.execute("UPDATE common SET postcode='ZZ11ZZ' WHERE uprn='1'");c.commit();check('common_same_count_corruption_invalid',m.valid_cp(c,'common_build','f'*64,'common') is None,out);c.close()
 check('hex64_accept',bool(m.HEX64.fullmatch('a'*64)),out);check('hex64_reject',not m.HEX64.fullmatch('A'*64),out)
 text=Path(__file__).with_name('087_exact_uprn_postcode_join_revision17.py').read_text()
 for name,token in [('without_rowid','WITHOUT ROWID'),('full_content_hash','FULL_ORDERED_TABLE_CONTENT_SHA256'),('safe_common','build_common_safe'),('stage_os','os_import'),('source_loop',"('nsul','onsud')"),('stage_common','common_build'),('no_parcel','parcel_relations_promoted'),('manifest_guard','manifest_sha256')]:check(name,token in text,out)
 check('test_count',len(out)==39,out);passed=sum(x['passed'] for x in out);print(json.dumps({'schema_version':2,'suite':'checkpointed_exact_uprn_join','tests_expected':40,'tests_passed':passed,'tests_failed':len(out)-passed,'checks':out,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False},indent=2));return 0 if passed==len(out) else 1
if __name__=='__main__':raise SystemExit(main())
