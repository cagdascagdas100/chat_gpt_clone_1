from app.api.routes import planned_assets


def test_planned_assets_route_exports_router_and_admin_router():
    assert planned_assets.router is not None
    assert planned_assets.admin_router is not None


def test_planned_assets_route_contains_parcel_layer_endpoint():
    paths = {route.path for route in planned_assets.router.routes}
    assert "/planned-assets/parcel-layer" in paths
