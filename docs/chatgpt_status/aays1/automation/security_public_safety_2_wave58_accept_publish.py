from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")


def replace_required(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)


replace_required("590", "5920")
replace_required(
    "0007_security_public_safety_2_priority_5920row_incremental_evidence_expansion_20260729.v3.task.json",
    "0033_security_public_safety_2_priority_5920row_incremental_evidence_expansion_20260730.v3.task.json",
)
replace_required(
    "2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae",
    "a7ef9fdff7e5fb7bff3116a3f8b07f43f06302b62f048ac30ef73c7bb64ea6a5",
)
replace_required("wave32", "wave58")
replace_required("range(30762, 31352)", "range(30762, 36682)")
replace_required("parcel_31351", "parcel_36681")
replace_required("MIN_QUALITY = 561", "MIN_QUALITY = 5624")
replace_required('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 5.57')
replace_required('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 5590')
replace_required('"incremental_rows_target": 70', '"incremental_rows_target": 330')
replace_required('"incremental_rows_completed": 70', '"incremental_rows_completed": 330')
replace_required(
    "security_public_safety_2_priority_5920row_incremental_evidence_expansion_20260729",
    "security_public_safety_2_priority_5920row_incremental_evidence_expansion_20260730",
)
replace_required(
    "priority_5920row_browser_acceptance_wave58_receipt_20260729.json",
    "priority_5920row_browser_acceptance_wave58_receipt_20260730.json",
)
replace_required(
    "priority_5920row_targeted_retry_wave58_diagnostic_20260729.json",
    "priority_5920row_targeted_retry_wave58_diagnostic_20260730.json",
)

old_gate = '    if any(gate.get("state") != "PASS" for gate in gates[:12]):\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
new_gate = '    failed_gates = [gate for gate in gates[:12] if gate.get("state") != "PASS"]\n    if failed_gates:\n        print("PRE_BROWSER_FAILED_GATES=" + __import__("json").dumps(failed_gates, ensure_ascii=False, sort_keys=True))\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
replace_required(old_gate, new_gate)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
