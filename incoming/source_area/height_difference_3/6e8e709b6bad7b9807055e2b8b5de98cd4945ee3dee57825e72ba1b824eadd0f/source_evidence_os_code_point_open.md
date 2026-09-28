# Ordnance Survey Code-Point Open — source-area / postcode-location bridge evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-28T17:16:00+03:00

Official source
- Publisher: Ordnance Survey
- Product: Code-Point Open
- Official product page: https://www.ordnancesurvey.co.uk/products/code-point-open
- Official documentation: https://docs.os.uk/os-downloads/products/areas-and-zones-portfolio/code-point-open
- Technical product structure: https://docs.os.uk/os-downloads/products/areas-and-zones-portfolio/code-point-open/code-point-open-technical-specification/product-structure
- National Data Library dataset ID: c1e0176d-59fb-4a8c-92c9-c8b376a80687
- Harvest GUID: 4a44536b-6fd2-416e-bef9-59ec5fe55ca8
- Coverage: Great Britain
- Official metadata extent: west -8.655, south 49.90, east 1.79, north 60.85
- Postcode coordinate CRS: British National Grid / EPSG:27700
- Formats: CSV and GeoPackage
- Update cadence: quarterly / every three months, publication months February, May, August and November
- Access: OS OpenData; free to use for everyone

Field evidence relevant to the missing canonical link
- Postcode: postcode-unit identifier.
- Easting / Northing: British National Grid coordinate in metres.
- Positional Quality Indicator (PQI): coordinate-quality flag.
- Administrative district code: local authority/district context.
- OS documentation states postcode coordinates are supplied to a resolution of 1 metre.

Geometry semantics
The Polygon in records.geojson is only the official National Data Library metadata coverage envelope for Great Britain. It is evidence_scope=coverage_area and is not a parcel/property/postcode-unit polygon.

Scope decision
No postcode value is assigned to canonical partition rows 61523–92283 because this execution context still does not expose a trusted canonical postcode, UPRN, point, or parcel geometry. Therefore no Code-Point row is promoted to parcel evidence.

Height Difference next step
Local OpenCode must expose a trusted canonical postcode or geometry. A postcode can then bind to Code-Point Open coordinates/admin district, continue through UPRN/linked-identifier/building-footprint sources as appropriate, and only for footprint-proven canonical parcels compute official DEM/LIDAR min/max/mean/max-min.
