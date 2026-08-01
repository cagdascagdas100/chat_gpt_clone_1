from __future__ import annotations

import importlib.util
import traceback
from pathlib import Path

ROOT = Path.cwd()
REPAIR = ROOT / 'docs/chatgpt_status/aays1/automation/security_public_safety_2_wave138_repair_official_asset_discovery_20260801.py'
ORIGINAL = ROOT / 'docs/chatgpt_status/aays1/automation/security_public_safety_2_wave138_official_postcode_package_assets_exact_row_binding_20260801.py'

repair_spec = importlib.util.spec_from_file_location('wave138_repair', REPAIR)
repair = importlib.util.module_from_spec(repair_spec)
assert repair_spec and repair_spec.loader
repair_spec.loader.exec_module(repair)

original_spec = importlib.util.spec_from_file_location('wave138_original_clean', ORIGINAL)
original = importlib.util.module_from_spec(original_spec)
assert original_spec and original_spec.loader
original_spec.loader.exec_module(original)


def fixed_asset_candidates(items: list[dict]) -> list[dict]:
    existing = original.asset_candidates(items)
    combined: dict[str, dict] = {row['url']: row for row in existing}
    for item in items:
        for row in repair.hosted_query_assets(item):
            combined[row['url']] = row
    rows = list(combined.values())
    rows.sort(key=lambda row: (
        int(row.get('priority', 9)),
        not any(token in str(row.get('item_title') or '').lower() for token in (
            'onspd', 'nspl', 'postcode directory', 'postcode lookup'
        )),
        -(int(row.get('item_modified') or 0)),
        row['url'],
    ))
    return rows[:repair.r.MAX_ASSETS]


repair.r.asset_candidates = fixed_asset_candidates


if __name__ == '__main__':
    try:
        repair.r.main()
        repair.write_diagnostic('COMPLETED')
    except Exception:
        error = traceback.format_exc()
        repair.write_diagnostic('FAILED_FAIL_CLOSED', error)
        raise
