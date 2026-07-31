from __future__ import annotations
import importlib.util
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('v21',HERE/'bind_inspire_enfield_batch_v21.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
checks=0
def ok(value):
    global checks
    assert value
    checks += 1
ok(mod.base.TASK_VERSION=='8.0-feature-member-cardinality-and-collection-count-batch')
ok(mod.base.WEB.name=='progress_wave29_exact_result_latest.json')
ok(mod.base.parse is mod.validator.parse)
ok(mod.base.geometry is mod.validator.geometry)
ok(mod.base.canonical is mod.previous.previous.canonical)
ok(callable(mod.base.fetch))
ok(len(mod._ALLOWED_WRITES)==3)
mod.write(mod.base.RESULT,{'a':1});ok(len(mod.previous.previous.previous.calls)==1)
try:mod.write(Path('/tmp/no.json'),{})
except RuntimeError as exc:ok('WRITE_PATH_NOT_ALLOWED' in str(exc))
else:raise AssertionError('write gate')
ok(callable(mod.validator.validate_collection_cardinality))
ok(mod.main()==7)
ok(mod._POOL.cleaned)
ok(mod.base.WEB==mod.EXACT_WEB)
print(f'PARCEL_LABEL_2_V21_WRAPPER_TESTS={checks}/{checks}')
print('FINAL_READY=false')
