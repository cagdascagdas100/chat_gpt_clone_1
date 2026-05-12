#!/usr/bin/env python3
"""Safe contractor DB environment loading utilities."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse, urlunparse

DB_ENV_KEYS = ("DATABASE_URL", "PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGPORT")
BRIDGE_LOCAL_SECRET_PATH = Path(r"C:\AAYS1_GITHUB_BRIDGE\local-secrets\contractor-db.env")


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _merge_missing(target: dict[str, str], source: dict[str, str]) -> None:
    for key in DB_ENV_KEYS:
        value = source.get(key)
        if value and not target.get(key):
            target[key] = value
    contractor_url = source.get("CONTRACTOR_DATABASE_URL")
    if contractor_url and not target.get("DATABASE_URL"):
        target["DATABASE_URL"] = contractor_url


def _build_database_url(values: dict[str, str]) -> str | None:
    if values.get("DATABASE_URL"):
        return values["DATABASE_URL"]
    host = values.get("PGHOST")
    database = values.get("PGDATABASE")
    user = values.get("PGUSER")
    password = values.get("PGPASSWORD")
    if not (host and database and user and password):
        return None
    port = values.get("PGPORT") or "5432"
    return f"postgresql://{quote(user)}:{quote(password)}@{host}:{port}/{quote(database)}"


def load_contractor_env(project_root: Path) -> dict[str, Any]:
    """Load DB credentials in precedence order without logging secret values."""
    root = project_root.resolve()
    merged: dict[str, str] = {}
    _merge_missing(merged, dict(os.environ))
    _merge_missing(merged, _parse_env_file(root / ".env.local"))
    _merge_missing(merged, _parse_env_file(root / ".env"))
    _merge_missing(merged, _parse_env_file(BRIDGE_LOCAL_SECRET_PATH))
    database_url = _build_database_url(merged)
    report = {
        "database_url_present": bool(merged.get("DATABASE_URL")),
        "pghost_present": bool(merged.get("PGHOST")),
        "pgdatabase_present": bool(merged.get("PGDATABASE")),
        "pguser_present": bool(merged.get("PGUSER")),
        "pgpassword_present": bool(merged.get("PGPASSWORD")),
        "pgport_present": bool(merged.get("PGPORT")),
        "db_credentials_present": bool(database_url),
    }
    return {
        "database_url": database_url,
        "env": merged,
        "report": report,
        "loaded_paths": {
            "env_local_present": (root / ".env.local").exists(),
            "env_present": (root / ".env").exists(),
            "bridge_local_secrets_present": BRIDGE_LOCAL_SECRET_PATH.exists(),
        },
    }


def redact_secrets(text: Any, env_info: dict[str, Any]) -> str:
    """Mask known DB secret material from exception strings and status details."""
    redacted = str(text)
    candidates: set[str] = set()
    database_url = env_info.get("database_url")
    if database_url:
        candidates.add(str(database_url))
        parsed = urlparse(str(database_url))
        if parsed.password:
            candidates.add(parsed.password)
        if parsed.username:
            candidates.add(parsed.username)
        if parsed.netloc:
            safe_netloc = parsed.netloc
            if parsed.password:
                safe_netloc = safe_netloc.replace(parsed.password, "[REDACTED]")
            candidates.add(urlunparse(parsed._replace(netloc=safe_netloc)))
    env_values = env_info.get("env") if isinstance(env_info.get("env"), dict) else {}
    for key in ("PGPASSWORD", "DATABASE_URL", "CONTRACTOR_DATABASE_URL"):
        value = env_values.get(key)
        if value:
            candidates.add(str(value))
    for value in sorted(candidates, key=len, reverse=True):
        if value:
            redacted = redacted.replace(value, "[REDACTED]")
    return redacted
