from __future__ import annotations
import hashlib, importlib.util, json, tempfile
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('v2',HERE/'stream_canonical_inventory_v2.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def blob(raw:bytes)->str:return hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
def feature(n:int, *, pid=None,row=None,iid=None,props=True):
    if not props:return {'type':'Feature','properties':None}
    return {'type':'Feature','properties':{'parcel_id':pid or f'parcel_{n}','row_no':n if row is None else row,'hmlr_inspire_id':iid or str(1000+n),'hmlr_lon':-0.1,'hmlr_lat':51.5,'hmlr_area_m2':10,'london_authority':'London Borough of Enfield'}}
def run(features,targets=('parcel_2','parcel_4'),expected=None,sha=None):
    raw=json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')).encode()
    with tempfile.NamedTemporaryFile(suffix='.geojson',delete=False) as h:h.write(raw);p=Path(h.name)
    try:return mod.canonical_targets(p,expected_blob_sha=sha or blob(raw),expected_feature_count=expected or len(features),target_ids=targets)
    finally:p.unlink(missing_ok=True)
def err(code,fn):
    try:fn()
    except RuntimeError as e:assert code in str(e),(code,str(e));return
    raise AssertionError(code)

tests=[]
def test(fn):tests.append(fn);return fn

@test
def valid():
    rows,s=run([feature(i) for i in range(1,6)])
    assert set(rows)=={'parcel_2','parcel_4'} and s['unique_parcel_id_count']==5 and s['parcel_id_span_complete']
@test
def duplicate():err('CANONICAL_PARCEL_ID_DUPLICATE',lambda:run([feature(1),feature(2),feature(2),feature(4),feature(5)]))
@test
def out_range():err('CANONICAL_PARCEL_ID_OUT_OF_RANGE',lambda:run([feature(1),feature(2),feature(3),feature(4),feature(6)]))
@test
def malformed():err('CANONICAL_PARCEL_ID_INVALID',lambda:run([feature(1),feature(2),feature(3,pid='parcel_03'),feature(4),feature(5)]))
@test
def row_mismatch():err('ROW_NO_MISMATCH',lambda:run([feature(1),feature(2,row=9),feature(3),feature(4),feature(5)]))
@test
def row_bool():err('ROW_NO_INVALID',lambda:run([feature(1),feature(2,row=True),feature(3),feature(4),feature(5)]))
@test
def props_missing():err('CANONICAL_PROPERTIES_NOT_OBJECT',lambda:run([feature(1),feature(2),feature(3,props=False),feature(4),feature(5)]))
@test
def target_iid_duplicate():err('INSPIRE_ID_INVALID_OR_DUPLICATE',lambda:run([feature(1),feature(2,iid='55'),feature(3),feature(4,iid='55'),feature(5)]))
@test
def target_iid_invalid():err('INSPIRE_ID_INVALID_OR_DUPLICATE',lambda:run([feature(1),feature(2,iid='x'),feature(3),feature(4),feature(5)]))
@test
def count_mismatch():err('CANONICAL_FEATURE_COUNT_MISMATCH',lambda:run([feature(i) for i in range(1,5)],targets=('parcel_2','parcel_4'),expected=5))
@test
def blob_mismatch():err('CANONICAL_BLOB_MISMATCH',lambda:run([feature(i) for i in range(1,6)],sha='0'*40))
@test
def duplicate_target_input():err('TARGET_ID_INPUT_DUPLICATE',lambda:run([feature(i) for i in range(1,6)],targets=('parcel_2','parcel_2')))
@test
def target_out_range():err('CANONICAL_PARCEL_ID_OUT_OF_RANGE',lambda:run([feature(i) for i in range(1,6)],targets=('parcel_2','parcel_9')))
@test
def generator_targets():
    rows,s=run([feature(i) for i in range(1,6)],targets=(x for x in ('parcel_2','parcel_4')))
    assert len(rows)==2 and s['target_count']==2
@test
def numeric_row_string_allowed():
    rows,s=run([feature(1),feature(2,row='2'),feature(3),feature(4),feature(5)])
    assert rows['parcel_2']['row_no']==2 and s['all_row_numbers_aligned']

for fn in tests:fn()
print(f'PASS {len(tests)}/{len(tests)}')
