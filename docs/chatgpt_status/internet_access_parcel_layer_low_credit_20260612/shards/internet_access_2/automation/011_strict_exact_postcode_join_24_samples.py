# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
MAX_SAMPLES = 24
EXPECTED_FILES = 121
EXPECTED_ROWS = 1_741_096
R2 = re.compile(r"(?:^|/)202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$", re.I)
POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b", re.I)
SAMPLES_ENV = "AAYS_OFCom_POSTCODES_PATH"
ALIASES = {
    "postcode": ["postcode", "postcode_space"],
    "postcode_area": ["postcode area", "postcode_area"],
    "sfbb": ["SFBB availability (% premises)", "SFBB availability"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)", "UFBB100 availability (% premises)"],
    "ufbb300": ["UFBB availability (% premises)", "UFBB (300Mbit/s) availability (% premises)"],
    "gigabit": ["Gigabit availability (% premises)", "Gigabit availability"],
    "unable30": ["% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalise_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def match_column(fieldnames: list[str], aliases: list[str]) -> str | None:
    lookup = {normalise_header(name): name for name in fieldnames}
    return next((lookup[normalise_header(alias)] for alias in aliases if normalise_header(alias) in lookup), None)


def normalise_postcode(value: str) -> str:
    compact = re.sub(r"\s+", "", str(value).upper())
    if len(compact) < 5:
        raise ValueError(f"INVALID_POSTCODE:{value}")
    return compact[:-3] + " " + compact[-3:]


def postcode_area(postcode: str) -> str:
    match = re.match(r"^([A-Z]{1,2})", postcode)
    if not match:
        raise ValueError(f"POSTCODE_AREA_NOT_FOUND:{postcode}")
    return match.group(1)


def postcode_hash(postcode: str) -> str:
    return hashlib.sha256(postcode.encode("utf-8")).hexdigest()[:16]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).casefold()
            if any(token in lowered for token in ("postcode", "sample", "candidate")):
                yield from iter_strings(item)


def load_samples(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    found: list[str] = []
    for text in iter_strings(payload):
        for match in POSTCODE_RE.finditer(text):
            postcode = normalise_postcode(match.group(1))
            if postcode not in found:
                found.append(postcode)
    if not found:
        raise RuntimeError("NO_POSTCODES_FOUND_IN_SAMPLE_MANIFEST")
    if len(found) != MAX_SAMPLES:
        raise RuntimeError(f"SAMPLE_COUNT_NOT_EXACTLY_24:{len(found)}")
    return found


def accepted_state(value: Any) -> bool:
    return str(value) in {
        "OFCom_V2_R2_POSTCODE_ARCHIVE_ACCEPTED",
        "OFCom_POSTCODE_ZIP_SCHEMA_ACCEPTED",
    }


def validation_gate(validation: dict[str, Any], archive: Path) -> dict[str, Any]:
    download = validation.get("download") if isinstance(validation.get("download"), dict) else {}
    expected_sha = str(
        download.get("sha256")
        or validation.get("archive_sha256")
        or validation.get("sha256")
        or ""
    ).lower()
    revision = str(
        validation.get("required_inner_postcode_revision")
        or validation.get("observed_postcode_revision")
        or ""
    ).lower()
    observed_files = int(
        validation.get(
            "observed_r2_postcode_file_count",
            validation.get("r2_postcode_file_count", validation.get("postcode_file_count", 0)),
        )
    )
    observed_rows = int(
        validation.get(
            "total_r2_postcode_rows",
            validation.get("total_postcode_rows", 0),
        )
    )
    checks = {
        "state": accepted_state(validation.get("state")),
        "accepted": validation.get("accepted") is True,
        "revision": revision == "r2",
        "files": observed_files == EXPECTED_FILES,
        "rows": observed_rows == EXPECTED_ROWS,
        "crc": validation.get("zip_crc_ok") is True,
        "unique_areas": validation.get("unique_postcode_areas_ok") is True,
        "no_stale_r1": validation.get("stale_r1_postcode_files_absent") is True,
        "core_columns": validation.get("all_r2_files_nonempty_and_core_columns_present") is True,
        "sha": bool(expected_sha and sha256_file(archive) == expected_sha),
    }
    checks["all"] = all(checks.values())
    return checks


def number(value: Any) -> float | None:
    try:
        return float(str(value or "").strip().replace("%", ""))
    except Exception:
        return None


def join_archive(archive_path: Path, postcodes: list[str]) -> list[dict[str, Any]]:
    wanted = {postcode: index for index, postcode in enumerate(postcodes, start=1)}
    by_area: dict[str, list[str]] = {}
    for postcode in postcodes:
        by_area.setdefault(postcode_area(postcode), []).append(postcode)

    output: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive_path) as archive:
        bad_crc = archive.testzip()
        if bad_crc:
            raise RuntimeError(f"ZIP_CRC_FAILURE:{bad_crc}")

        members: dict[str, str] = {}
        for raw_name in archive.namelist():
            name = raw_name.replace("\\", "/")
            match = R2.search(name)
            if not match:
                continue
            area = match.group(1).upper()
            if area in members:
                raise RuntimeError(f"DUPLICATE_AREA_FILE:{area}")
            members[area] = raw_name

        for area, group in sorted(by_area.items()):
            member = members.get(area)
            if not member:
                output.extend(
                    {
                        "sample_index": wanted[postcode],
                        "postcode_hash": postcode_hash(postcode),
                        "postcode_area": area,
                        "state": "NO_DATA_AREA_FILE_MISSING",
                    }
                    for postcode in group
                )
                continue

            found: dict[str, list[dict[str, Any]]] = {postcode: [] for postcode in group}
            with archive.open(member) as raw:
                reader = csv.DictReader(
                    io.TextIOWrapper(raw, encoding="utf-8-sig", errors="strict", newline="")
                )
                fields = list(reader.fieldnames or [])
                columns = {key: match_column(fields, aliases) for key, aliases in ALIASES.items()}
                missing = [key for key, value in columns.items() if value is None]
                if missing:
                    raise RuntimeError("CORE_COLUMNS_MISSING:" + ",".join(missing))

                for source_row, row in enumerate(reader, start=2):
                    postcode = normalise_postcode(row.get(columns["postcode"], ""))
                    if postcode in found:
                        found[postcode].append(
                            {
                                "source_file": member,
                                "source_row": source_row,
                                "sfbb": number(row.get(columns["sfbb"])),
                                "ufbb100": number(row.get(columns["ufbb100"])),
                                "ufbb300": number(row.get(columns["ufbb300"])),
                                "gigabit": number(row.get(columns["gigabit"])),
                                "unable30": number(row.get(columns["unable30"])),
                            }
                        )

            for postcode in group:
                matches = found[postcode]
                base = {
                    "sample_index": wanted[postcode],
                    "postcode_hash": postcode_hash(postcode),
                    "postcode_area": area,
                    "source_file": member,
                }
                if len(matches) == 1:
                    output.append(
                        base
                        | {
                            "state": "PASS_EXACT_POSTCODE_MATCH",
                            "accuracy_tier": "3/4_POSTCODE_PROXY",
                        }
                        | matches[0]
                    )
                elif not matches:
                    output.append(base | {"state": "NO_DATA_EXACT_POSTCODE_NOT_FOUND"})
                else:
                    output.append(
                        base
                        | {
                            "state": "REJECT_AMBIGUOUS_DUPLICATE_POSTCODE",
                            "duplicate_matches": len(matches),
                        }
                    )
    return sorted(output, key=lambda row: row["sample_index"])


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--samples")
    args = parser.parse_args()

    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")

    archive = Path(args.archive).expanduser().resolve()
    validation = json.loads(Path(args.validation).read_text(encoding="utf-8-sig"))
    output_path = Path(args.output).expanduser().resolve()
    sample_value = args.samples or os.environ.get(SAMPLES_ENV, "")

    payload: dict[str, Any] = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "checked_at": now(),
        "candidate_accuracy_written": 0,
        "parcel_measured_values_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }

    if not sample_value:
        payload.update(
            {
                "state": "BLOCKED_SAMPLE_MANIFEST_REQUIRED",
                "required_argument_or_environment": ["--samples", SAMPLES_ENV],
                "operation_rows": [],
            }
        )
        write_output(output_path, payload)
        return 2

    try:
        postcodes = load_samples(Path(sample_value).expanduser().resolve())
        gate = validation_gate(validation, archive)
        payload["archive_gate"] = gate
        payload["sample_count"] = len(postcodes)
        payload["sample_hashes"] = [postcode_hash(postcode) for postcode in postcodes]

        if not gate["all"]:
            payload.update(
                {
                    "state": "BLOCKED_ARCHIVE_VALIDATION_GATE_NOT_ACCEPTED",
                    "operation_rows": [],
                }
            )
            write_output(output_path, payload)
            return 2

        rows = join_archive(archive, postcodes)
        exact = sum(row["state"] == "PASS_EXACT_POSTCODE_MATCH" for row in rows)
        rejected = sum(row["state"].startswith("REJECT") for row in rows)
        payload.update(
            {
                "state": (
                    "STRICT_24_SAMPLE_EXACT_POSTCODE_JOIN_COMPLETE"
                    if not rejected
                    else "STRICT_24_SAMPLE_JOIN_REVIEW_REQUIRED"
                ),
                "exact_postcode_matches": exact,
                "official_coverage_verified_candidates": exact,
                "candidate_accuracy_written": exact,
                "accuracy_tier": "3/4_POSTCODE_PROXY" if exact else None,
                "operation_rows": rows,
                "completed_at": now(),
            }
        )
        write_output(output_path, payload)
        return 0 if not rejected else 2
    except Exception as exc:
        payload.update(
            {
                "state": "STRICT_JOIN_FAILED",
                "blocker": f"{type(exc).__name__}:{exc}",
                "operation_rows": [],
                "updated_at": now(),
            }
        )
        write_output(output_path, payload)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
