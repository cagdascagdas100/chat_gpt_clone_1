from __future__ import annotations
import hashlib, importlib.util, os, stat, tempfile, threading
from pathlib import Path
from typing import Callable, TypeVar

BASE_PATH=Path(__file__).with_name('stable_xml_source_v3.py')
spec=importlib.util.spec_from_file_location('parcel_label_2_snapshot_v3',BASE_PATH)
if spec is None or spec.loader is None: raise RuntimeError('PARCEL_LABEL_2_SNAPSHOT_V3_IMPORT_FAILED')
previous=importlib.util.module_from_spec(spec); spec.loader.exec_module(previous)
_T=TypeVar('_T'); _DEFAULT_MAX_BYTES=256*1024*1024; _LOCK=threading.RLock()


def _normalise_expected(value:str)->str:
    candidate=str(value).strip().lower()
    if len(candidate)!=64 or any(c not in '0123456789abcdef' for c in candidate): raise RuntimeError('XML_EXPECTED_SHA256_INVALID')
    return candidate

def _positive(name:str,value:int)->int:
    if not isinstance(value,int) or isinstance(value,bool) or value<=0: raise ValueError(f'{name} must be a positive integer')
    return value

def _size_gate(fd:int,expected:int,maximum:int,prefix:str)->None:
    size=os.fstat(fd).st_size
    if size>maximum: raise RuntimeError(f'{prefix}_SIZE_LIMIT_EXCEEDED:{size}:{maximum}')
    if size!=expected: raise RuntimeError(f'{prefix}_SIZE_MISMATCH:{size}:{expected}')

def _hash_exact(fd:int,*,chunk_size:int,expected:int,maximum:int,prefix:str)->str:
    _size_gate(fd,expected,maximum,prefix); digest=hashlib.sha256(); total=0; os.lseek(fd,0,os.SEEK_SET)
    while total<expected:
        chunk=os.read(fd,min(chunk_size,expected-total))
        if not chunk: raise RuntimeError(f'{prefix}_TRUNCATED:{total}:{expected}')
        total+=len(chunk); digest.update(chunk)
    if os.read(fd,1): raise RuntimeError(f'{prefix}_GREW_BEYOND_EXPECTED_SIZE:{expected}')
    os.lseek(fd,0,os.SEEK_SET); return digest.hexdigest()

def _copy_exact(fd:int,*,chunk_size:int,expected:int,maximum:int):
    _size_gate(fd,expected,maximum,'XML_SOURCE')
    directory=tempfile.TemporaryDirectory(prefix='parcel-label-2-xml-snapshot-'); root=Path(directory.name); target=root/'snapshot.gml'
    try:
        os.chmod(root,0o700); out=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_CLOEXEC',0),0o600)
        digest=hashlib.sha256(); total=0
        try:
            os.lseek(fd,0,os.SEEK_SET)
            while total<expected:
                chunk=os.read(fd,min(chunk_size,expected-total))
                if not chunk: raise RuntimeError(f'XML_SOURCE_TRUNCATED_DURING_SNAPSHOT:{total}:{expected}')
                total+=len(chunk); digest.update(chunk); view=memoryview(chunk)
                while view:
                    written=os.write(out,view)
                    if written<=0: raise RuntimeError('XML_SNAPSHOT_WRITE_ZERO')
                    view=view[written:]
            if os.read(fd,1): raise RuntimeError(f'XML_SOURCE_GREW_DURING_SNAPSHOT:{expected}')
            os.fsync(out); os.fchmod(out,0o400)
        finally:
            os.close(out); os.lseek(fd,0,os.SEEK_SET)
        info=os.stat(target,follow_symlinks=False); previous._regular_single_link(info,prefix='XML_SNAPSHOT')
        if info.st_size!=expected: raise RuntimeError(f'XML_SNAPSHOT_SIZE_MISMATCH:{info.st_size}:{expected}')
        if stat.S_IMODE(info.st_mode)!=0o400: raise RuntimeError(f'XML_SNAPSHOT_MODE_INVALID:{oct(stat.S_IMODE(info.st_mode))}')
        return directory,target,digest.hexdigest()
    except Exception:
        directory.cleanup(); raise

def guarded_immutable_snapshot_call(path:Path,*,expected_sha256:str,expected_size_bytes:int,operation:Callable[[Path],_T],chunk_size:int=1024*1024,max_bytes:int=_DEFAULT_MAX_BYTES,force_linked_snapshot:bool=False)->tuple[_T,dict]:
    expected_sha256=_normalise_expected(expected_sha256); expected_size=_positive('expected_size_bytes',expected_size_bytes); chunk=_positive('chunk_size',chunk_size); maximum=_positive('max_bytes',max_bytes)
    if expected_size>maximum: raise RuntimeError(f'XML_EXPECTED_SIZE_LIMIT_EXCEEDED:{expected_size}:{maximum}')
    with _LOCK:
        old_hash,old_copy=previous._hash_descriptor,previous._copy_descriptor_snapshot
        previous._hash_descriptor=lambda fd,*,chunk_size: _hash_exact(fd,chunk_size=chunk_size,expected=expected_size,maximum=maximum,prefix='XML_DESCRIPTOR')
        previous._copy_descriptor_snapshot=lambda fd,*,chunk_size: _copy_exact(fd,chunk_size=chunk_size,expected=expected_size,maximum=maximum)
        try:
            result,evidence=previous.guarded_immutable_snapshot_call(Path(path),expected_sha256=expected_sha256,operation=operation,chunk_size=chunk,force_linked_snapshot=force_linked_snapshot)
            return result,evidence|{'xml_source_expected_size_bytes':expected_size,'xml_source_observed_size_bytes':expected_size,'xml_snapshot_observed_size_bytes':expected_size,'xml_source_max_bytes':maximum,'xml_exact_size_validation_passed':True,'xml_bounded_read_validation_passed':True}
        finally:
            previous._hash_descriptor,previous._copy_descriptor_snapshot=old_hash,old_copy
