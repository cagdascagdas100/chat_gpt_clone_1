#!/usr/bin/env python3
"""Contract tests for exact-manifest Ofcom/ONSPD/HMLR binding."""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import os
import tempfile
from pathlib import Path

SLOT_ID = "internet_access_3"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/020_exact_manifest_binding_tests_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "docs").exists() and (item / "england_map_web").exists():
            return item
    raise FileNotFoundError("repository root not found")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


class LegacyStub:
    @staticmethod
    def parse_ring(text: str):
        values = [float(value) for value in text.split()]
        ring = list(zip(values[0::2], values[1::2]))
        if ring and ring[0] != ring[-1]:
            ring.append(ring[0])
        return ring


def main() -> int:
    args = parse_args()
    repo = root(args.repo_root)
    automation = Path(__file__).resolve().parent
    adapter_path = automation / "024_stratified_ofcom_onspd_adapter.py"
    hmlr_path = automation / "025_hmlr_exact_stratified_manifest_audit.py"
    adapter_source = adapter_path.read_text(encoding="utf-8")
    hmlr_source = hmlr_path.read_text(encoding="utf-8")
    hmlr = load_module(hmlr_path, "exact_hmlr")
    tests: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        tests.append({"name": name, "passed": bool(condition), "detail": detail})

    check("ADAPTER_SUPPORTS_OFcom_AND_ONSPD", 'choices=["ofcom", "onspd"]' in adapter_source, "both modes required")
    check("ADAPTER_REQUIRES_EXACT_MANIFEST_COUNT", "stratified manifest count mismatch" in adapter_source, "count gate")
    check("ADAPTER_REJECTS_DUPLICATE_ROWS", "duplicate row identities" in adapter_source, "duplicate gate")
    check("ADAPTER_REJECTS_MISSING_ROWS", "manifest rows missing from full migrated rows" in adapter_source, "missing-row gate")
    check("ADAPTER_PATCHES_DETERMINISTIC_SAMPLE", "module.deterministic_sample = exact_manifest_sample" in adapter_source, "exact identity patch")
    check("HMLR_REQUIRES_EXACT_MANIFEST", "exact_manifest_row_identity_required" in hmlr_source and "manifest_ids" in hmlr_source, "exact manifest gate")
    check("HMLR_STREAMING_PARSE", "ET.iterparse" in hmlr_source and '"streaming_iterparse": True' in hmlr_source, "streaming parser")
    check("HMLR_LARGEST_RING_POLICY", "max(rings, key=ring_area)" in hmlr_source and '"largest_exterior_ring_policy": True' in hmlr_source, "largest ring")
    small = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
    large = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]
    check("RING_AREA_ORDER", hmlr.ring_area(large) > hmlr.ring_area(small), str((hmlr.ring_area(small), hmlr.ring_area(large))))
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.gml"
        path.write_text('<root xmlns:gml="http://www.opengis.net/gml"><CadastralParcel><id>ABC123</id><gml:posList>0 0 2 0 2 2 0 2 0 0</gml:posList><gml:posList>0 0 4 0 4 4 0 4 0 0</gml:posList></CadastralParcel></root>', encoding="utf-8")
        found, audit = hmlr.find_largest_rings(LegacyStub(), [path], {"ABC123"})
        check("MULTI_RING_LARGEST_SELECTED", round(hmlr.ring_area(found["ABC123"]), 2) == 16.0, repr(found))
        check("MULTI_RING_AUDITED", audit["multiple_ring_elements"] == 1, repr(audit))
    check("NO_PROMOTION_AND_SAFETY", all(token in hmlr_source for token in ['"parcel_relations_promoted": 0', '"confidence_uplifts": 0', '"fake_data": False', '"db_write": False', '"migration": False', '"production_deploy": False']), "no promotion and safety flags")
    failures = [item for item in tests if not item["passed"]]
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "passed" if not failures else "failed",
        "tests_expected": 12,
        "tests_executed": len(tests),
        "tests_passed": len(tests) - len(failures),
        "tests_failed": len(failures),
        "tests": tests,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(repo / args.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
