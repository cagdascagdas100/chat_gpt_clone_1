from __future__ import annotations

import ast
from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave97_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

protected = [
    ("46d33e257cb7d824d5a677d8f762e5afa956111e", "__SOURCE_HEAD__"),
    ("1486d431576a8dcdd404cf0e8630338af66e73694ce8f9be71a6936afa272732", "__PREVIOUS_CONTINUATION__"),
    ("8c0d233f0b4e80b52f2d50fcfc8c2febd9686377a12aa148dc70960267080c8b", "__CURRENT_CONTINUATION__"),
    ("wave96", "__PREVIOUS_WAVE__"),
    ("wave97", "__CURRENT_WAVE__"),
    ("0071_", "__PREVIOUS_QUEUE__"),
    ("0072_", "__CURRENT_QUEUE__"),
    ("21910", "__ROWS_OLD_PREVIOUS__"),
    ("22360", "__ROWS_BASE__"),
    ("22810", "__ROWS_TARGET__"),
    ("21242", "__MIN_OLD_PREVIOUS__"),
    ("21670", "__MIN_CURRENT__"),
    ("22081", "__ACCURACY_BASE__"),
    ("52672", "__PARCEL_OLD_START__"),
    ("53122", "__PARCEL_START__"),
    ("53572", "__PARCEL_END_PLUS_ONE__"),
    ("53121", "__PARCEL_OLD_END__"),
    ("53571", "__PARCEL_END__"),
    ("2.01", "__DELTA_PREVIOUS__"),
    ("1.97", "__DELTA_CURRENT__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_TRANSFORM_FRAGMENT_MISSING: {old}")
    text = text.replace(old, token)


def replace_last(value: str, old: str, new: str) -> str:
    prefix, separator, suffix = value.rpartition(old)
    if not separator:
        raise SystemExit(f"ORCHESTRATOR_ADVANCE_VALUE_MISSING:{old}")
    return prefix + new + suffix


tree = ast.parse(text, filename=str(source))
direct_assignments = [
    node
    for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "direct" for target in node.targets)
]
if len(direct_assignments) != 1:
    raise SystemExit(f"ORCHESTRATOR_DIRECT_ASSIGNMENT_COUNT_INVALID:{len(direct_assignments)}")
direct_value = direct_assignments[0].value
if not isinstance(direct_value, ast.List) or len(direct_value.elts) != 10:
    raise SystemExit("ORCHESTRATOR_DIRECT_LIST_SHAPE_INVALID")

advance_rules = [
    (("schema_version", "74", "75"), (("75", "76"), ("74", "75"))),
    (("schema_version", "115", "120"), (("120", "121"),)),
    (("schema_version", "119", "124"), (("124", "125"),)),
    (("schema_version", "114", "119"), (("119", "120"),)),
    (("or 141", "or 146"), (("146", "147"),)),
    (("priority", "-168", "-173"), (("-173", "-174"),)),
    (("97.81", "98.03"), (("98.03", "98.07"),)),
    (("expanded_scope_progress_percent", "98.03"), (("98.03", "98.07"),)),
    (("WAVE92", "WAVE97"), (("WAVE97", "WAVE98"),)),
    (("WAVE97_REMOTE_TERMINAL_READBACK_FAILED",), (("WAVE97", "WAVE98"),)),
]

shift_entries: list[ast.expr] = []
for index, (entry, rule) in enumerate(zip(direct_value.elts, advance_rules, strict=True)):
    if not isinstance(entry, ast.Tuple) or len(entry.elts) != 2:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_ENTRY_SHAPE_INVALID:{index}")
    old_node, new_node = entry.elts
    if not isinstance(old_node, ast.Constant) or not isinstance(old_node.value, str):
        raise SystemExit(f"ORCHESTRATOR_DIRECT_OLD_INVALID:{index}")
    if not isinstance(new_node, ast.Constant) or not isinstance(new_node.value, str):
        raise SystemExit(f"ORCHESTRATOR_DIRECT_NEW_INVALID:{index}")

    markers, replacements = rule
    current_new = new_node.value
    if not all(marker in current_new for marker in markers):
        raise SystemExit(f"ORCHESTRATOR_DIRECT_MARKER_MISSING:{index}:{markers}")
    next_new = current_new
    for old, new in replacements:
        next_new = replace_last(next_new, old, new)

    old_literal_source = ast.get_source_segment(text, old_node)
    new_literal_source = ast.get_source_segment(text, new_node)
    if old_literal_source is None or new_literal_source is None:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_SOURCE_SEGMENT_MISSING:{index}")
    next_literal_source = repr(next_new)

    # Advance the current new literal first, then shift the old literal into its place.
    shift_entries.append(
        ast.Tuple(
            elts=[ast.Constant(value=new_literal_source), ast.Constant(value=next_literal_source)],
            ctx=ast.Load(),
        )
    )
    shift_entries.append(
        ast.Tuple(
            elts=[ast.Constant(value=old_literal_source), ast.Constant(value=new_literal_source)],
            ctx=ast.Load(),
        )
    )

