from __future__ import annotations

import datetime as dt
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, brownfield, contractor, cost, etl, facilities, future_growth, health, listings, map_layers, ops, parcels, planned_assets, proxy, sources
from app.api.routes import aays_sales_layers
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

app.include_router(health.router)
app.include_router(sources.router)
app.include_router(admin.router)
app.include_router(etl.router)
app.include_router(facilities.router)
app.include_router(cost.router)
app.include_router(cost.admin_router)
app.include_router(parcels.router)
app.include_router(planned_assets.router)
app.include_router(planned_assets.admin_router)
app.include_router(listings.router)
app.include_router(brownfield.router)
app.include_router(map_layers.router)
app.include_router(future_growth.router)
app.include_router(contractor.router)
app.include_router(proxy.router)
app.include_router(ops.router)

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

app.include_router(aays_sales_layers.router)
# AAYS sales-history parcel/evidence layer routes
from app.api.routes import aays_sales_history_layers
from app.middleware.map_listings_cache import MapListingsCacheMiddleware
from app.api.routes.contractor_exports import router as contractor_exports_router
app.include_router(aays_sales_history_layers.router)

# AAYS performance patch: lightweight TTL cache for /map/listings
try:
    app.add_middleware(MapListingsCacheMiddleware)
except Exception as _aays_map_listings_cache_error:
    print(f"[AAYS] MapListingsCacheMiddleware not enabled: {_aays_map_listings_cache_error}")

app.include_router(contractor_exports_router)
