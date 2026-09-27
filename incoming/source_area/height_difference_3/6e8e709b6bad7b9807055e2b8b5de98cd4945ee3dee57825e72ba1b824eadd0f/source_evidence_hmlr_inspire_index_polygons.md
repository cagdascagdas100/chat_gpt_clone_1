# HM Land Registry INSPIRE Index Polygons — source-area/identifier evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-27T19:26:00+03:00

Official identifiers and current publication
- National Data Library dataset ID: 811bcf4c-fbbf-4597-aa9c-3d5bd3bfd455
- Publisher: HM Land Registry
- Dataset: INSPIRE Index Polygons spatial data
- Licence: UK Open Government Licence
- Current download-page publication: 6 September 2026
- Update cadence: first Sunday of each month; files show data from the previous month
- Distribution: GML files separated by local authority across England and Wales
- Public download page: https://use-land-property-data.service.gov.uk/datasets/inspire/download
- Dataset page: https://use-land-property-data.service.gov.uk/datasets/inspire
- National Data Library: https://www.data.gov.uk/dataset/811bcf4c-fbbf-4597-aa9c-3d5bd3bfd455/inspire-index-polygons-spatial-data

Geometry and identifier semantics
- INSPIRE polygons show the position and indicative extent of registered freehold property.
- Each INSPIRE Index Polygon has a unique Land Registry-INSPIRE ID that relates to a registered title.
- A registered title may contain several polygons; each polygon has a separate Land Registry-INSPIRE ID.
- HMLR states that the true extent of a registered title cannot be established from INSPIRE Index Polygons alone; the individual title plan is authoritative for that purpose.

Scope decision
No local-authority GML file is selected in this package because the canonical partition rows 61523–92283 have not been resolved to local authorities in this execution environment. Selecting any GML file would invent scope. This package therefore records one identifier-only source-area record and leaves geometry materialization and spatial matching to local OpenCode.

Height Difference next step
Local OpenCode must resolve the canonical partition to local-authority coverage, download the corresponding HMLR GML files, spatially bind candidate parcel geometries, intersect those candidates with already collected official OS building footprints, retain building-present canonical parcels, and then calculate official DEM/LIDAR min/max/mean/max-min statistics.
