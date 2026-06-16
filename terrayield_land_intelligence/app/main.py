from __future__ import annotations

import datetime as dt
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


def _fallback_settings() -> SimpleNamespace:
    return SimpleNamespace(
        app_name="TerraYield Land Intelligence",
        app_host="127.0.0.1",
        app_port=8010,
        allowed_origins=["*"],
    )


try:
    from app.core.config import get_settings
    settings = get_settings()
except Exception:
    settings = _fallback_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Parcel-centric land opportunity intelligence service for TerraYield",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "allowed_origins", None) or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_include_route_module(module_name: str, router_names: tuple[str, ...] = ("router",)) -> None:
    try:
        module = import_module(f"app.api.routes.{module_name}")
    except Exception:
        return
    for router_name in router_names:
        router = getattr(module, router_name, None)
        if router is not None:
            app.include_router(router)


for module_name, router_names in (
    ("health", ("router",)),
    ("sources", ("router",)),
    ("admin", ("router",)),
    ("etl", ("router",)),
    ("facilities", ("router",)),
    ("cost", ("router", "admin_router")),
    ("parcels", ("router",)),
    ("planned_assets", ("router", "admin_router")),
    ("listings", ("router",)),
    ("brownfield", ("router",)),
    ("map_layers", ("router",)),
    ("future_growth", ("router",)),
    ("contractor", ("router",)),
    ("proxy", ("router",)),
    ("ops", ("router",)),
    ("topography_lookup_v2", ("router", "legacy_router")),
    ("distance_property_types", ("router",)),
    ("aays_sales_layers", ("router",)),
):
    _safe_include_route_module(module_name, router_names)

for frontend_dir in (
    Path(__file__).resolve().parents[2] / "england_map_web",
    Path(__file__).resolve().parents[1] / "england_map_web",
    Path.cwd() / "england_map_web",
    Path("/app/england_map_web"),
    Path("/england_map_web"),
):
    if frontend_dir.exists():
        app.mount("/england_map_web", StaticFiles(directory=frontend_dir, html=True), name="england_map_web")
        break


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ok",
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
    }


def run() -> None:
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)


if __name__ == "__main__":
    run()