direct_value.elts = shift_entries

required_assignments = [
    node
    for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "required" for target in node.targets)
]
if len(required_assignments) != 1:
    raise SystemExit(f"ORCHESTRATOR_REQUIRED_ASSIGNMENT_COUNT_INVALID:{len(required_assignments)}")
required_value = required_assignments[0].value
if not isinstance(required_value, ast.List):
    raise SystemExit("ORCHESTRATOR_REQUIRED_LIST_SHAPE_INVALID")
for index, node in enumerate(required_value.elts):
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        raise SystemExit(f"ORCHESTRATOR_REQUIRED_ENTRY_INVALID:{index}")
    node.value = node.value.replace("\\", "")

ast.fix_missing_locations(tree)
text = ast.unparse(tree) + "\n"
validation_needle = "if fragment not in text:"
if text.count(validation_needle) != 1:
    raise SystemExit(f"ORCHESTRATOR_REQUIRED_LOOP_COUNT_INVALID:{text.count(validation_needle)}")
text = text.replace(
    validation_needle,
    "if fragment not in text.replace('\\\\', ''):",
    1,
)

resolved = [
    ("__SOURCE_HEAD__", "3976839fb696d3dfd0eedfd59c87f7bfdeb8a230"),
    ("__PREVIOUS_CONTINUATION__", "8c0d233f0b4e80b52f2d50fcfc8c2febd9686377a12aa148dc70960267080c8b"),
    ("__CURRENT_CONTINUATION__", "36f1b43ca5fd4ff3e2e79e5d3d960a8c479f5cbd20d4db374d9be4305030f1d3"),
    ("__PREVIOUS_WAVE__", "wave97"),
    ("__CURRENT_WAVE__", "wave98"),
    ("__PREVIOUS_QUEUE__", "0072_"),
    ("__CURRENT_QUEUE__", "0073_"),
    ("__ROWS_OLD_PREVIOUS__", "22360"),
    ("__ROWS_BASE__", "22810"),
    ("__ROWS_TARGET__", "23260"),
    ("__MIN_OLD_PREVIOUS__", "21670"),
    ("__MIN_CURRENT__", "22097"),
    ("__ACCURACY_BASE__", "22522"),
    ("__PARCEL_OLD_START__", "53122"),
    ("__PARCEL_START__", "53572"),
    ("__PARCEL_END_PLUS_ONE__", "54022"),
    ("__PARCEL_OLD_END__", "53571"),
    ("__PARCEL_END__", "54021"),
    ("__DELTA_PREVIOUS__", "1.97"),
    ("__DELTA_CURRENT__", "1.93"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

validation_text = text.replace("\\", "")
required_semantics = [
    '3976839fb696d3dfd0eedfd59c87f7bfdeb8a230',
    'EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_22810_TO_23260_ROWS_WITH_OFFICIAL_SOURCE_HASHES',
    '36f1b43ca5fd4ff3e2e79e5d3d960a8c479f5cbd20d4db374d9be4305030f1d3',
    'security_public_safety_2_priority_23260row_incremental_evidence_expansion_20260731',
    'github-actions-security-public-safety-2-wave98',
    '0073_security_public_safety_2_priority_23260row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave98_latest.json',
    'priority_23260row_evidence_expansion_latest.json',
    '"accepted_base_rows": 22810',
    '"merged_candidate_rows": 23260',
    '"minimum_merged_police_hash_rows": 22097',
    '"incremental_parcel_start": 53572',
    '"incremental_parcel_end": 54021',
    '"expanded_scope_progress_percent": 98.07',
    '"expanded_scope_delta_percentage_points": 1.93',
    'len(rows) != 23260',
    '"parcel_54021"',
    'WAVE98_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required_semantics:
    if fragment not in validation_text:
        raise SystemExit(f"ORCHESTRATOR_SEMANTIC_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})
