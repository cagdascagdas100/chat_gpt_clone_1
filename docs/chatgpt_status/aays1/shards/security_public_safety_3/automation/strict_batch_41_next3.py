from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

SLOT_ID = "security_public_safety_3"
TASK_VERSION = "5.2.12-next-unprocessed-batch41"
ATTEMPT_ID = "security-public-safety-3-20260731-021"
SUPERSEDES_ATTEMPT_ID = "security-public-safety-3-20260721-020"
TARGET_IDS = ["parcel_61526", "parcel_61527", "parcel_61528"]
SAMPLE_RANGE = {"start": 61526, "end": 61528, "count": 3}

BASE_REL = Path(
    "docs/chatgpt_status/security_public_safety/automation/"
    "security_public_safety_3_smoke_v5_2_11.py"
)
OUTPUT_REL = Path(
    "docs/chatgpt_status/aays1/shards/security_public_safety_3/runner_outputs/"
    "security_public_safety_3_batch41_candidates_latest.json"
)
RECON_REL = Path(
    "docs/chatgpt_status/aays1/shards/security_public_safety_3/runner_outputs/"
    "security_public_safety_3_batch41_reconciliation_latest.json"
)
WEBSITE_REL = Path(
    "england_map_web/data/aays_21_slots/security_public_safety_3/"
    "strict_rows_61526_61528_latest.json"
)
MANIFEST_REL = Path(
    "england_map_web/data/aays_21_slots/security_public_safety_3/"
    "strict_rows_61526_61528_manifest_latest.json"
)
CORE_WEB_ROOT_REL = Path(
    "docs/chatgpt_status/aays1/shards/security_public_safety_3/runner_outputs/core_web"
)

OLD_OUTPUT = (
    "docs/chatgpt_status/security_public_safety/runner_outputs/"
    "security_public_safety_3_smoke_candidates_v5_2_latest.json"
)
OLD_RECON = (
    "docs/chatgpt_status/security_public_safety/runner_outputs/"
    "security_public_safety_3_smoke_reconciliation_v5_2_latest.json"
)
OLD_WEBSITE = (
    "england_map_web/data/security_public_safety/"
    "security_public_safety_3_smoke_rows_latest.json"
)
OLD_MANIFEST = (
    "england_map_web/data/security_public_safety/"
    "security_public_safety_3_publication_manifest_latest.json"
)
OLD_CORE_OUT_ROOT = "docs/chatgpt_status/security_public_safety/runner_outputs"
OLD_CORE_WEB_ROOT = (
    "outputs/england_program_parcel_matrix_20260629/"
    "security_public_safety_updates"
)

_ORIGINAL_TRUEDIV = Path.__truediv__


def repo_root() -> Path:
    return Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))


def _normalised(path: Path) -> str:
    return path.as_posix().replace("\\", "/").rstrip("/")


def _redirect_candidate(candidate: Path) -> Path:
    value = _normalised(candidate)
    mappings = (
        (OLD_OUTPUT, OUTPUT_REL),
        (OLD_RECON, RECON_REL),
        (OLD_WEBSITE, WEBSITE_REL),
        (OLD_MANIFEST, MANIFEST_REL),
        (OLD_CORE_WEB_ROOT, CORE_WEB_ROOT_REL),
        (OLD_CORE_OUT_ROOT, OUTPUT_REL.parent),
    )
    for old_suffix, replacement in mappings:
        if value.endswith(old_suffix):
            return _ORIGINAL_TRUEDIV(repo_root(), replacement.as_posix())
    return candidate


def _patched_truediv(self: Path, key: object) -> Path:
    return _redirect_candidate(_ORIGINAL_TRUEDIV(self, key))


