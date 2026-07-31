from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave104_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

# Values without Python-string syntax are safely shifted through placeholders.
protected = [
    ("932f0dec011c3cd3837da448ee86725150ea4fe3", "__SOURCE_HEAD__"),
    ("bbf5266a5005f0dd7b09e450bf9f96af840df7acf2a123d2e42652451f619568", "__PREVIOUS_CONTINUATION__"),
    ("e744fbe6afb47dc3318636cbe2d4c07affe481c41149cf58f7cba680b5773b9a", "__CURRENT_CONTINUATION__"),
    ("wave103", "__PREVIOUS_WAVE__"),
    ("wave104", "__CURRENT_WAVE__"),
    ("WAVE104", "__CURRENT_WAVE_UPPER__"),
    ("0078_", "__PREVIOUS_QUEUE__"),
    ("0079_", "__CURRENT_QUEUE__"),
    ("25060", "__ROWS_OLD_PREVIOUS__"),
    ("25510", "__ROWS_BASE__"),
    ("25960", "__ROWS_TARGET__"),
    ("24235", "__MIN_OLD_PREVIOUS__"),
    ("24662", "__MIN_CURRENT__"),
    ("25188", "__ACCURACY_BASE__"),
    ("55822", "__PARCEL_OLD_START__"),
    ("56272", "__PARCEL_START__"),
    ("56722", "__PARCEL_END_PLUS_ONE__"),
    ("56271", "__PARCEL_OLD_END__"),
    ("56721", "__PARCEL_END__"),
    ("1.76", "__DELTA_PREVIOUS__"),
    ("1.73", "__DELTA_CURRENT__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"WAVE105_TRANSFORM_FRAGMENT_MISSING: {old}")
    text = text.replace(old, token)

resolved = [
    ("__SOURCE_HEAD__", "e82becf47301cd12374bc104635cbd343addb552"),
    ("__PREVIOUS_CONTINUATION__", "e744fbe6afb47dc3318636cbe2d4c07affe481c41149cf58f7cba680b5773b9a"),
    ("__CURRENT_CONTINUATION__", "c88ff5cd9693d956af9df90a59b630a07a954b5d504de33d6f0a71bb097cf57d"),
    ("__PREVIOUS_WAVE__", "wave104"),
    ("__CURRENT_WAVE__", "wave105"),
    ("__CURRENT_WAVE_UPPER__", "WAVE105"),
    ("__PREVIOUS_QUEUE__", "0079_"),
    ("__CURRENT_QUEUE__", "0080_"),
    ("__ROWS_OLD_PREVIOUS__", "25510"),
    ("__ROWS_BASE__", "25960"),
    ("__ROWS_TARGET__", "26410"),
    ("__MIN_OLD_PREVIOUS__", "24662"),
    ("__MIN_CURRENT__", "25090"),
    ("__ACCURACY_BASE__", "25632"),
    ("__PARCEL_OLD_START__", "56272"),
    ("__PARCEL_START__", "56722"),
    ("__PARCEL_END_PLUS_ONE__", "57172"),
    ("__PARCEL_OLD_END__", "56721"),
    ("__PARCEL_END__", "57171"),
    ("__DELTA_PREVIOUS__", "1.73"),
    ("__DELTA_CURRENT__", "1.70"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"WAVE105_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

# Syntax-sensitive rules are changed only on their unique source lines.
lines = text.splitlines()

def rewrite_unique_line(marker: str, old: str, new: str) -> None:
    matches = [i for i, line in enumerate(lines) if marker in line]
    if len(matches) != 1:
        raise SystemExit(f"WAVE105_LINE_COUNT_INVALID:{marker}:{len(matches)}")
    idx = matches[0]
    if old not in lines[idx]:
        raise SystemExit(f"WAVE105_LINE_FRAGMENT_MISSING:{marker}:{old}:{lines[idx]}")
    lines[idx] = lines[idx].replace(old, new, 1)


def shift_pair(marker: str, old_a: str, old_b: str, new_a: str, new_b: str) -> None:
    matches = [i for i, line in enumerate(lines) if marker in line]
    if len(matches) != 1:
        raise SystemExit(f"WAVE105_PAIR_LINE_COUNT_INVALID:{marker}:{len(matches)}")
    idx = matches[0]
    line = lines[idx]
    if old_a not in line or old_b not in line:
        raise SystemExit(f"WAVE105_PAIR_VALUES_MISSING:{marker}:{line}")
    line = line.replace(old_a, "__WAVE105_PAIR_A__", 1)
    line = line.replace(old_b, new_b, 1)
    line = line.replace("__WAVE105_PAIR_A__", new_a, 1)
    lines[idx] = line

# Protected rules in the generated Wave105 wrapper.
shift_pair(', "__EMBEDDED_SCHEMA_RULE__"),', "80", "81", "81", "82")
rewrite_unique_line(', "__CURRENT_SCHEMA__"),', "126", "127")
rewrite_unique_line(', "__OWNERSHIP_SCHEMA__"),', "130", "131")
rewrite_unique_line(', "__HEARTBEAT_SCHEMA__"),', "125", "126")
rewrite_unique_line(', "__LEASE_RULE__"),', "152", "153")
rewrite_unique_line(', "__PRIORITY_RULE__"),', "-179", "-180")
rewrite_unique_line(', "__PROGRESS_RULE__"),', "98.24", "98.27")

# Resolved rules applied by that wrapper to produce Wave105 runtime files.
shift_pair('("__EMBEDDED_SCHEMA_RULE__",', "81", "82", "82", "83")
rewrite_unique_line('("__CURRENT_SCHEMA__",', "127", "128")
rewrite_unique_line('("__OWNERSHIP_SCHEMA__",', "131", "132")
rewrite_unique_line('("__HEARTBEAT_SCHEMA__",', "126", "127")
rewrite_unique_line('("__LEASE_RULE__",', "153", "154")
rewrite_unique_line('("__PRIORITY_RULE__",', "-180", "-181")
rewrite_unique_line('("__PROGRESS_RULE__",', "98.27", "98.30")

# The generated wrapper's own final-fragment assertion must follow the new scope.
rewrite_unique_line('expanded_scope_progress_percent', "98.27", "98.30")

text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

required = [
    'source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave104_orchestrator.py")',
    'SOURCE_HEAD = "e82becf47301cd12374bc104635cbd343addb552"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_25960_TO_26410_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "c88ff5cd9693d956af9df90a59b630a07a954b5d504de33d6f0a71bb097cf57d"',
    'TASK_ID = "security_public_safety_2_priority_26410row_incremental_evidence_expansion_20260731"',
    'OWNER = "github-actions-security-public-safety-2-wave105"',
    '0080_security_public_safety_2_priority_26410row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave105_latest.json',
    'priority_26410row_evidence_expansion_latest.json',
    '"accepted_base_rows": 25960',
    '"merged_candidate_rows": 26410',
    '"minimum_merged_police_hash_rows": 25090',
    '"incremental_parcel_start": 56722',
    '"incremental_parcel_end": 57171',
    '"expanded_scope_progress_percent": 98.3',
    '"expanded_scope_delta_percentage_points": 1.7',
    'len(rows) != 26410',
    '"parcel_57171"',
    'WAVE105_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"WAVE105_FINAL_FRAGMENT_MISSING: {fragment}")

compile(text, str(source), "exec")
exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})
