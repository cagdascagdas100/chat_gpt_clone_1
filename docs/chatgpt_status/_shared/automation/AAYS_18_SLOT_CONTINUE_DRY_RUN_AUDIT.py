from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def load_coordinator(script: Path):
    spec = importlib.util.spec_from_file_location("aays_18_coordinator", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"COORDINATOR_IMPORT_FAILED: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_task(module, slot_id: str, spec: dict) -> dict:
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": module.WORKSTREAM_ID,
        "slot_id": slot_id,
        "base_slot_id": spec["base_slot_id"],
        "shard_index": spec["shard_index"],
        "task_id": f"dryrun_continue_{slot_id}",
        "attempt_id": f"dryrun-{slot_id}",
        "idempotency_key": f"dryrun-{slot_id}-remote-head",
        "script_path": f"{spec['business_root']}/automation/{slot_id}_continue.py",
        "read_paths": [
            spec["business_root"],
            f"docs/chatgpt_status/_shared/slots_18/{slot_id}",
        ],
        "exact_write_paths": [
            f"{spec['business_root']}/shards/{slot_id}/dryrun_result.json"
        ],
        "resource_class": "light_read",
        "parcel_partition": spec["parcel_partition"],
        "safety_flags": {
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        },
        "data_quality_contract": {
            "source_urls": [],
            "source_snapshot_date": "",
            "source_discovery_required": True,
            "measurement_level": "unknown_pending_source",
            "output_semantics": "NO_DATA",
            "parcel_binding_method": "NOT_RUN",
            "confidence_method": "NOT_SCORED",
            "no_data_policy": "NO_DATA_NOT_INFERRED",
            "ai_role": "not_used",
            "human_review_required_when": [
                "source_conflict",
                "low_confidence",
                "geometry_mismatch",
            ],
        },
        "timeout_seconds": 3600,
    }


def audit(root: Path, coordinator_script: Path) -> dict:
    module = load_coordinator(coordinator_script)
    coordinator = module.Coordinator(root)
    accepted: list[str] = []
    validation_errors: list[dict] = []
    wrong_slot_results: list[dict] = []
    samples: list[dict] = []
    slot_contracts: list[dict] = []

    for slot_id, slot_spec in module.SLOT_SPECS.items():
        task = build_task(module, slot_id, slot_spec)
        slot_contracts.append(
            {
                "slot_id": slot_id,
                "base_slot_id": slot_spec["base_slot_id"],
                "shard_index": slot_spec["shard_index"],
                "parcel_partition": slot_spec["parcel_partition"],
            }
        )
        try:
            accepted.append(coordinator.classify_task(task))
        except Exception as exc:
            validation_errors.append({"slot_id": slot_id, "error": str(exc)})

        wrong = dict(task)
        wrong["task_id"] = f"dryrun_wrong_{slot_id}"
        wrong["exact_write_paths"] = [
            f"{slot_spec['business_root']}/shards/not_{slot_id}/bad.json"
        ]
        try:
            coordinator.classify_task(wrong)
            wrong_slot_results.append({"slot_id": slot_id, "blocked": False})
        except Exception as exc:
            wrong_slot_results.append(
                {"slot_id": slot_id, "blocked": True, "reason": str(exc)}
            )

        if slot_id in (
            "ready_to_sell_1",
            "security_public_safety_2",
            "internet_access_3",
        ):
            samples.append(task)

    legacy = dict(samples[0])
    legacy["task_id"] = "dryrun_legacy_ready"
    legacy["workstream_id"] = "AAYS_15_SLOT_SAFE_PARALLEL_V1"
    legacy_non_internet_accepted = (
        coordinator.classify_task(legacy) == "ready_to_sell_1"
    )

    legacy_internet = dict(samples[-1])
    legacy_internet["task_id"] = "dryrun_legacy_internet"
    legacy_internet["workstream_id"] = "AAYS_15_SLOT_SAFE_PARALLEL_V1"
    try:
        coordinator.classify_task(legacy_internet)
        legacy_internet_blocked = False
    except Exception as exc:
        legacy_internet_blocked = (
            "INTERNET_SLOT_REQUIRES_18_SLOT_WORKSTREAM" in str(exc)
        )

    web_task = build_task(
        module,
        "internet_access_1",
        module.SLOT_SPECS["internet_access_1"],
    )
    web_task["task_id"] = "dryrun_web_incomplete_source"
    web_task["exact_write_paths"] = [
        "england_map_web/data/aays_18_slots/internet_access_1/output.json"
    ]
    try:
        coordinator.classify_task(web_task)
        incomplete_source_web_publish_blocked = False
    except Exception as exc:
        incomplete_source_web_publish_blocked = (
            "WEB_PUBLISH_REQUIRES_COMPLETED_SOURCE_DISCOVERY" in str(exc)
        )

    nonparcel_measured = dict(web_task)
    nonparcel_measured["task_id"] = "dryrun_web_nonparcel_measured"
    nonparcel_measured["data_quality_contract"] = dict(
        web_task["data_quality_contract"]
    )
    nonparcel_measured["data_quality_contract"].update(
        {
            "source_urls": ["https://example.invalid/official-source-placeholder"],
            "source_snapshot_date": "2026-07-18",
            "source_discovery_required": False,
            "measurement_level": "postcode",
            "output_semantics": "MEASURED",
            "parcel_binding_method": "postcode_join",
            "confidence_method": "source_coverage_only",
        }
    )
    try:
        coordinator.classify_task(nonparcel_measured)
        nonparcel_measured_web_publish_blocked = False
    except Exception as exc:
        nonparcel_measured_web_publish_blocked = (
            "NON_PARCEL_DATA_CANNOT_BE_PUBLISHED_AS_PARCEL_MEASUREMENT" in str(exc)
        )

    report = {
        "status": "PASS"
        if (
            len(accepted) == 18
            and not validation_errors
            and all(item["blocked"] for item in wrong_slot_results)
            and legacy_non_internet_accepted
            and legacy_internet_blocked
            and incomplete_source_web_publish_blocked
            and nonparcel_measured_web_publish_blocked
        )
        else "BLOCKED",
        "workstream_id": module.WORKSTREAM_ID,
        "valid_continue_contracts": len(accepted),
        "accepted_slots": accepted,
        "slot_contracts": slot_contracts,
        "validation_errors": validation_errors,
        "wrong_slot_blocked_count": sum(
            bool(item["blocked"]) for item in wrong_slot_results
        ),
        "wrong_slot_results": wrong_slot_results,
        "legacy_non_internet_accepted": legacy_non_internet_accepted,
        "legacy_internet_blocked": legacy_internet_blocked,
        "incomplete_source_web_publish_blocked": incomplete_source_web_publish_blocked,
        "nonparcel_measured_web_publish_blocked": nonparcel_measured_web_publish_blocked,
        "sample_task_shapes": samples,
        "business_files_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--coordinator", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    coordinator_script = args.coordinator or (
        args.root / "AAYS_ADAPTIVE_15_WORKER_COORDINATOR.py"
    )
    report = audit(args.root.resolve(), coordinator_script.resolve())
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
