from __future__ import annotations

import types
from pathlib import Path

MODULE_PATH = Path(__file__).with_name(
    'security_public_safety_2_wave139_official_postcode_release_lineage_field_semantics_primary_binding_20260801_v2.py'
)

source = MODULE_PATH.read_text()
start_marker = "'wave139_first_release_items': ["
end_marker = 'for item in item_release_rows[:50]'
needle = "'item_id': row['item_id'],"
replacement = "'item_id': item['item_id'],"

start = source.find(start_marker)
if start < 0:
    raise RuntimeError('WAVE139_FIRST_RELEASE_BLOCK_START_NOT_FOUND')
end = source.find(end_marker, start)
if end < 0:
    raise RuntimeError('WAVE139_FIRST_RELEASE_BLOCK_END_NOT_FOUND')
end += len(end_marker)
block = source[start:end]
occurrences = block.count(needle)
if occurrences != 1:
    raise RuntimeError(f'WAVE139_CONTEXT_REFERENCE_REPAIR_COUNT_MISMATCH:{occurrences}')
repaired_block = block.replace(needle, replacement, 1)
repaired_source = source[:start] + repaired_block + source[end:]
if repaired_source.count(needle) != source.count(needle) - 1:
    raise RuntimeError('WAVE139_CONTEXT_REFERENCE_REPAIR_POSTCHECK_FAILED')

module = types.ModuleType('wave139_v2_repaired')
module.__file__ = str(MODULE_PATH)
exec(compile(repaired_source, str(MODULE_PATH), 'exec'), module.__dict__)

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
