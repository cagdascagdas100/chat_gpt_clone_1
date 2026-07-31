from __future__ import annotations
import hashlib
import importlib.util
import tempfile
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('v33',HERE/'bind_inspire_enfield_batch_v33.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
checks=0
def ok(v):
    global checks
    assert v; checks+=1

def expect(fragment, fn):
    global checks
    try: fn()
    except Exception as exc:
        assert fragment in str(exc), exc; checks+=1
    else: raise AssertionError(fragment)

ok(mod.base.TASK_VERSION=='9.2-descriptor-pinned-parser-source-batch')
ok(mod.base.WEB.name=='progress_wave41_exact_result_latest.json')
ok(mod.base.parse is mod.parse)
ok(mod.base.sha256 is mod.previous.sha256)
ok(mod.base.geometry is mod.validator.geometry)
ok(len(mod._ALLOWED_WRITES)==3)

payload=b'<root/>'
with tempfile.NamedTemporaryFile(suffix='.gml',delete=False) as handle:
    handle.write(payload); path=Path(handle.name)
try:
    digest=mod.base.sha256(payload)
    ok(digest==hashlib.sha256(payload).hexdigest())
    found,summary=mod.base.parse(path,{'1','2'})
    ok(set(found)=={'1','2'})
    ok(summary['xml_descriptor_pinning_validation_passed'] is True)
    ok(summary['xml_parser_uses_descriptor_pinned_source'] is True)
    ok(mod.previous._expected_gml_sha256 is None)
    expect('XML_EXPECTED_SHA256_NOT_CAPTURED',lambda:mod.base.parse(path,{'1'}))
    mod.base.sha256(payload)
    expect('XML_EXPECTED_SHA256_ALREADY_CAPTURED',lambda:mod.base.sha256(payload))
    mod.previous._expected_gml_sha256=None
finally:
    path.unlink(missing_ok=True)

mod.write(mod.base.RESULT,{'x':1}); ok(True)
expect('WRITE_PATH_NOT_ALLOWED',lambda:mod.write(Path('/tmp/no.json'),{}))
ok(mod.main()==0)
ok(mod._POOL.cleaned)
ok(mod.validator.parse is not mod.previous.validator.parse)
print(f'PARCEL_LABEL_2_V33_WRAPPER_TESTS={checks}/{checks}')
