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
text = text.replace(old_owner, "github-actions-security-public-safety-2-wave99")
text = text.replace("wave32", "wave99")
if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "23710")
text = text.replace("__WAVE71_QUEUE__", "0074_security_public_safety_2_priority_23710row_incremental_evidence_expansion_20260731.v3.task.json")
text = text.replace("__WAVE71_CONTINUATION__", "589db0e5285d9801cbc1a038b3768ae1440605f34d6b88208e4319213abc3e0e")

required_replacements = [
    ("range(30762, 31352)", "range(30762, 54472)"),
    ("parcel_31351", "parcel_54471"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 22525"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 1.90'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 23260'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 450'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 450'),
    ("security_public_safety_2_priority_23710row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_23710row_incremental_evidence_expansion_20260731"),
    ("priority_23710row_browser_acceptance_wave99_receipt_20260729.json", "priority_23710row_browser_acceptance_wave99_receipt_20260731.json"),
    ("priority_23710row_targeted_retry_wave99_diagnostic_20260729.json", "priority_23710row_targeted_retry_wave99_diagnostic_20260731.json"),
]
for old, new in required_replacements:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

old_gate = '    if any(gate.get("state") != "PASS" for gate in gates[:12]):\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
new_gate = '    failed_gates = [gate for gate in gates[:12] if gate.get("state") != "PASS"]\n    if failed_gates:\n        print("PRE_BROWSER_FAILED_GATES=" + __import__("json").dumps(failed_gates, ensure_ascii=False, sort_keys=True))\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
if old_gate in text:
    text = text.replace(old_gate, new_gate)

old_dom = """            locator = page.locator("xpath=//h2[contains(normalize-space(.),'23710 örnek satır')]/following-sibling::table[1]/tbody/tr")
            dom_rows = locator.count()"""
new_dom = """            locator = page.locator("xpath=//h2[contains(normalize-space(.),'23710 örnek satır')]/following-sibling::table[1]/tbody/tr")
            dom_rows = locator.count()
            dom_deadline = time.time() + 180
            while dom_rows < 23710 and time.time() < dom_deadline:
                page.wait_for_timeout(250)
                dom_rows = locator.count()"""
if old_dom not in text:
    raise SystemExit("DOM_WAIT_FRAGMENT_MISSING")
text = text.replace(old_dom, new_dom)

required = [
    'CONTINUATION_KEY = "589db0e5285d9801cbc1a038b3768ae1440605f34d6b88208e4319213abc3e0e"',
    '0074_security_public_safety_2_priority_23710row_incremental_evidence_expansion_20260731.v3.task.json',
    'OWNER = "github-actions-security-public-safety-2-wave99"',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"FINAL_ACCEPTANCE_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
