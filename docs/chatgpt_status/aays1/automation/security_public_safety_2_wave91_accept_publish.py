from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
old_queue = "0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json"
old_continuation = "2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae"
old_owner = "github-actions-security-public-safety-2-wave32"
for fragment in (old_queue, old_continuation, old_owner, "wave32"):
    if fragment not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {fragment}")

text = text.replace(old_queue, "__WAVE71_QUEUE__")
text = text.replace(old_continuation, "__WAVE71_CONTINUATION__")
text = text.replace(old_owner, "github-actions-security-public-safety-2-wave91")
text = text.replace("wave32", "wave91")
if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "20110")
text = text.replace("__WAVE71_QUEUE__", "0066_security_public_safety_2_priority_20110row_incremental_evidence_expansion_20260730.v3.task.json")
text = text.replace("__WAVE71_CONTINUATION__", "a3efcf9d82e085183979087a1bf0d2ea905fa427d3009fdccd73ac023f01ce92")

required_replacements = [
    ("range(30762, 31352)", "range(30762, 50872)"),
    ("parcel_31351", "parcel_50871"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 19105"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 2.24'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 19660'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 450'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 450'),
    ("security_public_safety_2_priority_20110row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_20110row_incremental_evidence_expansion_20260730"),
    ("priority_20110row_browser_acceptance_wave91_receipt_20260729.json", "priority_20110row_browser_acceptance_wave91_receipt_20260730.json"),
    ("priority_20110row_targeted_retry_wave91_diagnostic_20260729.json", "priority_20110row_targeted_retry_wave91_diagnostic_20260730.json"),
]
for old, new in required_replacements:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

old_gate = '    if any(gate.get("state") != "PASS" for gate in gates[:12]):\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
new_gate = '    failed_gates = [gate for gate in gates[:12] if gate.get("state") != "PASS"]\n    if failed_gates:\n        print("PRE_BROWSER_FAILED_GATES=" + __import__("json").dumps(failed_gates, ensure_ascii=False, sort_keys=True))\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
if old_gate in text:
    text = text.replace(old_gate, new_gate)

old_dom = """            locator = page.locator("xpath=//h2[contains(normalize-space(.),'20110 örnek satır')]/following-sibling::table[1]/tbody/tr")
            dom_rows = locator.count()"""
new_dom = """            locator = page.locator("xpath=//h2[contains(normalize-space(.),'20110 örnek satır')]/following-sibling::table[1]/tbody/tr")
            dom_rows = locator.count()
            dom_deadline = time.time() + 180
            while dom_rows < 20110 and time.time() < dom_deadline:
                page.wait_for_timeout(250)
                dom_rows = locator.count()"""
if old_dom not in text:
    raise SystemExit("DOM_WAIT_FRAGMENT_MISSING")
text = text.replace(old_dom, new_dom)

required = [
    'CONTINUATION_KEY = "a3efcf9d82e085183979087a1bf0d2ea905fa427d3009fdccd73ac023f01ce92"',
    '0066_security_public_safety_2_priority_20110row_incremental_evidence_expansion_20260730.v3.task.json',
    'OWNER = "github-actions-security-public-safety-2-wave91"',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"FINAL_ACCEPTANCE_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
