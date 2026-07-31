from __future__ import annotations

import hashlib
import importlib.util
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    shutil.copy2(HERE / "validate_inspire_cadastral_parcel_v22.py", root / "validate_inspire_cadastral_parcel_v22.py")
    shutil.copy2(HERE / "stable_xml_source_v4.py", root / "stable_xml_source_v4.py")
    shutil.copy2(HERE / "stable_xml_source_v3.py", root / "stable_xml_source_v3.py")
    (root / "validate_inspire_cadastral_parcel_v21.py").write_text('''from pathlib import Path\nclass Base: pass\nbase=Base()\nclass Under:\n @staticmethod\n def parse(path,target_ids):\n  data=Path(path).read_bytes()\n  return {t:[{"payload":data.decode()}] for t in target_ids},{"underlying_parse":True}\nprevious=Under()\ngeometry=object()\ndef validate_collection_cardinality(*a,**k): return True\n''')
    spec=importlib.util.spec_from_file_location('v22',root/'validate_inspire_cadastral_parcel_v22.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    data=b'<FeatureCollection/>'
    with tempfile.NamedTemporaryFile(suffix='.gml',delete=False) as h:
        h.write(data); path=Path(h.name)
    try:
        found,summary=mod.parse(path,{'1','2'},expected_sha256=hashlib.sha256(data).hexdigest(),expected_size_bytes=len(data),max_bytes=1024)
        values=[
            set(found)=={'1','2'}, summary['underlying_parse'], summary['xml_immutable_snapshot_validation_passed'],
            summary['xml_exact_size_validation_passed'], summary['xml_bounded_read_validation_passed'],
            summary['xml_parse_bytes_bound_to_download_sha256'], summary['xml_parse_bytes_bound_to_download_size'],
            summary['xml_parser_source_bound_to_bounded_immutable_private_snapshot'],
            summary['xml_transient_original_growth_cannot_exhaust_snapshot_read'],
            summary['xml_source_expected_size_bytes']==len(data), mod.geometry is not None,
            callable(mod.validate_collection_cardinality), mod.base is not None,
        ]
        checks=0
        for value in values: assert value; checks+=1
        try: mod.parse(path,{'1'},expected_sha256=hashlib.sha256(data).hexdigest(),expected_size_bytes=len(data)+1,max_bytes=1024)
        except RuntimeError as exc: assert 'SIZE_MISMATCH' in str(exc); checks+=1
        else: raise AssertionError('size mismatch')
        print(f'PARCEL_LABEL_2_BOUNDED_SNAPSHOT_VALIDATOR_TESTS={checks}/{checks}')
    finally: path.unlink(missing_ok=True)
