from __future__ import annotations

import datetime as dt
import importlib
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Parcel-centric land opportunity intelligence service for TerraYield",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _include_optional_router(module_name: str, attr_name: str = "router") -> None:
    try:
        module = importlib.import_module(module_name)
        router = getattr(module, attr_name, None)
        if router is not None:
            app.include_router(router)
    except Exception as exc:
        print(f"[AAYS] Optional router not enabled: {module_name}.{attr_name}: {exc}")


for _module_name in (
    "app.api.routes.health",
    "app.api.routes.sources",
    "app.api.routes.admin",
    "app.api.routes.etl",
    "app.api.routes.facilities",
    "app.api.routes.cost",
    "app.api.routes.parcels",
    "app.api.routes.planned_assets",
    "app.api.routes.listings",
    "app.api.routes.brownfield",
    "app.api.routes.map_layers",
    "app.api.routes.future_growth",
    "app.api.routes.contractor",
    "app.api.routes.proxy",
    "app.api.routes.ops",
    "app.api.routes.aays_sales_layers",
    "app.api.routes.aays_sales_history_layers",
):
    _include_optional_router(_module_name)

for _module_name, _attr_name in (
    ("app.api.routes.cost", "admin_router"),
    ("app.api.routes.planned_assets", "admin_router"),
):
    _include_optional_router(_module_name, _attr_name)

frontend_candidates = [
    Path(__file__).resolve().parents[2] / "england_map_web",
    Path(__file__).resolve().parents[1] / "england_map_web",
    Path.cwd() / "england_map_web",
    Path("/app/england_map_web"),
    Path("/england_map_web"),
]
for frontend_dir in frontend_candidates:
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

try:
    from app.middleware.map_listings_cache import MapListingsCacheMiddleware

    app.add_middleware(MapListingsCacheMiddleware)
except Exception as _aays_map_listings_cache_error:
    print(f"[AAYS] MapListingsCacheMiddleware not enabled: {_aays_map_listings_cache_error}")

_include_optional_router("app.api.routes.contractor_exports")
