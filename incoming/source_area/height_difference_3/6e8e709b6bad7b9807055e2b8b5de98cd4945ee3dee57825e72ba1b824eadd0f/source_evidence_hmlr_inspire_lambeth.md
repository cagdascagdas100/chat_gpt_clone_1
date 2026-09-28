# HM Land Registry INSPIRE Lambeth current exact-ID window

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-29T01:28:00+03:00

Official current source
- HM Land Registry INSPIRE Index Polygons spatial data.
- Current download page: https://use-land-property-data.service.gov.uk/datasets/inspire/download
- The current page states publication date 6 September 2026, monthly publication on the first Sunday, and lists London Borough of Lambeth for download.
- Official Lambeth endpoint pinned by the existing canonical runner: https://use-land-property-data.service.gov.uk/datasets/inspire/download/London_Borough_of_Lambeth.zip
- Dataset is open/free under OGL conditions and contains freehold registered-property polygons for England and Wales.

Canonical binding discovered in repository
- Canonical source: england_map_web/data/program_layer_matrix/security.geojson
- Pinned source Git blob: 8afd1d2bac414cf0f6b9484014e7878a4ceff877
- Existing exact candidate manifest: docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/059_candidate_manifest_61536_61539_batch_115.json
- Candidate manifest blob: 8d8f3186dd530187849b1bc8b545b77fed9076c6
- Exact candidate IDs:
  - row 61536: parcel_61536, HMLR INSPIRE 36760596, BNG 529209.089, 169949.549
  - row 61537: parcel_61537, HMLR INSPIRE 36758146, BNG 529197.094, 170094.802
  - row 61538: parcel_61538, HMLR INSPIRE 36781190, BNG 529264.73, 170045.496
  - row 61539: parcel_61539, HMLR INSPIRE 36776765, BNG 529293.92, 170098.724

Materialization result
The official page and exact Lambeth endpoint were verified, but this session could not materialize the current GML/ZIP bytes: the web fetch layer reports a redirect loop and the container reports DNS resolution failure. Therefore no HMLR parcel polygon is claimed, no building footprint is claimed, and accepted_count remains zero.

Geometry semantics
records.geojson contains only an operational Polygon query window around the four pinned canonical points. It is evidence_scope=coverage_area and is explicitly not an HMLR parcel/property/building polygon.

Next gate
Materialize the current Lambeth HMLR GML, require exactly one polygon for each exact INSPIRE ID, then verify real building footprint presence and calculate official DEM/LIDAR min/max/mean/max-min only for footprint-proven canonical parcels.
