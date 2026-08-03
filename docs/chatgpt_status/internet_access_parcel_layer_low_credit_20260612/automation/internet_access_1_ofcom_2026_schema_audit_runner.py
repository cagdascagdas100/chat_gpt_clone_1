from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_portable_root(repo_root: Path) -> Path:
    configured = os.environ.get("AAYS_PORTABLE_ROOT")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if not _is_within(candidate, repo_root):
            return candidate

    for candidate in (repo_root, *repo_root.parents):
        if candidate.name.casefold() == "terrayield_aays_portable":
            resolved = candidate.resolve()
            if not _is_within(resolved, repo_root):
                return resolved

    fallback = (Path(tempfile.gettempdir()) / "aays_terrayield_runtime").resolve()
    if _is_within(fallback, repo_root):
        raise RuntimeError("INTERNET_ACCESS_1_CACHE_ROOT_INSIDE_REPOSITORY")
    return fallback


def main() -> int:
    repo_root = Path.cwd().resolve()
    script = repo_root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/internet_access_1_ofcom_2026_schema_audit.py"
    output = repo_root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_1/ofcom_2026_schema_audit_latest.json"
    portable_root = resolve_portable_root(repo_root)
    cache_dir = portable_root / "runtime/internet_access_1/source_cache"
    if _is_within(cache_dir.resolve(), repo_root):
        raise RuntimeError("INTERNET_ACCESS_1_CACHE_DIR_INSIDE_REPOSITORY")
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
    print(f"INTERNET_ACCESS_1_CACHE_DIR={cache_dir}")
    print(f"INTERNET_ACCESS_1_OFCom_SCHEMA_AUDIT_EXIT_CODE={completed.returncode}")
    print("FINAL_READY=false")
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
