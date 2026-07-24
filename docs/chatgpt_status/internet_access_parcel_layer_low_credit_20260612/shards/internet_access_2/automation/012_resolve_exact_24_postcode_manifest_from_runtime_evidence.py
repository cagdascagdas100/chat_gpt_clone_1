# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
EXPECTED_SAMPLES = 24
MAX_FILES = 2000
MAX_FILE_BYTES = 5_000_000
POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b", re.I)
ALLOWED_SUFFIXES = {".json", ".csv", ".txt", ".log", ".md"}


def normalise_postcode(value: str) -> str:
    compact = re.sub(r"\s+", "", value.upper())
    if len(compact) < 5:
        raise ValueError("INVALID_POSTCODE")
    return compact[:-3] + " " + compact[-3:]


def postcode_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def extract_from_text(text: str) -> list[str]:
    out: list[str] = []
    for match in POSTCODE_RE.finditer(text):
        postcode = normalise_postcode(match.group(1))
        if postcode not in out:
            out.append(postcode)
    return out


def extract_file(path: Path) -> list[str]:
    if path.stat().st_size > MAX_FILE_BYTES or path.suffix.lower() not in ALLOWED_SUFFIXES:
        return []
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return []
        found: list[str] = []
        for text in strings(payload):
            for postcode in extract_from_text(text):
                if postcode not in found:
                    found.append(postcode)
        return found
    try:
        return extract_from_text(path.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return []


def under_repo_output(path: Path) -> bool:
    lowered = {part.casefold() for part in path.resolve().parts}
    return "docs" in lowered or "england_map_web" in lowered or ".git" in lowered


def scan(roots: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exact: list[dict[str, Any]] = []
    inspected: list[dict[str, Any]] = []
    seen_files = 0
    for root in roots:
        root = root.expanduser().resolve()
        if not root.exists():
            inspected.append({"root_hash": postcode_hash(str(root)), "state": "ROOT_MISSING"})
            continue
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if seen_files >= MAX_FILES:
                raise RuntimeError(f"FILE_SCAN_LIMIT_EXCEEDED:{MAX_FILES}")
            if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
                continue
            seen_files += 1
            try:
                values = extract_file(path)
                source = {
                    "path_hash": postcode_hash(str(path.resolve())),
                    "file_sha256": file_sha256(path),
                    "unique_postcodes": len(values),
                }
            except Exception as exc:
                inspected.append({"path_hash": postcode_hash(str(path)), "state": f"READ_FAILED:{type(exc).__name__}"})
                continue
            inspected.append(source)
            if len(values) == EXPECTED_SAMPLES:
                exact.append({**source, "postcodes": values})
    return exact, inspected


def choose(exact: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in exact:
        canonical = "\n".join(sorted(item["postcodes"]))
        key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        groups.setdefault(key, []).append(item)
    if not groups:
        raise RuntimeError("NO_EXACT_24_POSTCODE_MANIFEST_FOUND")
    if len(groups) != 1:
        raise RuntimeError(f"CONFLICTING_EXACT_24_POSTCODE_SETS:{len(groups)}")
    set_sha, sources = next(iter(groups.items()))
    postcodes = sources[0]["postcodes"]
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "sample_count": len(postcodes),
        "postcodes": postcodes,
        "postcode_set_sha256": set_sha,
        "source_file_count": len(sources),
        "source_path_hashes": [item["path_hash"] for item in sources],
        "source_file_sha256": [item["file_sha256"] for item in sources],
        "raw_source_paths_persisted": False,
        "final_ready": False,
    }


def write_private(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    if under_repo_output(path):
        raise RuntimeError("RAW_POSTCODE_MANIFEST_MUST_NOT_BE_WRITTEN_TO_REPO")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one exact 24-postcode manifest from runtime evidence")
    parser.add_argument("--search-root", action="append", default=[])
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-output")
    args = parser.parse_args()

    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")

    roots = [Path(item) for item in args.search_root]
    env_roots = os.environ.get("AAYS_OFCom_SAMPLE_SEARCH_ROOTS", "")
    roots.extend(Path(item) for item in env_roots.split(os.pathsep) if item.strip())
    if not roots:
        raise RuntimeError("SAMPLE_SEARCH_ROOT_REQUIRED")

    exact, inspected = scan(roots)
    manifest = choose(exact)
    write_private(Path(args.output), manifest)

    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "EXACT_24_POSTCODE_RUNTIME_MANIFEST_RESOLVED",
        "sample_count": manifest["sample_count"],
        "postcode_set_sha256": manifest["postcode_set_sha256"],
        "sample_hashes": [postcode_hash(item) for item in manifest["postcodes"]],
        "candidate_files_with_exact_24": len(exact),
        "inspected_files": len(inspected),
        "raw_postcodes_persisted_in_summary": False,
        "manifest_output_is_outside_repo": True,
        "next_environment": {"AAYS_OFCom_POSTCODES_PATH": str(Path(args.output).expanduser().resolve())},
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    if args.summary_output:
        Path(args.summary_output).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
