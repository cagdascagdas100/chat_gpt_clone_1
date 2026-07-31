from __future__ import annotations
import importlib.util
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('v19',HERE/'bind_inspire_enfield_batch_v19.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
checks=0
def ok(v):
    global checks
    assert v; checks+=1
ok(mod.base.TASK_VERSION=='7.8-full-canonical-inventory-and-row-alignment-batch')
ok(mod.base.WEB.name=='progress_wave27_exact_result_latest.json')
ok(mod.base.canonical is mod.canonical)
ok(mod.base.fetch is mod.previous.fetch)
ok(len(mod._ALLOWED_WRITES)==3)
seen={}
def fake(path,**kwargs): seen['path']=path;seen.update(kwargs);return ({'x':1},{'ok':1})
mod.canonical_inventory.canonical_targets=fake
rows,summary=mod.canonical()
ok(rows=={'x':1} and summary=={'ok':1})
ok(seen['path']==mod.base.SOURCE)
ok(seen['expected_blob_sha']=='abc' and seen['expected_feature_count']==5)
ok(seen['target_ids']==['parcel_2','parcel_4'])
mod.write(mod.base.RESULT,{'a':1});ok(len(mod.previous.calls)==1)
try:mod.write(Path('/tmp/no.json'),{})
except RuntimeError as e:ok('WRITE_PATH_NOT_ALLOWED' in str(e))
else:raise AssertionError('write gate')
ok(mod.main()==7)
ok(mod._POOL.cleaned)
print(f'PASS {checks}/{checks}')
