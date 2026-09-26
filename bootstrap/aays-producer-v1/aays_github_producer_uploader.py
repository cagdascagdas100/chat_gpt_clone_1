"""Validate AAYS producer packages and upload them to GitHub atomically.

The producer browser should save generated packages into a dedicated outbox,
never the user's Downloads directory.  This agent validates the package,
creates the external SHA-256 sidecar, and publishes both files in one GitHub
commit.  Credentials are read from AAYS_GITHUB_TOKEN and are never persisted.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_MEMBERS = (
    "records.geojson",
    "evidence_manifest.json",
    "source_ledger.jsonl",
    "unmatched.jsonl",
    "checkpoint.json",
    "receipt.json",
)
SAFE_PART = re.compile(r"[^A-Za-z0-9._-]+")
CATEGORY_SLOTS = {
    "future_growth_new": {f"future_growth_{index}" for index in range(1, 10)},
    "building_type_new": {f"building_type_{index}" for index in range(1, 10)},
    "planned_building_new": {f"planned_buildings_{index}" for index in range(1, 6)},
}
LAYER24_VALID_SLOTS = {
    f"{family}_{index}"
    for family in (
        "gas_emissions", "height_difference",
        "security_public_safety", "internet_access",
    )
    for index in range(1, 7)
}


class PackageValidationError(ValueError):
    pass


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def resolve_github_token() -> str:
    token = os.environ.get("AAYS_GITHUB_TOKEN", "").strip()
    if token:
        return token
    gh = shutil.which("gh")
    if not gh:
        return ""
    try:
        completed = subprocess.run(
            [gh, "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


@dataclass(frozen=True)
class ValidatedPackage:
    path: Path
    sha256: str
    family: str
    slot_id: str
    lineage_id: str
    accepted_count: int
    receipt: dict[str, Any]


def _safe_part(value: object, fallback: str) -> str:
    cleaned = SAFE_PART.sub("_", str(value or "").strip()).strip("._-")
    return cleaned[:96] or fallback


def _member_by_basename(names: list[str], basename: str) -> str:
    matches = [name for name in names if Path(name).name == basename]
    if len(matches) != 1:
        raise PackageValidationError(
            f"required member {basename!r} must appear exactly once; found {len(matches)}"
        )
    return matches[0]


def _sidecar_digest(payload: bytes) -> str:
    text = payload.decode("utf-8", "strict").strip()
    digest = text.split()[0].lower() if text else ""
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise PackageValidationError("invalid SHA-256 sidecar")
    return digest


def validate_package(path: Path) -> ValidatedPackage:
    path = Path(path)
    if not path.is_file() or path.suffix.casefold() != ".zip":
        raise PackageValidationError("producer input must be an existing ZIP file")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            members = {name: _member_by_basename(names, name) for name in REQUIRED_MEMBERS}
            for basename, member in members.items():
                sidecar = _member_by_basename(names, f"{basename}.sha256")
                actual = hashlib.sha256(archive.read(member)).hexdigest()
                declared = _sidecar_digest(archive.read(sidecar))
                if actual != declared:
                    raise PackageValidationError(f"SHA-256 mismatch for {basename}")
            receipt = json.loads(archive.read(members["receipt.json"]))
    except (OSError, zipfile.BadZipFile, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageValidationError(f"invalid producer ZIP: {exc}") from exc

    category = str(receipt.get("category") or "")
    slot_id = str(receipt.get("slot_id") or "")
    accepted = receipt.get("accepted_count")
    if accepted is None:
        accepted = (receipt.get("batch_summary") or {}).get("accepted_count", 0)
    duplicates = receipt.get("duplicate_count")
    if duplicates is None:
        duplicates = (receipt.get("batch_summary") or {}).get("duplicate_count", 0)
    try:
        accepted_count = int(accepted or 0)
        duplicate_count = int(duplicates or 0)
    except (TypeError, ValueError) as exc:
        raise PackageValidationError("receipt counters must be integers") from exc
    if accepted_count <= 0:
        raise PackageValidationError("accepted_count must be positive")
    if duplicate_count != 0:
        raise PackageValidationError("duplicate_count must be zero")

    if category == "AAYS_LAYER24_EVIDENCE_V1":
        family = "layer24"
        valid_slots = LAYER24_VALID_SLOTS
    else:
        family = "plan0"
        valid_slots = set(CATEGORY_SLOTS.get(category, ()))
    if slot_id not in valid_slots:
        raise PackageValidationError(
            f"slot {slot_id!r} is not valid for category {category!r}"
        )
    lineage = (
        receipt.get("lineage_id")
        or (receipt.get("lineage") or {}).get("lineage_id")
        or digest[:16]
    )
    return ValidatedPackage(
        path=path,
        sha256=digest,
        family=family,
        slot_id=slot_id,
        lineage_id=_safe_part(lineage, digest[:16]),
        accepted_count=accepted_count,
        receipt=receipt,
    )


class GitHubAtomicUploader:
    def __init__(self, repository: str, token: str, branch: str = "main") -> None:
        if not token:
            raise RuntimeError("AAYS_GITHUB_TOKEN is not configured")
        self.repository = repository
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repository}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "AAYS-Producer-Uploader/1",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(self, method: str, endpoint: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + endpoint,
            data=data,
            method=method,
            headers={**self.headers, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[-1000:]
            raise RuntimeError(f"GitHub HTTP {exc.code}: {detail}") from exc
        return json.loads(body) if body else {}

    def _blob(self, payload: bytes) -> str:
        result = self._request(
            "POST", "/git/blobs",
            {"content": base64.b64encode(payload).decode("ascii"), "encoding": "base64"},
        )
        return str(result["sha"])

    def upload(self, package: ValidatedPackage, attempts: int = 3) -> dict[str, str]:
        filename = _safe_part(package.path.name, f"{package.sha256}.zip")
        remote_dir = (
            f"incoming/{package.family}/{package.slot_id}/{package.lineage_id}"
        )
        remote_zip = f"{remote_dir}/{package.sha256[:16]}__{filename}"
        remote_sidecar = f"{remote_zip}.sha256"
        package_bytes = package.path.read_bytes()
        sidecar_bytes = f"{package.sha256}  {Path(remote_zip).name}\n".encode("ascii")

        for attempt in range(1, attempts + 1):
            ref = self._request("GET", f"/git/ref/heads/{urllib.parse.quote(self.branch)}")
            parent_sha = str(ref["object"]["sha"])
            commit = self._request("GET", f"/git/commits/{parent_sha}")
            base_tree = str(commit["tree"]["sha"])
            tree = self._request(
                "POST", "/git/trees",
                {
                    "base_tree": base_tree,
                    "tree": [
                        {"path": remote_zip, "mode": "100644", "type": "blob", "sha": self._blob(package_bytes)},
                        {"path": remote_sidecar, "mode": "100644", "type": "blob", "sha": self._blob(sidecar_bytes)},
                    ],
                },
            )
            created = self._request(
                "POST", "/git/commits",
                {
                    "message": f"AAYS producer {package.slot_id} {package.sha256[:16]}",
                    "tree": tree["sha"],
                    "parents": [parent_sha],
                },
            )
            try:
                self._request(
                    "PATCH", f"/git/refs/heads/{urllib.parse.quote(self.branch)}",
                    {"sha": created["sha"], "force": False},
                )
                return {
                    "commit_sha": str(created["sha"]),
                    "remote_zip": remote_zip,
                    "remote_sidecar": remote_sidecar,
                }
            except RuntimeError as exc:
                if attempt == attempts or not any(code in str(exc) for code in ("409", "422")):
                    raise
                time.sleep(attempt)
        raise RuntimeError("GitHub upload retries exhausted")


def process_package(path: Path, uploader: GitHubAtomicUploader | None, dry_run: bool) -> dict:
    package = validate_package(path)
    result: dict[str, Any] = {
        "ok": True,
        "source": str(package.path),
        "sha256": package.sha256,
        "family": package.family,
        "slot_id": package.slot_id,
        "lineage_id": package.lineage_id,
        "accepted_count": package.accepted_count,
        "dry_run": dry_run,
    }
    if not dry_run:
        if uploader is None:
            raise RuntimeError("uploader is required outside dry-run mode")
        result.update(uploader.upload(package))
    return result


def watch_outbox(args: argparse.Namespace, uploader: GitHubAtomicUploader | None) -> int:
    outbox = Path(args.outbox)
    sent = Path(args.sent or outbox.parent / "sent")
    rejected = Path(args.rejected or outbox.parent / "rejected")
    state_path = Path(args.state or outbox.parent / "producer_state.json")
    outbox.mkdir(parents=True, exist_ok=True)
    sent.mkdir(parents=True, exist_ok=True)
    rejected.mkdir(parents=True, exist_ok=True)
    state: dict[str, Any] = {"uploaded_sha256": [], "events": []}
    try:
        state.update(json.loads(state_path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    uploaded = set(state.get("uploaded_sha256") or [])

    while True:
        for path in sorted(outbox.glob("*.zip"), key=lambda item: item.stat().st_mtime):
            if time.time() - path.stat().st_mtime < 3:
                continue
            try:
                package = validate_package(path)
                if package.sha256 in uploaded:
                    destination = sent / path.name
                    shutil.move(str(path), str(destination))
                    continue
                row = process_package(path, uploader, args.dry_run)
                if not args.dry_run:
                    uploaded.add(package.sha256)
                    shutil.move(str(path), str(sent / path.name))
            except Exception as exc:  # one bad package must not stop the producer
                row = {"ok": False, "source": str(path), "error": str(exc)}
                shutil.move(str(path), str(rejected / path.name))
            row["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            events = list(state.get("events") or [])[-199:]
            events.append(row)
            state.update({"uploaded_sha256": sorted(uploaded), "events": events, "last_event": row})
            atomic_json(state_path, state)
            print(json.dumps(row, ensure_ascii=False), flush=True)
        if args.once:
            return 0
        time.sleep(max(5, args.poll_seconds))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", help="validate/upload one package")
    parser.add_argument("--outbox", default=r"C:\AAYS_Producer\outbox")
    parser.add_argument("--sent")
    parser.add_argument("--rejected")
    parser.add_argument("--state")
    parser.add_argument("--repository", default="cagdascagdas100/chat_gpt_clone_1")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = resolve_github_token()
    uploader = None if args.dry_run else GitHubAtomicUploader(args.repository, token, args.branch)
    if args.package:
        print(json.dumps(process_package(Path(args.package), uploader, args.dry_run), indent=2))
        return 0
    return watch_outbox(args, uploader)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PackageValidationError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
