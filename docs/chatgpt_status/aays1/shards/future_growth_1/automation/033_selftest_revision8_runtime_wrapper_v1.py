#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "032_validate_revision8_runtime_wrapper_v1.py"
WRAPPER = HERE.parents[2] / "automation/future_growth_1_official_geometry_entry_v8_runtime.py"
spec = importlib.util.spec_from_file_location("validator", TARGET)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def case(name, text, expected):
    actual = mod.validate_text(text)["result"]
    return {"name": name, "expected": expected, "actual": actual, "pass": actual == expected}


def main() -> int:
    exact = WRAPPER.read_text(encoding="utf-8")
    cases = [
        case("exact_bounded_wrapper", exact, "PASS"),
        case("missing_bootstrap", exact.replace("future_growth_1_official_geometry_entry_v8_bootstrap.py", "removed.py"), "FAIL"),
        case("missing_stall_validator", exact.replace("040_validate_revision8_stall_state_v1.py", "removed.py"), "FAIL"),
        case("missing_stall_selftest", exact.replace("041_selftest_revision8_stall_state_v1.py", "removed.py"), "FAIL"),
        case("unbounded_core_timeout", exact.replace('"core_pipeline": 4500', '"core_pipeline": 999999'), "FAIL"),
        case("missing_windows_tree_kill", exact.replace('["taskkill", "/PID", str(proc.pid), "/T", "/F"]', '["taskkill"]'), "FAIL"),
        case("missing_posix_tree_kill", exact.replace("os.killpg(proc.pid, signal.SIGKILL)", "proc.kill()"), "FAIL"),
        case("missing_timeout_handler", exact.replace("except subprocess.TimeoutExpired", "except RuntimeError"), "FAIL"),
        case("missing_stall_bounded_call", exact.replace('run_bounded([sys.executable, str(STALL_VALIDATOR)', 'run_unbounded([sys.executable, str(STALL_VALIDATOR)'), "FAIL"),
        case("missing_core_bounded_call", exact.replace('run_bounded([sys.executable, str(CORE_BOOTSTRAP)', 'run_unbounded([sys.executable, str(CORE_BOOTSTRAP)'), "FAIL"),
        case("direct_network", exact + "\n# urlopen(unsafe)\n", "FAIL"),
        case("business_claim", exact + '\n# business_progress_claimed": True\n', "FAIL"),
    ]
    passed = sum(item["pass"] for item in cases)
    output = {"schema_version": 4, "slot_id": "future_growth_1", "selftest_kind": "REVISION8_STALL_RESISTANT_BOUNDED_RUNTIME", "result": f"{passed}/{len(cases)} PASS", "passed": passed, "total": len(cases), "cases": cases, "runner_execution_claimed": False, "business_progress_claimed": False, "final_ready": False}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if passed == len(cases) else 2


if __name__ == "__main__":
    raise SystemExit(main())
