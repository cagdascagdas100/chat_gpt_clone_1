#!/usr/bin/env python3
"""Resume height_difference_3 official-source processing from the first invalid artefact.

Runs inside one existing runner process. Completed stages are reused only after the
025 validator rechecks identity, counts, source hashes, raster contracts and publication.
At most two independent I/O stages run concurrently. No queue, lease or new runner is created.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("height_difference_3_resume_validator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def run_command(stage: str, command: list[str], cwd: Path) -> dict[str, Any]:
    started = utc_now()
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "stage": stage,
        "started_at": started,
        "finished_at": utc_now(),
        "command": command,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-16000:],
        "stderr_tail": proc.stderr[-16000:],
    }


def plan_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["stage"]): item for item in plan.get("stages") or []}


def is_valid(plan: dict[str, Any], stage: str) -> bool:
    item = plan_map(plan).get(stage)
    return bool(item and item.get("valid") is True and item.get("reusable") is True)


def read_archives(manifest_path: Path) -> list[Path]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    values = payload.get("archives") if isinstance(payload, dict) else None
    if not isinstance(values, list) or not values:
        raise ValueError("Terrain50 required-area manifest has no archives")
    result = []
    for value in values:
        path = Path(str(value.get("archive_path") or ""))
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        result.append(path)
    return result


class Execution:
    def __init__(self, args: argparse.Namespace, validator: Any) -> None:
        self.args = args
        self.validator = validator
        self.out = args.output_dir.resolve()
        self.script_dir = args.script_dir.resolve()
        self.source = args.security_geojson.resolve()
        self.execution_path = self.out / "resumable_targeted_source_execution.json"
        self.plan_path = self.out / "resume_validation_latest.json"
        self.runtime_path = self.out / "runtime_progress_latest.json"
        self.web_runtime_path = args.web_runtime_status.resolve() if args.web_runtime_status else None
        self.operations: list[dict[str, Any]] = []
        self.stage_runs: list[dict[str, Any]] = []
        self.operation_no = args.operation_start
        self.status = "STARTED"
        self.failure: str | None = None
        self.plan: dict[str, Any] = {}

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "slot_id": "height_difference_3",
            "updated_at": utc_now(),
            "status": self.status,
            "failure": self.failure,
            "first_invalid_stage": self.plan.get("first_invalid_stage"),
            "all_stages_valid": self.plan.get("all_stages_valid", False),
            "operation_count": len(self.operations),
            "operations": self.operations,
            "stage_runs": self.stage_runs,
            "resume_plan": self.plan,
            "single_shared_runner_only": True,
            "single_process_bounded_concurrency": True,
            "maximum_parallel_network_stages": 2,
            "new_runner_created": False,
            "parallel_runner_used": False,
            "queue_submission": False,
            "final_ready": False,
            "product_final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }

    def persist(self) -> None:
        payload = self.snapshot()
        write_json(self.execution_path, payload)
        write_json(self.runtime_path, payload)
        if self.web_runtime_path:
            write_json(self.web_runtime_path, payload)

    def add_operation(self, stage: str, status: str, summary: str, **extra: Any) -> None:
        row = {
            "operation_no": self.operation_no,
            "recorded_at": utc_now(),
            "stage": stage,
            "status": status,
            "details_summary": summary,
            **extra,
        }
        self.operation_no += 1
        self.operations.append(row)
        self.persist()

    def refresh_plan(self) -> dict[str, Any]:
        self.plan = self.validator.build_plan(self.out, self.source)
        write_json(self.plan_path, self.plan)
        self.persist()
        return self.plan

    def reuse_or_run(self, stage: str, command: list[str]) -> None:
        self.refresh_plan()
        if is_valid(self.plan, stage):
            evidence = plan_map(self.plan)[stage].get("evidence")
            self.add_operation(stage, "reused", "Previously completed stage passed full artefact validation.", evidence=evidence)
            return
        self.add_operation(stage, "running", "Stage is invalid or absent and will be executed.", command=command)
        result = run_command(stage, command, self.script_dir)
        self.stage_runs.append(result)
        if result["exit_code"] != 0:
            self.add_operation(stage, "blocked", "Stage execution failed; downstream stages were not run.", exit_code=result["exit_code"], stderr_tail=result["stderr_tail"])
            raise RuntimeError(f"{stage} failed with exit code {result['exit_code']}")
        self.refresh_plan()
        if not is_valid(self.plan, stage):
            reason = plan_map(self.plan).get(stage, {}).get("reason")
            self.add_operation(stage, "blocked", "Stage exited zero but its output failed validation.", validation_reason=reason)
            raise RuntimeError(f"{stage} output validation failed: {reason}")
        self.add_operation(stage, "completed", "Stage completed and passed post-execution artefact validation.", evidence=plan_map(self.plan)[stage].get("evidence"))

    def parallel_reuse_or_run(self, specs: list[tuple[str, list[str]]], group: str) -> None:
        self.refresh_plan()
        pending: list[tuple[str, list[str]]] = []
        for stage, command in specs:
            if is_valid(self.plan, stage):
                self.add_operation(stage, "reused", "Previously completed stage passed full artefact validation.", evidence=plan_map(self.plan)[stage].get("evidence"))
            else:
                pending.append((stage, command))
        if not pending:
            return
        for stage, command in pending:
            self.add_operation(stage, "running", f"{group}: stage scheduled inside bounded two-worker group.", command=command)
        with ThreadPoolExecutor(max_workers=min(2, len(pending)), thread_name_prefix="height_difference_3_resume") as pool:
            futures = [(stage, pool.submit(run_command, stage, command, self.script_dir)) for stage, command in pending]
            results = [(stage, future.result()) for stage, future in futures]
        failed = []
        for stage, result in results:
            self.stage_runs.append(result)
            if result["exit_code"] != 0:
                failed.append(stage)
                self.add_operation(stage, "blocked", f"{group}: execution failed.", exit_code=result["exit_code"], stderr_tail=result["stderr_tail"])
        if failed:
            raise RuntimeError(f"{group} failed: {failed}")
        self.refresh_plan()
        invalid = []
        for stage, _ in pending:
            if not is_valid(self.plan, stage):
                invalid.append(stage)
                self.add_operation(stage, "blocked", f"{group}: output failed post-execution validation.", validation_reason=plan_map(self.plan).get(stage, {}).get("reason"))
            else:
                self.add_operation(stage, "completed", f"{group}: stage completed and passed post-execution validation.", evidence=plan_map(self.plan)[stage].get("evidence"))
        if invalid:
            raise RuntimeError(f"{group} validation failed: {invalid}")

    def execute(self) -> int:
        self.out.mkdir(parents=True, exist_ok=True)
        scripts = {
            "extract": self.script_dir / "020_stream_extract_security_canonical.py",
            "query": self.script_dir / "004_prepare_three_real_sample_queries.py",
            "hmlr_download": self.script_dir / "012_download_hmlr_inspire_sources.py",
            "terrain_area": self.script_dir / "023_download_os_terrain50_required_areas.py",
            "hmlr_match": self.script_dir / "008_match_hmlr_inspire_gml.py",
            "ea_wcs": self.script_dir / "013_fetch_ea_dtm_wcs_for_matches.py",
            "terrain_tile": self.script_dir / "014_prepare_os_terrain50_tiles.py",
            "sample": self.script_dir / "009_sample_ea_dtm_and_os_terrain50.py",
            "publish": self.script_dir / "010_publish_verified_height_difference_examples.py",
        }
        for path in [self.args.validator_script.resolve(), *scripts.values()]:
            if not path.is_file():
                raise FileNotFoundError(path)
        if not self.source.is_file():
            raise FileNotFoundError(self.source)

        canonical = self.out / "canonical"
        sources = self.out / "sources"
        terrain_areas = sources / "os_terrain50_areas"
        matches = self.out / "hmlr_matches.json"
        measurements = self.out / "official_measurements.json"
        verified_json = self.out / "verified_examples.json"
        verified_geojson = self.out / "verified_examples.geojson"

        self.status = "VALIDATING_RESUME_STATE"
        self.refresh_plan()
        self.add_operation("RESUME_PLAN", "completed", "Existing artefacts were checked before execution.", first_invalid_stage=self.plan.get("first_invalid_stage"))

        extract_cmd = [sys.executable, str(scripts["extract"]), "--source-geojson", str(self.source), "--output-dir", str(canonical), "--query-preparer", str(scripts["query"])]
        if self.args.no_network_query_preparer:
            extract_cmd.append("--no-network")
        self.reuse_or_run("CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE", extract_cmd)

        starter = canonical / "starter_three_query_manifest.json"
        self.parallel_reuse_or_run(
            [
                ("HMLR_SOURCE_PREPARATION", [sys.executable, str(scripts["hmlr_download"]), "--starter-manifest", str(starter), "--output-dir", str(sources), "--timeout", str(self.args.timeout)]),
                ("TERRAIN50_REQUIRED_AREA_ACQUISITION", [sys.executable, str(scripts["terrain_area"]), "--starter-manifest", str(starter), "--output-dir", str(terrain_areas), "--timeout", str(self.args.timeout)]),
            ],
            "PARALLEL_HMLR_AND_TERRAIN50_ACQUISITION",
        )

        self.reuse_or_run(
            "HMLR_BOUNDARY_MATCH",
            [sys.executable, str(scripts["hmlr_match"]), "--starter-manifest", str(starter), "--vector-root", str(sources / "hmlr"), "--output", str(matches)],
        )

        archives = read_archives(terrain_areas / "terrain50_required_areas_manifest.json")
        terrain_cmd = [sys.executable, str(scripts["terrain_tile"]), "--matched-manifest", str(matches), "--output-dir", str(sources)]
        for archive in archives:
            terrain_cmd.extend(["--source", str(archive)])
        self.parallel_reuse_or_run(
            [
                ("EA_DTM_WCS_PREPARATION", [sys.executable, str(scripts["ea_wcs"]), "--matched-manifest", str(matches), "--output-dir", str(sources), "--timeout", str(self.args.timeout)]),
                ("TERRAIN50_EXACT_TILE_PREPARATION", terrain_cmd),
            ],
            "PARALLEL_EA_AND_TERRAIN50_TILE_PREPARATION",
        )

        self.reuse_or_run(
            "EA_DTM_AND_TERRAIN50_SAMPLE",
            [sys.executable, str(scripts["sample"]), "--matched-manifest", str(matches), "--ea-root", str(sources / "ea_dtm"), "--terrain50-root", str(sources / "terrain50"), "--output", str(measurements)],
        )
        self.reuse_or_run(
            "VERIFIED_WEBSITE_PUBLICATION",
            [sys.executable, str(scripts["publish"]), "--measurement-manifest", str(measurements), "--output-json", str(verified_json), "--output-geojson", str(verified_geojson)],
        )

        self.refresh_plan()
        if not self.plan.get("all_stages_valid"):
            raise RuntimeError(f"pipeline ended with invalid stage: {self.plan.get('first_invalid_stage')}")
        self.status = "THREE_REAL_SHARD_ROWS_OFFICIAL_CROSSCHECKED_AND_PUBLISHED"
        self.add_operation("PIPELINE", "completed", "All stages passed final validation; three official examples are available.")
        self.persist()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--script-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--validator-script", type=Path)
    parser.add_argument("--web-runtime-status", type=Path)
    parser.add_argument("--operation-start", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--no-network-query-preparer", action="store_true")
    args = parser.parse_args()
    if args.operation_start < 1:
        raise ValueError("operation-start must be positive")
    if args.validator_script is None:
        args.validator_script = args.script_dir / "025_validate_resumable_targeted_sources.py"
    validator = load_validator(args.validator_script.resolve())
    execution = Execution(args, validator)
    try:
        return execution.execute()
    except Exception as exc:
        execution.status = "BLOCKED_RESUMABLE_TARGETED_SOURCE_PIPELINE"
        execution.failure = f"{type(exc).__name__}: {exc}"
        execution.operations.append({
            "operation_no": execution.operation_no,
            "recorded_at": utc_now(),
            "stage": "PIPELINE",
            "status": "blocked",
            "details_summary": "Pipeline stopped at the first failed or invalid stage.",
            "error": execution.failure,
            "traceback_tail": traceback.format_exc()[-12000:],
        })
        execution.persist()
        print(json.dumps({"ok": False, "status": execution.status, "error": execution.failure, "execution": str(execution.execution_path)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