def atomic_rewrite(path: Path, updater: Callable[[dict[str, Any]], None]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"TOP_LEVEL_NOT_OBJECT:{path}")
    updater(payload)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def rewrite_base_metadata() -> None:
    def update_primary(payload: dict[str, Any]) -> None:
        payload["task_version"] = TASK_VERSION
        payload["attempt_id"] = ATTEMPT_ID
        payload["supersedes_attempt_id"] = SUPERSEDES_ATTEMPT_ID
        payload["sample_kind"] = "three-row-next-unprocessed-batch"
        payload["sample_range"] = dict(SAMPLE_RANGE)
        payload["target_parcels"] = list(TARGET_IDS)
        payload["sample_count"] = 3
        payload["fake_data"] = False
        payload["final_ready"] = False

    def update_reconciliation(payload: dict[str, Any]) -> None:
        payload["task_version"] = TASK_VERSION
        payload["attempt_id"] = ATTEMPT_ID
        payload["supersedes_attempt_id"] = SUPERSEDES_ATTEMPT_ID
        payload["expected_rows"] = 3
        payload["expected_gate_cells"] = 12
        payload["fake_data"] = False
        payload["final_ready"] = False

    for relative in (OUTPUT_REL, WEBSITE_REL):
        path = repo_root() / relative
        if path.is_file():
            atomic_rewrite(path, update_primary)
    recon = repo_root() / RECON_REL
    if recon.is_file():
        atomic_rewrite(recon, update_reconciliation)


def patch_module(module: ModuleType) -> ModuleType:
    for name, value in (
        ("TASK_VERSION", TASK_VERSION),
        ("ATTEMPT_ID", ATTEMPT_ID),
        ("SUPERSEDES_ATTEMPT_ID", SUPERSEDES_ATTEMPT_ID),
    ):
        if hasattr(module, name):
            setattr(module, name, value)
    if hasattr(module, "TARGET_IDS"):
        module.TARGET_IDS = list(TARGET_IDS)
    if hasattr(module, "OUTPUT_REL"):
        module.OUTPUT_REL = OUTPUT_REL
    if hasattr(module, "RECON_REL"):
        module.RECON_REL = RECON_REL
    if hasattr(module, "WEBSITE_REL"):
        module.WEBSITE_REL = WEBSITE_REL
    if hasattr(module, "MANIFEST_REL"):
        module.MANIFEST_REL = MANIFEST_REL

    for loader_name in ("load_base", "load_core"):
        original = getattr(module, loader_name, None)
        if not callable(original) or getattr(original, "_aays_batch41_patched", False):
            continue

        def wrapped_loader(
            _original: Callable[[], ModuleType] = original,
        ) -> ModuleType:
            child = _original()
            return patch_module(child)

        setattr(wrapped_loader, "_aays_batch41_patched", True)
        setattr(module, loader_name, wrapped_loader)

    if (
        hasattr(module, "LOCATE_NEIGHBOURHOOD_URL")
        and hasattr(module, "EXPECTED_IOD25_FILE7_V2_URL")
        and callable(getattr(module, "main", None))
        and not getattr(module.main, "_aays_batch41_metadata_wrapper", False)
    ):
        original_main = module.main

        def wrapped_main() -> int:
            result = int(original_main())
            rewrite_base_metadata()
            return result

        setattr(wrapped_main, "_aays_batch41_metadata_wrapper", True)
        module.main = wrapped_main

    return module


def load_entry() -> ModuleType:
    entry_path = repo_root() / BASE_REL
    spec = importlib.util.spec_from_file_location(
        "security_public_safety_3_batch41_entry", entry_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"ENTRY_IMPORT_FAILED:{entry_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return patch_module(module)


def main() -> int:
    Path.__truediv__ = _patched_truediv
    try:
        entry = load_entry()
        result = int(entry.main())
        print(f"SLOT_ID={SLOT_ID}")
        print(f"ATTEMPT_ID={ATTEMPT_ID}")
        print(f"TARGET_IDS={','.join(TARGET_IDS)}")
        print(f"OUTPUT={repo_root() / OUTPUT_REL}")
        print(f"WEBSITE={repo_root() / WEBSITE_REL}")
        print("FINAL_READY=false")
        return result
    finally:
        Path.__truediv__ = _ORIGINAL_TRUEDIV


if __name__ == "__main__":
    raise SystemExit(main())
