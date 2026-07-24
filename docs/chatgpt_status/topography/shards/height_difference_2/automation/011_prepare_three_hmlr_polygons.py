#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-8000:],
        "stderr": process.stderr[-8000:],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--download-page", default="https://use-land-property-data.service.gov.uk/datasets/inspire/download")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--resolve-only", action="store_true")
    parser.add_argument("--page-html", type=Path)
    args = parser.parse_args(argv)

    script_root = Path(__file__).resolve().parent
    adapter = script_root / "008_adapt_candidate_seeds_to_starter_manifest.py"
    downloader = script_root / "009_prepare_hmlr_inspire_sources.py"
    matcher = script_root / "010_match_hmlr_exact_polygons.py"
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    starter = output_dir / "starter_manifest.json"
    stages: list[dict[str, Any]] = []

    result = _run(
        [sys.executable, str(adapter), "--seed-manifest", str(args.seed_manifest), "--output", str(starter)],
        script_root,
    )
    result["stage"] = "ADAPT_CANONICAL_SEEDS"
    stages.append(result)
    if result["exit_code"] != 0:
        status = "BLOCKED_ADAPT_CANONICAL_SEEDS"
        code = 2
    else:
        command = [
            sys.executable,
            str(downloader),
            "--starter-manifest",
            str(starter),
            "--output-dir",
            str(output_dir / "sources"),
            "--download-page",
            args.download_page,
            "--timeout",
            str(args.timeout),
        ]
        if args.resolve_only:
            command.append("--resolve-only")
        if args.page_html:
            command.extend(["--page-html", str(args.page_html)])
        result = _run(command, script_root)
        result["stage"] = "PREPARE_HMLR_SOURCES"
        stages.append(result)
        if result["exit_code"] != 0:
            status = "BLOCKED_PREPARE_HMLR_SOURCES"
            code = 2
        elif args.resolve_only:
            status = "HMLR_URLS_RESOLVED_AWAITING_DOWNLOAD"
            code = 0
        else:
            result = _run(
                [
                    sys.executable,
                    str(matcher),
                    "--starter-manifest",
                    str(starter),
                    "--vector-root",
                    str(output_dir / "sources" / "hmlr"),
                    "--output",
                    str(output_dir / "hmlr_exact_matches.json"),
                ],
                script_root,
            )
            result["stage"] = "MATCH_HMLR_EXACT_POLYGONS"
            stages.append(result)
            code = result["exit_code"]
            status = "THREE_HMLR_EXACT_POLYGONS_READY" if code == 0 else "BLOCKED_MATCH_HMLR_EXACT_POLYGONS"

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "status": status,
        "stages": stages,
        "starter_manifest": str(starter),
        "hmlr_source_manifest": str(output_dir / "sources" / "hmlr_source_manifest.json"),
        "hmlr_exact_matches": str(output_dir / "hmlr_exact_matches.json"),
        "next_step": "SAMPLE_EA_DTM1M_WITHIN_EXACT_POLYGONS_THEN_OS_TERRAIN50_CROSSCHECK",
        "single_shared_runner_only": True,
        "new_runner": False,
        "parallel_runner": False,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write(output_dir / "hmlr_polygon_preparation_execution.json", payload)
    print(json.dumps({"ok": code == 0, "status": status}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
