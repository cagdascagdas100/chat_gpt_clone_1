# Height Difference 1 revision 8 geometry, datum and quality gate

- Scope: only `height_difference_1`, parcels `1-30761`.
- Existing logical task and idempotency key are preserved.
- No new or parallel runner is created.
- Official HMLR monthly bulk-GML evidence now requires `match=true`, a valid SHA-256, Barnet/Enfield authority, an INSPIRE identifier, a valid non-zero polygon and the candidate BNG point inside the polygon.
- EA 1 m evidence now requires EPSG:27700, 1 m-class pixel size, at least one valid polygon pixel and internally consistent median/min/max/IQR.
- OS Terrain 50 evidence now requires a 200x200, 50 m ASCII grid, a valid non-NoData cell and official MD5 verification whenever an MD5 is supplied.
- EA and OS heights are explicitly aligned to EPSG:5701 / Ordnance Datum Newlyn for these London candidates.
- Deterministic self-tests: `14/14` passed.
- Network execution was not performed here; it remains reserved for the canonical F portable single shared runner.
- `final_ready=false`; no parcel measurement was promoted.
