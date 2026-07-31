from __future__ import annotations
import hashlib
import importlib.util
import tempfile
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('validator20',HERE/'validate_inspire_cadastral_parcel_v20.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
checks=0

def ok(v):
    global checks
    assert v; checks+=1

def expect(fragment,fn):
    global checks
    try: fn()
    except Exception as exc:
        assert fragment in str(exc), exc; checks+=1
    else: raise AssertionError(fragment)

payload=b'<root/>'
with tempfile.NamedTemporaryFile(suffix='.gml',delete=False) as handle:
    handle.write(payload); path=Path(handle.name)
try:
    digest=hashlib.sha256(payload).hexdigest()
    found,summary=mod.parse(path,{'101','202'},expected_sha256=digest)
    ok(set(found)=={'101','202'})
    ok(summary['xml_descriptor_pinning_validation_passed'] is True)
    ok(summary['xml_parser_uses_descriptor_pinned_source'] is True)
    ok(summary['xml_parse_bytes_bound_to_download_sha256'] is True)
    ok(summary['xml_source_expected_sha256']==digest)
    ok(summary['xml_parser_source_mode'] in {'PROC_DESCRIPTOR_PATH','PRIVATE_SECURE_COPY'})
    expect('XML_SOURCE_SHA256_MISMATCH',lambda:mod.parse(path,{'1'},expected_sha256='0'*64))

    seen={}
    original=mod._underlying_parse
    def capture(stable_path,target_ids):
        seen['path']=Path(stable_path)
        seen['bytes']=Path(stable_path).read_bytes()
        return original(stable_path,target_ids)
    mod._underlying_parse=capture
    found,summary=mod.parse(path,{'303'},expected_sha256=digest)
    ok(seen['bytes']==payload)
    ok(seen['path'] != path or summary['xml_parser_source_mode']=='PRIVATE_SECURE_COPY')
    ok(found['303'][0]['feature']=='303')
    mod._underlying_parse=original
finally:
    path.unlink(missing_ok=True)

ok(mod.geometry is mod.previous.geometry)
ok(mod.validate_collection_cardinality is mod.previous.validate_collection_cardinality)
ok(callable(mod.pinning.guarded_descriptor_call))
print(f'PARCEL_LABEL_2_DESCRIPTOR_VALIDATOR_TESTS={checks}/{checks}')
