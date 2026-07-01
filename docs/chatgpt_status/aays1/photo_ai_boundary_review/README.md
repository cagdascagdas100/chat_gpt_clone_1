# AAYS photo AI boundary review

Goal: add a photo-evidence layer on top of existing parcel GeoJSON review.

Confidence rules:
- 3/4: existing matched parcel geometry from official/metadata pipeline.
- 3.25/4: listing photo supports land type/location but boundary is partial.
- 3.5/4: listing photo shows a marked or visible boundary and the visible shape is consistent with existing parcel polygon.
- 3.75/4: listing photo, listing map, satellite context and existing polygon strongly agree.
- 4/4: official survey/cadastre authority confirmation.

Pipeline:
1. Read each listing URL from the 1264 geometry table.
2. Extract listing image URLs and source page evidence.
3. Download images to a local evidence folder outside git when large.
4. Render the existing GeoJSON polygon to a small PNG/SVG.
5. Send listing image plus polygon render to a vision model.
6. Save structured JSON result per row.
7. Update the review table columns: photo evidence, visual match score, mismatch flag, confidence after photo check.

Safety rule: photo evidence must never replace official geometry. It can only upgrade confidence to 3.5/4 or flag mismatch for human review.

Current status: integration scaffold added. Full automated photo download and vision execution needs local runner/API credentials.
