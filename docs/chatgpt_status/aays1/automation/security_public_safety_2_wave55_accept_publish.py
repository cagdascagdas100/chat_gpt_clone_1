from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0030_security_public_safety_2_priority_4960row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "4c2891cdfb8bb260d9c088aa0fcf79e92c6230f45ae22a4238f299ac8ce439e4"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave55"),
    ("wave32", "wave55"),
    ("590", "4960"),
    ("range(30762, 31352)", "range(30762, 35722)"),
    ("parcel_31351", "parcel_35721"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 4712"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 6.05'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 4660'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 300'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 300'),
    ("security_public_safety_2_priority_4960row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_4960row_incremental_evidence_expansion_20260730"),
    ("priority_4960row_browser_acceptance_wave55_receipt_20260729.json", "priority_4960row_browser_acceptance_wave55_receipt_20260730.json"),
    ("priority_4960row_targeted_retry_wave55_diagnostic_20260729.json", "priority_4960row_targeted_retry_wave55_diagnostic_20260730.json"),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "4960")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

old_gate_block = '''    if any(gate.get("state") != "PASS" for gate in gates[:12]):
        raise SystemExit("PRE_BROWSER_GATES_FAILED")'''
new_gate_block = '''    failed_pre_browser = [gate for gate in gates[:12] if gate.get("state") != "PASS"]
    if failed_pre_browser:
        print("PRE_BROWSER_FAILED_GATES=" + json.dumps(failed_pre_browser, ensure_ascii=False, sort_keys=True))
        raise SystemExit("PRE_BROWSER_GATES_FAILED")'''
if old_gate_block not in text:
    raise SystemExit("EXPECTED_PRE_BROWSER_GATE_BLOCK_MISSING")
text = text.replace(old_gate_block, new_gate_block)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
