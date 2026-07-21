from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_ENTRY = HERE / "security_public_safety_1_worker_entry_v5.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    base = load_module(BASE_ENTRY, "security_public_safety_1_worker_entry_v5_base")
    base.CANDIDATE_LIMIT = 50
    base.EXPECTED_UNIQUE_ENDPOINTS = 8
    return int(base.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
