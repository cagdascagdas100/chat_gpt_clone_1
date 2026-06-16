from fastapi import APIRouter

router = APIRouter(tags=["map-layers"])

@router.get("/map/layers")
def map_layers():
    return {
        "status": "ok",
        "layers": ["distance-property-types"],
        "note": "Minimal map_layers router restored for AAYS runner smoke compatibility."
    }
