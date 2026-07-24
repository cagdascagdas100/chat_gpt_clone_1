#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable

MAX_MEMBER_BYTES = 20_000_000
MAX_EXTRACTED_BYTES = 600_000_000


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {"command": command, "exit_code": process.returncode, "stdout": process.stdout[-8000:], "stderr": process.stderr[-8000:]}


def _safe_extract_archives(archives: list[Path], root: Path) -> list[str]:
    root.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    total = 0
    for archive_index, archive in enumerate(archives, start=1):
        if not archive.is_file() or not zipfile.is_zipfile(archive):
            raise ValueError(f"Terrain50 archive invalid: {archive}")
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                if info.is_dir() or Path(info.filename).suffix.casefold() not in {".asc", ".txt"}:
                    continue
                path = Path(info.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError(f"unsafe Terrain50 archive member: {info.filename}")
                if info.file_size <= 0 or info.file_size > MAX_MEMBER_BYTES:
                    raise ValueError(f"Terrain50 member size invalid: {info.filename}")
                total += info.file_size
                if total > MAX_EXTRACTED_BYTES:
                    raise ValueError("Terrain50 extracted data exceeds safety limit")
                target = root / f"a{archive_index}_{path.name}"
                with zf.open(info) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
                written.append(str(target))
    if not written:
        raise ValueError("no Terrain50 ASCII grid files extracted")
    return written


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--hmlr-exact-matches", type=Path, required=True)
    parser.add_argument("--ea-samples", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--terrain50-archive", type=Path)
    parser.add_argument("--terrain50-root", type=Path)
    args = parser.parse_args(argv)
    stages: list[dict[str, Any]] = []
    try:
        repo_root = args.repo_root.resolve()
        automation = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/automation"
        resolver = automation / "015_resolve_os_terrain50_downloads.py"
        crosschecker = automation / "013_crosscheck_os_terrain50.py"
        if not resolver.is_file() or not crosschecker.is_file():
            raise FileNotFoundError("Terrain50 resolver or crosschecker missing")
        archive = args.terrain50_archive or (Path(os.environ["AAYS_TERRAIN50_ARCHIVE"]) if os.environ.get("AAYS_TERRAIN50_ARCHIVE") else None)
        root = args.terrain50_root or (Path(os.environ["AAYS_TERRAIN50_ROOT"]) if os.environ.get("AAYS_TERRAIN50_ROOT") else None)
        if archive:
            source_kind, source_value = "configured_archive", archive
        elif root:
            source_kind, source_value = "configured_root", root
        else:
            resolver_output_dir = args.output_dir / "downloads"
            resolver_manifest = args.output_dir / "terrain50_download_manifest.json"
            resolver_stage = _run([sys.executable, str(resolver), "--hmlr-exact-matches", str(args.hmlr_exact_matches), "--output-dir", str(resolver_output_dir), "--output", str(resolver_manifest)], repo_root)
            resolver_stage["stage"] = "OS_DOWNLOADS_API_TERRAIN50_RESOLUTION"
            stages.append(resolver_stage)
            if resolver_stage["exit_code"] != 0:
                raise RuntimeError("OS Downloads API Terrain50 resolution failed")
            manifest = json.loads(resolver_manifest.read_text(encoding="utf-8-sig"))
            archives = [Path(value) for value in manifest.get("archive_paths", [])]
            if not archives:
                raise ValueError("Terrain50 resolver returned no archives")
            extracted_root = args.output_dir / "resolved_ascii_root"
            extracted = _safe_extract_archives(archives, extracted_root)
            stages.append({"stage": "TERRAIN50_MULTI_ARCHIVE_SAFE_EXTRACTION", "exit_code": 0, "archive_count": len(archives), "ascii_grid_file_count": len(extracted), "root": str(extracted_root)})
            source_kind, source_value = "os_downloads_api_resolved_root", extracted_root
        command = [sys.executable, str(crosschecker), "--hmlr-exact-matches", str(args.hmlr_exact_matches), "--ea-samples", str(args.ea_samples), "--work-dir", str(args.output_dir / "crosscheck_work"), "--output", str(args.output)]
        if source_kind == "configured_archive":
            command.extend(["--terrain50-archive", str(source_value)])
        else:
            command.extend(["--terrain50-root", str(source_value)])
        crosscheck_stage = _run(command, repo_root)
        crosscheck_stage["stage"] = "OS_TERRAIN50_POLYGON_CROSSCHECK"
        stages.append(crosscheck_stage)
        if crosscheck_stage["exit_code"] != 0:
            raise RuntimeError("OS Terrain50 polygon crosscheck failed")
        payload = json.loads(args.output.read_text(encoding="utf-8-sig"))
        payload["source_resolution_kind"] = source_kind
        payload["preparation_stages"] = stages
        payload["os_downloads_api_used"] = source_kind == "os_downloads_api_resolved_root"
        _write(args.output, payload)
        code = 0
    except Exception as exc:
        payload = {"schema_version": 1, "slot_id": "height_difference_2", "status": "BLOCKED_TERRAIN50_PREPARATION_OR_CROSSCHECK", "error": f"{type(exc).__name__}: {exc}", "preparation_stages": stages, "crosscheck_count": 0, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
        _write(args.output, payload)
        code = 2
    print(json.dumps({"ok": code == 0, "status": payload.get("status"), "crosschecks": payload.get("crosscheck_count", 0)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
