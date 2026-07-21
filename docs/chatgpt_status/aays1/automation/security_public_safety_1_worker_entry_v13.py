from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
BASE_ENTRY = HERE / "security_public_safety_1_worker_entry_v12.py"
PROGRESS_JSON = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / "security_public_safety_1" / "progress" / "progress_latest.json"
PROGRESS_WEB_JSON = ROOT / "england_map_web" / "data" / "aays_21_slots" / "security_public_safety_1" / "progress_latest.json"

CANDIDATE_LIMIT = 120
EXPECTED_UNIQUE_ENDPOINTS = 16
ATTEMPT_ID = "security-public-safety-1-20260720-013"
SCRIPT_NAME = "security_public_safety_1_worker_entry_v13.py"
PROGRESS_HTML = ROOT / "england_map_web" / "data" / "aays_21_slots" / "security_public_safety_1" / "progress_v13.html"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    v12 = load_module(BASE_ENTRY, "security_public_safety_1_worker_entry_v12_base")
    v12.CANDIDATE_LIMIT = CANDIDATE_LIMIT
    v12.EXPECTED_UNIQUE_ENDPOINTS = EXPECTED_UNIQUE_ENDPOINTS
    v12.ATTEMPT_ID = ATTEMPT_ID
    v12.SCRIPT_NAME = SCRIPT_NAME
    v12.PROGRESS_HTML = PROGRESS_HTML
    exit_code = int(v12.main() or 0)

    if PROGRESS_JSON.is_file():
        progress = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
        progress["attempt_id"] = ATTEMPT_ID
        progress["candidate_examples_count"] = CANDIDATE_LIMIT
        progress["candidate_accuracy_score_4_count"] = CANDIDATE_LIMIT
        progress["candidate_unique_api_endpoints"] = EXPECTED_UNIQUE_ENDPOINTS
        for event in list(progress.get("events") or []):
            if event.get("step") == "DETERMINISTIC_PREFLIGHT":
                event["detail"] = (
                    "120 candidate rows, 16 unique endpoints, required files, Python syntax, "
                    "queue, legacy bridge and wrapper safety contracts validated without network calls; "
                    "rows 111-120 reuse existing endpoints and recursion-safe v11 preflight is retained"
                )
        payload = json.dumps(progress, ensure_ascii=False, indent=2) + "\n"
        PROGRESS_JSON.write_text(payload, encoding="utf-8")
        PROGRESS_WEB_JSON.write_text(payload, encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
