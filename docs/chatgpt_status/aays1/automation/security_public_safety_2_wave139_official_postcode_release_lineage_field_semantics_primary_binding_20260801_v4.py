from __future__ import annotations

import types
from pathlib import Path

MODULE_PATH = Path(__file__).with_name(
    'security_public_safety_2_wave139_official_postcode_release_lineage_field_semantics_primary_binding_20260801_v2.py'
)

source = MODULE_PATH.read_text()
needle = "'item_id': row['item_id'],"
replacement = "'item_id': item['item_id'],"
occurrences = source.count(needle)
if occurrences != 1:
    raise RuntimeError(f'WAVE139_EXACT_REFERENCE_REPAIR_COUNT_MISMATCH:{occurrences}')

module = types.ModuleType('wave139_v2_repaired')
module.__file__ = str(MODULE_PATH)
exec(compile(source.replace(needle, replacement, 1), str(MODULE_PATH), 'exec'), module.__dict__)

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
