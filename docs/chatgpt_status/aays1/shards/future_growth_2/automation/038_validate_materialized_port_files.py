#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path, PurePosixPath

ALLOWED=(
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/',
 'docs/chatgpt_status/aays1/shards/future_growth_2/',
 'england_map_web/data/aays_21_slots/future_growth_2/',
)
REQUIRED_ROLES={'checkpoint','status','next_task','website','progress','candidate_wave','validation','automation'}
HEX40=re.compile(r'^[0-9a-f]{40}$')
HEX64=re.compile(r'^[0-9a-f]{64}$')

def git_blob_sha1(data:bytes)->str:
    return hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()

def _safe_path(raw:str)->PurePosixPath:
    if not isinstance(raw,str) or not raw:
        raise ValueError('path missing')
    p=PurePosixPath(raw)
    if p.is_absolute() or '..' in p.parts or '\\' in raw:
        raise ValueError(f'unsafe path: {raw}')
    if not raw.startswith(ALLOWED):
        raise ValueError(f'out of scope: {raw}')
    return p

def validate(manifest:dict, repo_root:Path)->dict:
    if manifest.get('slot_id')!='future_growth_2':
        raise ValueError('wrong slot_id')
    source_head=str(manifest.get('source_head_sha') or '').lower()
    if not HEX40.fullmatch(source_head):
        raise ValueError('invalid source head sha')
    entries=manifest.get('entries')
    if not isinstance(entries,list) or not entries:
        raise ValueError('entries missing')
    root=repo_root.resolve(strict=True)
    paths=[];roles=[];verified_bytes=0
    for entry in entries:
        if not isinstance(entry,dict):
            raise ValueError('entry must be object')
        raw=str(entry.get('path') or '')
        _safe_path(raw)
        blob_sha=str(entry.get('blob_sha') or '').lower()
        content_sha=str(entry.get('content_sha256') or '').lower()
        expected_bytes=int(entry.get('bytes') or 0)
        role=str(entry.get('role') or '').strip()
        if not HEX40.fullmatch(blob_sha): raise ValueError(f'invalid blob sha: {raw}')
        if not HEX64.fullmatch(content_sha): raise ValueError(f'invalid content sha256: {raw}')
        if expected_bytes<=0: raise ValueError(f'invalid byte count: {raw}')
        if not role: raise ValueError(f'missing role: {raw}')
        path=(root/raw).resolve(strict=True)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f'resolved path escapes repo root: {raw}') from exc
        original=root/raw
        if original.is_symlink(): raise ValueError(f'symlink forbidden: {raw}')
        if not path.is_file(): raise ValueError(f'not a regular file: {raw}')
        data=path.read_bytes()
        if len(data)!=expected_bytes: raise ValueError(f'byte count mismatch: {raw}')
        if hashlib.sha256(data).hexdigest()!=content_sha: raise ValueError(f'content sha256 mismatch: {raw}')
        if git_blob_sha1(data)!=blob_sha: raise ValueError(f'git blob sha mismatch: {raw}')
        paths.append(raw);roles.append(role);verified_bytes+=len(data)
    if len(paths)!=len(set(paths)): raise ValueError('duplicate path')
    missing=sorted(REQUIRED_ROLES-set(roles))
    if missing: raise ValueError('missing roles: '+','.join(missing))
    product=manifest.get('product_state') or {}
    for field in ('verified_rows','canonical_parcel_matches','future_growth_scores','actual_business_rows_written'):
        if int(product.get(field) or 0)!=0: raise ValueError(f'product state must remain zero: {field}')
    return {'schema_version':1,'slot_id':'future_growth_2','executed':True,
            'entries_verified':len(entries),'bytes_verified':verified_bytes,
            'content_sha256_verified':len(entries),'git_blob_sha1_verified':len(entries),
            'required_roles_verified':len(REQUIRED_ROLES),'mismatches':0,'symlinks':0,
            'out_of_scope':0,'duplicates':0,'all_passed':True,'port_executed':False,
            'merge_executed':False,'ref_update_executed':False,'final_ready':False,
            'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=validate(json.loads(a.manifest.read_text(encoding='utf-8')),a.repo_root)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out));return 0
if __name__=='__main__': raise SystemExit(main())
