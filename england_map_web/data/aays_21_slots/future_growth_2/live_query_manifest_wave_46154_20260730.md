# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T21:00:25+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 75 attempts; parallelism 75; exit 6 x75; HTTP 000 x75; body bytes 0; JSON 0/75; raw-response SHA-256 0/75.

Query manifest SHA-256: `6769dd43cb5b550ad919afa6b698b96903d84882ae479f0f6466441c37e1c6e0`
Transport results SHA-256: `0bf7a27aeba59a9c172a3ebba036fb90128c5bd618b855942f2dabc3a3017c68`

Layers crossed with rows 30762, 46142 and 61522:
- IMA02 0 Streetmanager Permits (Points) (esriGeometryPoint)
- IMA02 1 Streetmanager Activity (Points) (esriGeometryPoint)
- IMA02 2 Section 58s (Lines) (esriGeometryPolyline)
- IMA02 3 Streetmanager Permits (Lines) (esriGeometryPolyline)
- IMA02 4 Streetmanager Activity (Lines) (esriGeometryPolyline)
- IMA02 5 Section 58s (Areas) (esriGeometryPolygon)
- IMA02 6 Streetmanager Permits (Areas) (esriGeometryPolygon)
- IMA02 7 Streetmanager Activity (Areas) (esriGeometryPolygon)
- IMA02 8 Postcode Units (esriGeometryPolygon)
- IMA02 9 Ward Boundaries (esriGeometryPolygon)
- IMA02 10 TfL Cycle Routes (Open and In Progress) (esriGeometryPolyline)
- IMA02 11 Index of Multiple Deprivation 2019 (esriGeometryPolygon)
- IMA02 12 UKPN Primary Substation Capacity (esriGeometryPolygon)
- IMA02 13 UKPN Grid Supply Points (esriGeometryPoint)
- IMA03 0 SuDS Completed Projects (esriGeometryPoint)
- IMA03 1 TfL Bus Stops (esriGeometryPoint)
- IMA03 2 TfL Bus Garages (esriGeometryPoint)
- IMA03 3 TfL Bus Routes (esriGeometryPolyline)
- IMA03 4 Supply Flow Monitoring Zones (esriGeometryPolygon)
- IMA03 5 Supply District Metering Area (esriGeometryPolygon)
- IMA03 6 Sewerage Drainage Area Catchment (esriGeometryPolygon)
- IMA03 7 UKPN Grid Sites (esriGeometryPoint)
- IMA03 8 UKPN Primary Sites (esriGeometryPoint)
- IMA03 10 TfL Strategic Road Network (esriGeometryPolyline)
- IMA03 11 UKPN Secondary Sites (esriGeometryPoint)

Every request used the official layer `/query` endpoint with `where=1=1`, EPSG:3857 point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. No membership inference was made from transport failure.

Point and polyline extents were not treated as parcel proximity or exact exclusions. Operational area extents were recorded only as named-layer coverage negatives and not as planning, access, capacity or delivery conclusions.