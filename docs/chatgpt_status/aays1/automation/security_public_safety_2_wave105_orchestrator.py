from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave104_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

# Wave104 is itself a wrapper. Mask its placeholder names so the Wave105
# transformation cannot accidentally resolve tokens belonging to the inner wrapper.
inner_tokens = [
    "SOURCE_HEAD",
    "PREVIOUS_CONTINUATION",
    "CURRENT_CONTINUATION",
    "PREVIOUS_WAVE",
    "CURRENT_WAVE",
    "CURRENT_WAVE_UPPER",
    "PREVIOUS_QUEUE",
    "CURRENT_QUEUE",
    "ROWS_OLD_PREVIOUS",
    "ROWS_BASE",
    "ROWS_TARGET",
    "MIN_OLD_PREVIOUS",
    "MIN_CURRENT",
    "ACCURACY_BASE",
    "PARCEL_OLD_START",
    "PARCEL_START",
    "PARCEL_END_PLUS_ONE",
    "PARCEL_OLD_END",
    "PARCEL_END",
    "DELTA_PREVIOUS",
    "DELTA_CURRENT",
    "EMBEDDED_SCHEMA_RULE",
    "CURRENT_SCHEMA",
    "OWNERSHIP_SCHEMA",
    "HEARTBEAT_SCHEMA",
    "LEASE_RULE",
    "PRIORITY_RULE",
    "PROGRESS_RULE",
]
for name in inner_tokens:
    original = f"__{name}__"
    masked = f"__W104_INNER_{name}__"
    if original not in text:
        raise SystemExit(f"WAVE105_INNER_TOKEN_MISSING: {original}")
    text = text.replace(original, masked)

