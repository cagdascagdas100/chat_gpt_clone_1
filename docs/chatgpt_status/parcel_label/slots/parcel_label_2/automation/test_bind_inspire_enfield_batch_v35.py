from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

SOURCE=Path(__file__).with_name('bind_inspire_enfield_batch_v35.py').read_text()
with tempfile.TemporaryDirectory() as td:
    here=Path(td)
    (here/'bind_inspire_enfield_batch_v35.py').write_text(SOURCE)
    (here/'bind_inspire_enfield_batch_v34.py').write_text('''from pathlib import Path\nclass Base:\n REPO=Path("/tmp/repo"); RESULT=Path("/tmp/result.json"); RECON=Path("/tmp/recon.json"); WEB=Path("/tmp/old.json"); TASK_VERSION="old"\n def main(self): return 7\nbase=Base()\nclass Pool:\n cleaned=False\n def cleanup(self): self.cleaned=True\n_POOL=Pool(); calls=[]\ndef _original_write(path,payload): calls.append((path,payload))\nclass ShaState: _expected_gml_sha256=None\n_sha_state=ShaState()\ndef sha256(payload):\n import hashlib\n data=Path(payload).read_bytes() if isinstance(payload,Path) else bytes(payload)\n value=hashlib.sha256(data).hexdigest(); _sha_state._expected_gml_sha256=value; return value\nbase.sha256=sha256\n_MAX_GML_BYTES=64\n''')
    (here/'validate_inspire_cadastral_parcel_v22.py').write_text('''from pathlib import Path\ngeometry=object()\ndef parse(path,target_ids,expected_sha256,expected_size_bytes,max_bytes):\n import hashlib\n data=Path(path).read_bytes()\n assert hashlib.sha256(data).hexdigest()==expected_sha256\n assert len(data)==expected_size_bytes and len(data)<=max_bytes\n return {t:[{"ok":True}] for t in target_ids},{"bounded":True,"size":expected_size_bytes}\n''')
    spec=importlib.util.spec_from_file_location('v35',here/'bind_inspire_enfield_batch_v35.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    checks=0
    assert mod.base.TASK_VERSION=='9.4-exact-size-bounded-immutable-snapshot-batch'; checks+=1
    assert mod.base.WEB.name=='progress_wave44_exact_result_latest.json'; checks+=1
    assert mod.base.parse is mod.parse; checks+=1
    assert mod.base.sha256 is mod.sha256; checks+=1
    assert mod.base.geometry is mod.validator.geometry; checks+=1
    assert mod._MAX_GML_BYTES==64; checks+=1
    assert len(mod._ALLOWED_WRITES)==3; checks+=1
    mod.write(mod.base.RESULT,{'x':1}); assert len(mod.previous.calls)==1; checks+=1
    try: mod.write(Path('/tmp/no.json'),{})
    except RuntimeError as exc: assert 'WRITE_PATH_NOT_ALLOWED' in str(exc); checks+=1
    else: raise AssertionError('write gate')
    with tempfile.NamedTemporaryFile(suffix='.gml',delete=False) as h:
        h.write(b'<x/>'); path=Path(h.name)
    try:
        digest=mod.base.sha256(path); assert mod._expected_gml_size_bytes==4; checks+=1
        assert mod._sha_state._expected_gml_sha256==digest; checks+=1
        found,summary=mod.parse(path,{'1'}); assert found['1'][0]['ok'] and summary['bounded']; checks+=1
        assert summary['size']==4; checks+=1
        assert mod._expected_gml_size_bytes is None; checks+=1
        assert mod._sha_state._expected_gml_sha256 is None; checks+=1
        try: mod.parse(path,{'1'})
        except RuntimeError as exc: assert 'EXPECTED_SHA256_NOT_CAPTURED' in str(exc); checks+=1
        else: raise AssertionError('missing digest')
        mod._sha_state._expected_gml_sha256='0'*64
        try: mod.parse(path,{'1'})
        except RuntimeError as exc: assert 'EXPECTED_SIZE_NOT_CAPTURED' in str(exc); checks+=1
        else: raise AssertionError('missing size')
        mod._sha_state._expected_gml_sha256=None
        path.write_bytes(b'x'*65)
        try: mod.sha256(path)
        except RuntimeError as exc: assert 'SIZE_LIMIT_EXCEEDED' in str(exc); checks+=1
        else: raise AssertionError('oversize')
    finally: path.unlink(missing_ok=True)
    assert mod.main()==7; checks+=1
    assert mod._POOL.cleaned; checks+=1
    assert mod.base.WEB==mod.EXACT_WEB; checks+=1
    print(f'PARCEL_LABEL_2_BOUNDED_SNAPSHOT_WORKER_TESTS={checks}/{checks}')
