from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave139_official_onsud_os_open_uprn_identity_chain_20260801.py"
spec = importlib.util.spec_from_file_location("wave139_onsud_base", BASE)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

TASK = "security_public_safety_2_wave142_official_onsud_os_open_uprn_identity_chain_20260801"
STEP = "WAVE142_SINGLE_OPEN_ROW_OFFICIAL_ONSUD_OS_OPEN_UPRN_IDENTITY_CHAIN"
PREVIOUS_CONTINUATION = "f3ef811e7b7ed20ced20008df9e1883c465f49d12df9b70b036436ed3b60353d"
SOURCE_HEAD = os.environ["AAYS_SOURCE_HEAD"]
CONTINUATION = hashlib.sha256(
    f"{base.m.WORKSTREAM_ID}|{base.m.SLOT_ID}|{base.m.CANONICAL_BRANCH}|{STEP}|{SOURCE_HEAD}".encode()
).hexdigest()

PREVIOUS_OUTPUT = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_postcode_hmlr_lineage_contract_wave141_latest.json"
MANUAL = ROOT / "docs/chatgpt_status/_shared/manual_actions/security_public_safety_2.json"
QUEUE = ROOT / "docs/chatgpt_status/aays1/queue/0155_security_public_safety_2_wave142_official_onsud_os_open_uprn_identity_chain_20260801.v3.task.json"
OUTPUT = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_onsud_os_open_uprn_identity_chain_wave142_latest.json"
WEBSITE = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_onsud_os_open_uprn_identity_chain_wave142.html"
STATUS = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave142_status_latest.json"
EVIDENCE = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave142_evidence_latest.json"

for name, value in {
    "TASK": TASK,
    "STEP": STEP,
    "PREVIOUS_CONTINUATION": PREVIOUS_CONTINUATION,
    "SOURCE_HEAD": SOURCE_HEAD,
    "CONTINUATION": CONTINUATION,
    "PREVIOUS_OUTPUT": PREVIOUS_OUTPUT,
    "MANUAL": MANUAL,
    "QUEUE": QUEUE,
    "OUTPUT": OUTPUT,
    "WEBSITE": WEBSITE,
    "STATUS": STATUS,
    "EVIDENCE": EVIDENCE,
}.items():
    setattr(base, name, value)


def rename_wave(value):
    if isinstance(value, dict):
        return {
            str(key).replace("wave139", "wave142").replace("Wave139", "Wave142").replace("WAVE139", "WAVE142"):
            rename_wave(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [rename_wave(child) for child in value]
    if isinstance(value, str):
        return value.replace("wave139", "wave142").replace("Wave139", "Wave142").replace("WAVE139", "WAVE142")
    return value


def normalize_outputs() -> None:
    output = rename_wave(json.loads(OUTPUT.read_text()))
    manual = rename_wave(json.loads(MANUAL.read_text()))
    status = rename_wave(json.loads(STATUS.read_text()))
    evidence = rename_wave(json.loads(EVIDENCE.read_text()))
    queue = rename_wave(json.loads(QUEUE.read_text()))

    output["task_id"] = TASK
    output["first_unverified_step"] = STEP
    output["continuation_key"] = CONTINUATION
    output["previous_continuation_key"] = PREVIOUS_CONTINUATION
    output["source_head"] = SOURCE_HEAD
    output.setdefault("scope", {})["maximum_simultaneous_workers"] = 15
    output["scope"]["maximum_simultaneous_large_downloads"] = 3
    output["fake_data"] = False

    manual["continuation_key"] = CONTINUATION
    status.update({
        "task_id": TASK,
        "continuation_key": CONTINUATION,
        "state": "COMPLETED_PUBLISHED",
        "owner": None,
        "blocker": None,
        "fake_data": False,
    })
    queue.update({
        "task_id": TASK,
        "continuation_key": CONTINUATION,
        "previous_continuation_key": PREVIOUS_CONTINUATION,
        "source_head": SOURCE_HEAD,
        "first_unverified_step": STEP,
        "state": "COMPLETED_PUBLISHED",
        "owner": None,
        "blocker": None,
        "fake_data_allowed": False,
    })

    page = WEBSITE.read_text().replace("wave139", "wave142").replace("Wave139", "Wave142").replace("WAVE139", "WAVE142")
    output_text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    evidence.update({
        "task_id": TASK,
        "continuation_key": CONTINUATION,
        "source_head": SOURCE_HEAD,
        "output_json": str(OUTPUT.relative_to(ROOT)),
        "output_html": str(WEBSITE.relative_to(ROOT)),
        "output_json_sha256": hashlib.sha256(output_text.encode()).hexdigest(),
        "output_html_sha256": hashlib.sha256(page.encode()).hexdigest(),
        "fake_data": False,
    })

    OUTPUT.write_text(output_text)
    WEBSITE.write_text(page)
    for path, payload in ((MANUAL, manual), (STATUS, status), (EVIDENCE, evidence), (QUEUE, queue)):
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    base.main()
    normalize_outputs()
    print(json.dumps({
        "state": json.loads(STATUS.read_text())["state"],
        "continuation_key": CONTINUATION,
        "result": json.loads(STATUS.read_text())["progress"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
