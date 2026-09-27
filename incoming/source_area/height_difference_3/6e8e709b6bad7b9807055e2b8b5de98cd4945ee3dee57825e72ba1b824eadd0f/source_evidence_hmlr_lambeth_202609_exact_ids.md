# HM Land Registry INSPIRE — Lambeth September 2026 exact-ID source window

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-28T01:18:00+03:00

Current official window
- HM Land Registry INSPIRE download page states the dataset was published on 6 September 2026.
- New files are published on the first Sunday of every month.
- The current page lists London Borough of Lambeth with a GML download.
- INSPIRE Index Polygons are available under the Open Government Licence.
- Each INSPIRE polygon has a unique Land Registry-INSPIRE ID related to a registered title.
- Source page: https://use-land-property-data.service.gov.uk/datasets/inspire/download
- Dataset semantics: https://use-land-property-data.service.gov.uk/datasets/inspire

Canonical exact targets from the existing height_difference_3 lineage
- row 61536 / parcel_61536 / INSPIRE 36760596 / Lambeth / lon -0.1434117 / lat 51.4138507
- row 61537 / parcel_61537 / INSPIRE 36758146 / Lambeth / lon -0.1435312 / lat 51.4151588
- row 61538 / parcel_61538 / INSPIRE 36781190 / Lambeth / lon -0.1425771 / lat 51.4147003
- row 61539 / parcel_61539 / INSPIRE 36776765 / Lambeth / lon -0.1421382 / lat 51.4151720

Canonical provenance
- Candidate manifest: docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/059_candidate_manifest_61536_61539_batch_115.json
- Candidate manifest blob SHA: 8d8f3186dd530187849b1bc8b545b77fed9076c6
- The lineage requires exact official INSPIRE ID matching; point-in-polygon-only or nearest substitution is not accepted.
- The prior July 2026 Lambeth GML window is not reused. This package targets the current September 2026 monthly publication.

Binary materialization attempts
1. Web direct current Lambeth download: failed with redirect-loop detection.
2. Direct download action to the same official URL: failed.
3. Container HTTPS request: failed at DNS resolution for use-land-property-data.service.gov.uk.
No current September Lambeth GML bytes were obtained, so no source-binary SHA-256 or polygon vertices are claimed.

Height Difference acceptance
No parcel acceptance is performed. Exact current HMLR polygon geometry is still required, followed by real building-footprint confirmation and official DEM/LIDAR min/max/mean/max-min.
