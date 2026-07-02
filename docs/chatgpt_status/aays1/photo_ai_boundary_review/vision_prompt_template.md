# Vision prompt template

Use this prompt for each parcel row.

Input images:
1. Listing photo or listing map image.
2. Existing parcel polygon render from current GeoJSON.

Task:
Compare the visible/marked land parcel in the listing image against the existing parcel polygon render.

Return strict JSON only:

```json
{
  "row_id": "",
  "photo_boundary_visible": true,
  "photo_shape_type": "four_sided_quadrilateral | long_narrow | irregular | unclear | no_boundary",
  "existing_polygon_shape_type": "four_sided_quadrilateral | long_narrow | irregular | multipart | unclear",
  "visual_match_score": 0.0,
  "geometry_mismatch_flag": false,
  "confidence_before": "3/4",
  "confidence_after": "3/4 | 3.25/4 | 3.5/4 | 3.75/4",
  "upgrade_allowed": false,
  "ai_notes": "short evidence-based reason"
}
```

Scoring rule:
- visual_match_score >= 0.75 and no mismatch: allow 3.5/4.
- partial land context only: 3.25/4.
- unclear photo or no boundary: keep 3/4.
- contradiction between photo shape and polygon shape: keep 3/4 and set mismatch flag true.

Never claim the photo is official cadastre evidence. Photo evidence is only a visual confidence layer.
