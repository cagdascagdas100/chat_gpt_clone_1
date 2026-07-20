from __future__ import annotations

import base64
import gzip
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
EXPECTED_BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_PAGE_KEY = "aays1"
REQUIRED_MODULES = ("requests", "numpy", "rasterio", "pyproj", "shapely", "lxml")


def _repo_root() -> Path:
    configured = os.environ.get("AAYS_REPO_ROOT", "").strip()
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _portable_root(repo_root: Path) -> Path:
    normalized = str(repo_root).replace("/", "\\")
    marker = "\\runner_system\\"
    idx = normalized.lower().find(marker)
    if idx >= 0:
        return Path(normalized[:idx])
    return repo_root.parent


def _ensure_dependencies(package_root: Path) -> None:
    package_root.mkdir(parents=True, exist_ok=True)
    package_text = str(package_root)
    if package_text not in sys.path:
        sys.path.insert(0, package_text)
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except ImportError:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-input",
                    "--upgrade",
                    "--target",
                    package_text,
                    module,
                ]
            )
            importlib.invalidate_caches()
            importlib.import_module(module)


def _sync_web_outputs(repo_root: Path) -> None:
    legacy = repo_root / "england_map_web" / "data" / "aays_18_slots" / "height_difference_2"
    canonical = repo_root / "england_map_web" / "data" / "aays_21_slots" / "height_difference_2"
    canonical.mkdir(parents=True, exist_ok=True)
    for filename in ("operations_latest.json", "candidates_latest.json", "status_latest.json", "index.html"):
        source = legacy / filename
        if source.is_file():
            shutil.copy2(source, canonical / filename)


def main() -> int:
    branch = os.environ.get("AAYS_TARGET_BRANCH", "").strip()
    if branch and branch != EXPECTED_BRANCH:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_BRANCH")
    page_key = os.environ.get("AAYS_PAGE_KEY", "").strip()
    if page_key and page_key != EXPECTED_PAGE_KEY:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_PAGE_KEY")

    repo_root = _repo_root()
    portable_root = _portable_root(repo_root)
    package_root = portable_root / "data" / "topography" / "python_packages" / "height_difference_2_official_sampling"
    _ensure_dependencies(package_root)

    payload_path = (
        repo_root
        / "docs"
        / "chatgpt_status"
        / "topography"
        / "shards"
        / "height_difference_2"
        / "automation"
        / "003_height_difference_2_canonical_export_official_sampling_20260720.py.gz.b64"
    )
    if not payload_path.is_file():
        raise FileNotFoundError("HEIGHT_DIFFERENCE_2_PAYLOAD_NOT_FOUND")

    os.environ["AAYS_TASK_ID"] = TASK_ID
    os.environ["AAYS_PORTABLE_ROOT"] = str(portable_root)
    os.environ["AAYS_HEIGHT_DIFFERENCE_2_PACKAGE_ROOT"] = str(package_root)

    encoded = payload_path.read_text(encoding="utf-8").strip()
    source = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    payload_globals = {
        "__name__": "__main__",
        "__file__": str(payload_path.with_suffix(".py")),
        "__package__": None,
    }
    exit_code = 0
    try:
        exec(compile(source, payload_globals["__file__"], "exec"), payload_globals)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    finally:
        _sync_web_outputs(repo_root)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
