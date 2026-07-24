# Height Difference 1 revision 9 — parcel height-difference metric gate

- Metric definition: maximum minus minimum valid EA LIDAR Composite DTM 1m elevation pixel inside the official HMLR parcel polygon.
- Unit: metre.
- Minimum valid EA pixels: 3.
- EA 1m is the parcel-range measurement source.
- OS Terrain 50 is an independent absolute-elevation and Ordnance Datum Newlyn crosscheck; its 50m grid is not promoted as the parcel-range measurement.
- EA 2m and 10m are same-provider resolution checks, not independent sources.
- Source vertical RMSE recorded: 0.15m.
- Indicative two-endpoint RSS RMSE recorded: 0.212m.
- Deterministic validation: 14/14 passed.
- Network execution was not performed outside the canonical F portable single shared runner.
- `final_ready=false`.
