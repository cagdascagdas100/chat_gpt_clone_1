# ONS Local Authority Districts (May 2026) UK BFC — source-area/identifier evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-27T20:35:00+03:00

Official identifiers
- Publisher: Office for National Statistics
- National Data Library dataset ID: 1616a168-78ab-40c8-a0df-0576925818e2
- ArcGIS item / harvest ID: 3030fda24bc34e3080d326db2942feaf
- Layer: LAD_MAY_2026_UK_BFC, ID 0
- Dataset reference date: May 2026
- Catalogue updated: 10 September 2026
- Boundary type: BFC, full resolution clipped to Mean High Water coastline
- Geometry type: polygon
- Spatial reference: EPSG:27700
- Local-authority code field: LAD26CD
- Local-authority name field: LAD26NM
- Feature data last edit: 8 September 2026
- Public service supports JSON, GeoJSON and PBF queries.

Official service endpoints
- https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_May_2026_Boundaries_UK_BFC/FeatureServer/0
- https://dservices1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/services/Local_Authority_Districts_(May_2026)_Boundaries_UK_BFC/WFSServer?request=getcapabilities&service=wfs
- https://www.data.gov.uk/dataset/1616a168-78ab-40c8-a0df-0576925818e2/local-authority-districts-may-2026-boundaries-uk-bfc

Rights/licence note
The dataset record says it contains both Ordnance Survey and ONS intellectual property rights and leaves its dataset licence field unset. The National Data Library page footer states OGL v3.0 except where otherwise stated. This package preserves both facts and does not silently assign a more specific dataset licence.

Scope decision
This window supplies the official LAD polygon service and exact LAD26 identifiers required to resolve HMLR local-authority GML scope. Canonical partition geometry for rows 61523–92283 is not present in this execution environment, so no LAD intersection or LAD code is invented.

Binary note
The public ArcGIS query endpoint is identified, but the execution container could not resolve the external host to materialize a GeoJSON payload. No remote source-file SHA-256 is claimed.

Height Difference next step
Local OpenCode must intersect canonical partition geometry with LAD26 polygons, select the corresponding HMLR INSPIRE local-authority GML files, bind parcel candidates, intersect official building footprints, retain building-present canonical parcels, and calculate official DEM/LIDAR min/max/mean/max-min statistics.
