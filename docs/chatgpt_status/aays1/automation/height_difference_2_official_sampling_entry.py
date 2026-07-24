from __future__ import annotations

import base64
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
EXPECTED_BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_PAGE_KEY = "aays1"
REQUIRED_MODULES = ("requests", "numpy", "rasterio", "pyproj", "shapely", "lxml")
EXPANDED_BUNDLE_REL = Path(
    "docs/chatgpt_status/topography/shards/height_difference_2/automation/"
    "004_height_difference_2_expanded_discovery_bundle.tar.gz.b64"
)
EXPANDED_BUNDLE_SHA256 = "f538891f2ed8053ef845b40328599ea694f4cceb4b190cd8a5b9b6a247982f2a"
EXPANDED_MEMBER_NAMES = {
    "004_discover_canonical_via_github_tree.py",
    "005_capture_validate_os_terrain50_download.py",
    "006_execute_expanded_discovery.py",
}


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


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def _safe_extract_bundle(bundle_bytes: bytes, target: Path) -> None:
    digest = hashlib.sha256(bundle_bytes).hexdigest()
    if digest != EXPANDED_BUNDLE_SHA256:
        raise ValueError("HEIGHT_DIFFERENCE_2_EXPANDED_BUNDLE_SHA256_MISMATCH")
    archive_path = target.parent / "expanded_discovery_bundle.tar.gz"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(bundle_bytes)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        names = {member.name for member in members}
        if names != EXPANDED_MEMBER_NAMES:
            raise ValueError("HEIGHT_DIFFERENCE_2_EXPANDED_BUNDLE_MEMBER_SET_MISMATCH")
        for member in members:
            parts = Path(member.name).parts
            if member.islnk() or member.issym() or Path(member.name).is_absolute() or ".." in parts:
                raise ValueError("HEIGHT_DIFFERENCE_2_EXPANDED_BUNDLE_UNSAFE_MEMBER")
        archive.extractall(target, filter="data")


def _split_env(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    values = []
    for line in raw.replace(";", "\n").splitlines():
        value = line.strip()
        if value:
            values.append(value)
    return list(dict.fromkeys(values))


def _run_expanded_discovery(repo_root: Path, portable_root: Path) -> dict[str, object]:
    bundle_path = repo_root / EXPANDED_BUNDLE_REL
    output_root = (
        repo_root
        / "docs"
        / "chatgpt_status"
        / "topography"
        / "shards"
        / "height_difference_2"
        / "runner_outputs"
        / "004_expanded_discovery_latest"
    )
    wrapper_output = output_root / "expanded_discovery_entrypoint.json"
    result: dict[str, object] = {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "bundle_path": str(bundle_path),
        "bundle_sha256_expected": EXPANDED_BUNDLE_SHA256,
        "single_shared_runner_only": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    try:
        if not bundle_path.is_file():
            raise FileNotFoundError("HEIGHT_DIFFERENCE_2_EXPANDED_BUNDLE_NOT_FOUND")
        bundle_bytes = base64.b64decode(bundle_path.read_text(encoding="utf-8").strip(), validate=True)
        script_dir = portable_root / "data" / "topography" / "automation" / "height_difference_2_expanded"
        _safe_extract_bundle(bundle_bytes, script_dir)
        command = [
            sys.executable,
            str(script_dir / "006_execute_expanded_discovery.py"),
            "--output-dir",
            str(output_root),
            "--repository",
            "cagdascagdas100/chat_gpt_clone_1",
            "--ref",
            EXPECTED_BRANCH,
        ]
        for value in _split_env("AAYS_TERRAIN50_HARS"):
            command.extend(["--terrain50-har", value])
        for value in _split_env("AAYS_TERRAIN50_URLS"):
            command.extend(["--terrain50-url", value])
        if os.environ.get("AAYS_TERRAIN50_DOWNLOAD", "").strip().lower() in {"1", "true", "yes"}:
            command.append("--download-terrain50")
        process = subprocess.run(command, cwd=script_dir, text=True, capture_output=True, check=False)
        result.update(
            {
                "status": "EXPANDED_DISCOVERY_EXECUTED",
                "command": command,
                "exit_code": process.returncode,
                "stdout": process.stdout[-8000:],
                "stderr": process.stderr[-8000:],
                "bundle_sha256_actual": hashlib.sha256(bundle_bytes).hexdigest(),
                "script_member_count": len(EXPANDED_MEMBER_NAMES),
            }
        )
    except Exception as exc:
        result.update(
            {
                "status": "BLOCKED_EXPANDED_DISCOVERY_ENTRYPOINT",
                "exit_code": 2,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
    _write_json(wrapper_output, result)
    return result


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
    expanded_result = _run_expanded_discovery(repo_root, portable_root)
    os.environ["AAYS_HEIGHT_DIFFERENCE_2_EXPANDED_DISCOVERY_STATUS"] = str(expanded_result.get("status", "UNKNOWN"))

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
