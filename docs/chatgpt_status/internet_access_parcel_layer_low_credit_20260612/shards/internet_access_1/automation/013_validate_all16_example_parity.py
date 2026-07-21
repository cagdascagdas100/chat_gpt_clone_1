#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from collections import Counter, defaultdict
from pathlib import Path

POSTCODE_RE = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2}$")
EXPECTED_CLASSES = {"strong": 3, "supported": 10, "borderline": 2, "conflict": 1}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8'))
    rows = data.get('examples', [])
    checks = []
    def check(name: str, ok: bool):
        checks.append({'name': name, 'pass': bool(ok)})
    check('slot_id', data.get('slot_id') == 'internet_access_1')
    check('sixteen_examples', len(rows) == 16)
    check('unique_row_numbers', len({r.get('row_no') for r in rows}) == 16)
    check('unique_parcels', len({r.get('parcel_id') for r in rows}) == 16)
    check('ten_unique_postcodes', len({r.get('postcode') for r in rows}) == 10)
    check('postcode_format', all(POSTCODE_RE.match(r.get('postcode','')) for r in rows))
    check('values_in_range', all(all(0 <= float(r[k]) <= 100 for k in ('gigabit_available_pct','ultrafast_or_100mbps_available_pct','superfast_30mbps_available_pct','unable_30mbps_pct')) for r in rows))
    check('threshold_monotonic', all(r['gigabit_available_pct'] <= r['ultrafast_or_100mbps_available_pct'] <= r['superfast_30mbps_available_pct'] for r in rows))
    check('accuracy_all_2_of_4', all(r.get('internet_accuracy') == '2/4' for r in rows))
    check('no_r2_refresh', all(r.get('r2_refreshed') is False for r in rows))
    check('coverage_source_guarded', all(r.get('coverage_source_role') == 'LEGACY_OFCom_POSTCODE_PROXY_NOT_CORRECTED_R2' for r in rows))
    check('postcode_source_guarded', all(r.get('postcode_source_role') == 'CENTROID_CROSSCHECK_ONLY_NO_BROADBAND_VALUES' for r in rows))
    check('official_direct_rows_zero', data.get('official_direct_rows_read') == 0)
    check('business_rows_zero', data.get('business_rows_written') == 0)
    check('final_ready_false', data.get('final_ready') is False)
    classes = Counter(r.get('join_class') for r in rows)
    check('class_distribution', dict(classes) == EXPECTED_CLASSES)
    groups = defaultdict(list)
    for r in rows:
        groups[r['postcode']].append((r['gigabit_available_pct'], r['ultrafast_or_100mbps_available_pct'], r['superfast_30mbps_available_pct'], r['unable_30mbps_pct']))
    repeated = {k: v for k, v in groups.items() if len(v) > 1}
    check('repeated_groups_rm70yl_rm70yx', set(repeated) == {'RM70YL','RM70YX'})
    check('repeated_values_invariant', all(len(set(v)) == 1 for v in repeated.values()))
    check('one_conflict_fail_closed', sum(r.get('join_class') == 'conflict' and r.get('join_distance_m') is None and len(r.get('join_distance_candidates_m', [])) == 2 for r in rows) == 1)
    check('thirteen_within_250m', sum(isinstance(r.get('join_distance_m'), (int, float)) and r['join_distance_m'] <= 250 for r in rows) == 13)
    passed = sum(c['pass'] for c in checks)
    result = {'schema_version': 1, 'slot_id': 'internet_access_1', 'status': 'PASS' if passed == len(checks) else 'FAIL', 'checks_passed': passed, 'checks_failed': len(checks)-passed, 'checks_total': len(checks), 'checks': checks, 'class_distribution': dict(classes), 'business_rows_written': 0, 'fake_data': False, 'migration': False, 'production_deploy': False, 'final_ready': False}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'passed': passed, 'total': len(checks)}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
