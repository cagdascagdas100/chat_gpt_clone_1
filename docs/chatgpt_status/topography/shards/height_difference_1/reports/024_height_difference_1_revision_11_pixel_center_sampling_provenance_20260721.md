# Height Difference 1 revision 11 pixel-center sampling provenance gate

- Same logical task and idempotency key are preserved.
- Revision 11 adds a final raster-footprint provenance gate after revision 10.
- Measured promotion requires `all_touched=false`, explicit pixel-center inclusion, a SHA-256 for the selected-pixel mask, matching selected-pixel counts, and matching declared/recomputed parcel area.
- This prevents elevations from pixels that merely touch the parcel boundary from inflating parcel maximum-minus-minimum range.
- Environment Agency DTM 1m remains the primary parcel-range source.
- OS Terrain 50 remains an independent absolute-elevation and ODN crosscheck only.
- Source-level validation: `20/20`.
- Runtime/network execution was not performed because the canonical F portable single shared runner is required.
- `final_ready=false`