protected = [
    ("932f0dec011c3cd3837da448ee86725150ea4fe3", "__W105_SOURCE_HEAD__"),
    ("bbf5266a5005f0dd7b09e450bf9f96af840df7acf2a123d2e42652451f619568", "__W105_PREVIOUS_CONTINUATION__"),
    ("e744fbe6afb47dc3318636cbe2d4c07affe481c41149cf58f7cba680b5773b9a", "__W105_CURRENT_CONTINUATION__"),
    ("wave103", "__W105_PREVIOUS_WAVE__"),
    ("wave104", "__W105_CURRENT_WAVE__"),
    ("WAVE104", "__W105_CURRENT_WAVE_UPPER__"),
    ("0078_", "__W105_PREVIOUS_QUEUE__"),
    ("0079_", "__W105_CURRENT_QUEUE__"),
    ("25060", "__W105_ROWS_OLD_PREVIOUS__"),
    ("25510", "__W105_ROWS_BASE__"),
    ("25960", "__W105_ROWS_TARGET__"),
    ("24235", "__W105_MIN_OLD_PREVIOUS__"),
    ("24662", "__W105_MIN_CURRENT__"),
    ("25188", "__W105_ACCURACY_BASE__"),
    ("55822", "__W105_PARCEL_OLD_START__"),
    ("56272", "__W105_PARCEL_START__"),
    ("56722", "__W105_PARCEL_END_PLUS_ONE__"),
    ("56271", "__W105_PARCEL_OLD_END__"),
    ("56721", "__W105_PARCEL_END__"),
    ("1.76", "__W105_DELTA_PREVIOUS__"),
    ("1.73", "__W105_DELTA_CURRENT__"),
    ('"schema_version": 127,', "__W105_CURRENT_SCHEMA__"),
    ('"schema_version": 131,', "__W105_OWNERSHIP_SCHEMA__"),
    ('"schema_version": 126,', "__W105_HEARTBEAT_SCHEMA__"),
    ('or 153) + 1', "__W105_LEASE_RULE__"),
    ('"priority": -180,', "__W105_PRIORITY_RULE__"),
    ('98.27', "__W105_PROGRESS_RULE__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"WAVE105_TRANSFORM_FRAGMENT_MISSING: {old}")
    text = text.replace(old, token)

resolved = [
    ("__W105_SOURCE_HEAD__", "e82becf47301cd12374bc104635cbd343addb552"),
    ("__W105_PREVIOUS_CONTINUATION__", "e744fbe6afb47dc3318636cbe2d4c07affe481c41149cf58f7cba680b5773b9a"),
    ("__W105_CURRENT_CONTINUATION__", "c88ff5cd9693d956af9df90a59b630a07a954b5d504de33d6f0a71bb097cf57d"),
    ("__W105_PREVIOUS_WAVE__", "wave104"),
    ("__W105_CURRENT_WAVE__", "wave105"),
    ("__W105_CURRENT_WAVE_UPPER__", "WAVE105"),
    ("__W105_PREVIOUS_QUEUE__", "0079_"),
    ("__W105_CURRENT_QUEUE__", "0080_"),
    ("__W105_ROWS_OLD_PREVIOUS__", "25510"),
    ("__W105_ROWS_BASE__", "25960"),
    ("__W105_ROWS_TARGET__", "26410"),
    ("__W105_MIN_OLD_PREVIOUS__", "24662"),
    ("__W105_MIN_CURRENT__", "25090"),
    ("__W105_ACCURACY_BASE__", "25632"),
    ("__W105_PARCEL_OLD_START__", "56272"),
    ("__W105_PARCEL_START__", "56722"),
    ("__W105_PARCEL_END_PLUS_ONE__", "57172"),
    ("__W105_PARCEL_OLD_END__", "56721"),
    ("__W105_PARCEL_END__", "57171"),
    ("__W105_DELTA_PREVIOUS__", "1.73"),
    ("__W105_DELTA_CURRENT__", "1.70"),
    ("__W105_CURRENT_SCHEMA__", '"schema_version": 128,'),
    ("__W105_OWNERSHIP_SCHEMA__", '"schema_version": 132,'),
    ("__W105_HEARTBEAT_SCHEMA__", '"schema_version": 127,'),
    ("__W105_LEASE_RULE__", 'or 154) + 1'),
    ("__W105_PRIORITY_RULE__", '"priority": -181,'),
    ("__W105_PROGRESS_RULE__", '98.30'),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"WAVE105_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

# Preserve the exact raw-string escaping already proven by Wave104 and only
# shift the two schema numbers on the two unique embedded-rule lines.
lines = text.splitlines()

def shift_pair(marker: str, first_old: str, second_old: str, first_new: str, second_new: str) -> None:
    indices = [i for i, line in enumerate(lines) if marker in line]
    if len(indices) != 1:
        raise SystemExit(f"WAVE105_EMBEDDED_LINE_COUNT_INVALID:{marker}:{len(indices)}")
    idx = indices[0]
    line = lines[idx]
    first_pos = line.find(first_old)
    if first_pos < 0:
        raise SystemExit(f"WAVE105_EMBEDDED_FIRST_VALUE_MISSING:{marker}:{line}")
    line = line[:first_pos] + "__W105_SCHEMA_FIRST__" + line[first_pos + len(first_old):]
    second_pos = line.find(second_old)
    if second_pos < 0:
        raise SystemExit(f"WAVE105_EMBEDDED_SECOND_VALUE_MISSING:{marker}:{line}")
    line = line[:second_pos] + second_new + line[second_pos + len(second_old):]
    line = line.replace("__W105_SCHEMA_FIRST__", first_new, 1)
    lines[idx] = line

shift_pair(', "__W104_INNER_EMBEDDED_SCHEMA_RULE__"),', "80", "81", "81", "82")
shift_pair('("__W104_INNER_EMBEDDED_SCHEMA_RULE__",', "81", "82", "82", "83")
text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

# Restore Wave104's own placeholder names after all Wave105 values are resolved.
for name in inner_tokens:
    masked = f"__W104_INNER_{name}__"
    original = f"__{name}__"
    if masked not in text:
        raise SystemExit(f"WAVE105_MASKED_TOKEN_MISSING: {masked}")
    text = text.replace(masked, original)

required = [
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
