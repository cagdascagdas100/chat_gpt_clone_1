from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name(
    'security_public_safety_2_wave139_official_postcode_release_lineage_field_semantics_primary_binding_20260801_v2.py'
)
spec = importlib.util.spec_from_file_location('wave139_v2', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

_original_classify_field = module.classify_field


def classify_field(name: str, alias: str = '') -> str:
    semantic = _original_classify_field(name, alias)
    if semantic != 'other':
        return semantic
    text = f'{name} {alias}'.lower()
    if any(token in text for token in ('uprn', 'udprn', 'addressbase')):
        return 'property_identifier'
    if any(token in text for token in ('easting', 'northing', 'latitude', 'longitude', 'lat', 'long', 'x_coord', 'y_coord')):
        return 'coordinate'
    if any(token in text for token in ('msoa', 'output area', ' oa', 'ward', 'lad', 'local authority', 'region', 'country')):
        return 'administrative_geography'
    if any(token in text for token in ('objectid', 'fid', 'globalid', 'record_id', 'row_id')):
        return 'record_identifier'
    return semantic


module.classify_field = classify_field
module.main()
