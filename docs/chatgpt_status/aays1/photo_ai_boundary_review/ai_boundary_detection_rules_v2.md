# AAYS AI Boundary Detection Rules v2

PAGE_KEY: aays1
STATUS: active
FINAL_READY: false

## Purpose
Use listing photos as visual evidence to increase confidence only when the visible parcel boundary agrees with the existing parcel polygon.

## Confidence rules
- 3/4: existing real parcel polygon is present, but no visual photo confirmation yet.
- 3.25/4: listing photo supports the land parcel but boundary is not clear enough.
- 3.5/4: photo boundary is visible and visually consistent with the existing polygon shape.
- 3.75/4: photo boundary, listing map/satellite, and existing polygon strongly agree.
- 4/4: official title plan, cadastre, survey, or authoritative legal plan confirms the geometry.

## Required AI checks per row
1. Open source/listing URL.
2. Collect candidate listing photos.
3. Select the best boundary evidence photo.
4. Identify whether parcel boundary is visible.
5. Classify photo boundary type: red line, dashed line, fence, road frontage, hedge/tree line, map/satellite overlay, drone/aerial, site plan, or unclear.
6. Render the existing polygon.
7. Compare visible photo boundary with existing polygon shape.
8. Write structured JSON result.

## Safe geometry rule
The photo-derived shape is not allowed to overwrite the stored official/source polygon automatically.
It can only:
- upgrade confidence when consistent,
- create candidate_photo_geometry when visible,
- flag geometry_mismatch when materially different,
- send the row to manual or additional-source recovery.

## Upgrade gate for 3.5/4
All of these must be true:
- photo_boundary_visible = true
- visual_match_score >= 0.70
- geometry_mismatch_flag = false
- existing_polygon_shape_type is present
- candidate_photo_geometry or photo_shape_type is present

## Mismatch gate
Set geometry_mismatch_flag = true when:
- photo shape is materially different from existing polygon,
- road frontage/orientation is inconsistent,
- photo boundary suggests a compact plot but stored polygon is long/narrow, or the reverse,
- AI cannot reconcile the visible boundary with the existing polygon.
