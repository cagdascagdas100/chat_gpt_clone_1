# Ordnance Survey OS Open Zoomstack / local_buildings — source-area evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-27T19:26:00+03:00

Official/public identifiers
- National Data Library dataset ID: d34f5fb0-b40e-4641-a989-9c1f6f11348c
- Harvest GUID: 5f1ec104-f61b-48f9-99f3-f31da8a8fb7d
- Publisher: Ordnance Survey
- GeoPackage CRS: EPSG:27700
- Coverage: Great Britain
- Official metadata extent: west -8.655, south 49.90, east 1.79, north 60.85
- Publication cycle in current OS product documentation: June and December

Building layer semantics
- GeoPackage layer: local_buildings
- Geometry type: Polygon
- Attributes include id and uuid
- OS documentation describes Building content as generalised building footprints at local and district resolutions.
- The local-building uuid can style/distinguish features but is not persistent between product versions.

Public no-login access evidence
- OS Downloads API documentation states that OS OpenData endpoints do not require an API key.
- OS Open Zoomstack is an OS OpenData product, supplied as GeoPackage and vector tiles.

Official URLs
- https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-open-zoomstack
- https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-open-zoomstack/os-open-zoomstack-technical-specification
- https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-open-zoomstack/os-open-zoomstack-technical-specification/geopackage-schema
- https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-open-zoomstack/os-open-zoomstack-technical-specification/list-of-layers
- https://docs.os.uk/os-apis/accessing-os-apis/os-downloads-api/technical-specification
- https://www.data.gov.uk/dataset/d34f5fb0-b40e-4641-a989-9c1f6f11348c/os-open-zoomstack

Height Difference semantics
This is source-area evidence only. No canonical parcel is accepted. Local OpenCode must materialize the local_buildings polygons, intersect them with canonical parcels 61523–92283, retain building-present parcels, then use the already collected official EA/OS DEM/LIDAR sources for min/max/mean/max-min statistics.
