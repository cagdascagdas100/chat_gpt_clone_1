from __future__ import annotations

import importlib
import pkgutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI

app = FastAPI(title="TerraYield AAYS local API", version="aays-local-evidence")

_INCLUDED_ROUTERS: list[str] = []
_ROUTER_IMPORT_ERRORS: dict[str, str] = {}

try:
    routes_pkg = importlib.import_module("app.api.routes")
    for info in pkgutil.iter_modules(getattr(routes_pkg, "__path__", [])):
        if info.name.startswith("_"):
            continue
        mod_name = f"app.api.routes.{info.name}"
        try:
            mod = importlib.import_module(mod_name)
            router = getattr(mod, "router", None)
            if router is not None:
                app.include_router(router)
                _INCLUDED_ROUTERS.append(mod_name)
        except Exception as exc:
            _ROUTER_IMPORT_ERRORS[mod_name] = repr(exc)
except Exception as exc:
    _ROUTER_IMPORT_ERRORS["app.api.routes"] = repr(exc)

@app.get("/health", tags=["runtime"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "aays-local-api",
        "included_router_count": len(_INCLUDED_ROUTERS),
        "import_error_count": len(_ROUTER_IMPORT_ERRORS),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/mapdata/live-evidence", tags=["mapdata"])
def mapdata_live_evidence() -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    status_root = repo_root / "docs" / "chatgpt_status"
    evidence_files = sorted(status_root.glob("AAYS_MAPDATA_LIVE_EVIDENCE_*.txt"))[-10:]
    route_root = Path(__file__).resolve().parent / "api" / "routes"
    route_files = sorted(route_root.glob("*.py")) if route_root.exists() else []
    return {
        "status": "ok",
        "evidence_mode": "runtime_inventory_only_no_db_write",
        "repo_root": str(repo_root),
        "included_routers": _INCLUDED_ROUTERS,
        "router_import_errors": _ROUTER_IMPORT_ERRORS,
        "route_files": [p.name for p in route_files],
        "recent_mapdata_evidence_files": [p.name for p in evidence_files],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
