# Ordnance Survey OS OpenMap – Local / Building — source-area evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-27

Official/public metadata identifiers
- National Data Library dataset ID: 3760f49c-cfe7-488f-91f7-79f1ace7b539
- Harvest GUID: 49ab56d6-51b7-4500-8107-6cb17327256f
- Publisher: Ordnance Survey
- Dataset CRS: EPSG:27700
- Dataset metadata extent: west -8.655, south 49.90, east 1.79, north 60.85
- Product update cadence: bi-annually, April and October

Building feature semantics from official OS technical documentation
- Building is a built entity that includes a roof.
- Geometry is a polygon / GM_Surface.
- OS OpenMap – Local building geometries are generalised and derived from OS MasterMap large-scale data.
- Product coverage is Great Britain.
- OS OpenData is licensed for reuse under the Open Government Licence.

Official documentation
- https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-openmap-local
- https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-openmap-local/os-openmap-local-technical-specification/feature-types/building
- https://docs.os.uk/os-downloads/resources/product-resources/product-refresh-dates
- https://www.data.gov.uk/dataset/3760f49c-cfe7-488f-91f7-79f1ace7b539/os-openmap-local1
- https://www.ordnancesurvey.co.uk/products/open-data

Official API endpoint intended for local materialization
- https://api.os.uk/downloads/v1/products/OpenMapLocal/downloads?area=GB&format=GeoPackage&redirect

Execution note
The API binary was not materialized in this session because the execution container returned DNS resolution failure for api.os.uk. No remote binary SHA-256 is claimed. This package therefore records the official dataset/source-area metadata and exact identifiers only.

Height Difference semantics
No parcel is accepted here. Local OpenCode must materialize the Building polygons, spatially intersect them with canonical parcels 61523–92283 to determine building-present parcels, then intersect those parcels/buildings with the already collected official EA/OS terrain source indexes and calculate official DEM/LIDAR min/max/mean/max-min values.
