from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path.cwd().resolve()
    script = repo_root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/internet_access_1_ofcom_2026_schema_audit.py"
    output = repo_root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_1/ofcom_2026_schema_audit_latest.json"
    portable_root = Path(os.environ.get("AAYS_PORTABLE_ROOT", str(repo_root))).resolve()
    cache_dir = portable_root / "runtime/internet_access_1/source_cache"
    command = [
        sys.executable,
        str(script),
        "--repo-root",
        str(repo_root),
        "--output",
        str(output),
        "--cache-dir",
        str(cache_dir),
        "--count-rows",
    ]
    completed = subprocess.run(command, cwd=repo_root, check=False)
    print(f"INTERNET_ACCESS_1_OFCom_SCHEMA_AUDIT_EXIT_CODE={completed.returncode}")
    print("FINAL_READY=false")
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
