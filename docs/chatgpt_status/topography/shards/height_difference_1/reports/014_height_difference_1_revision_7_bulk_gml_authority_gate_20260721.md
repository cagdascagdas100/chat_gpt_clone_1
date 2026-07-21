# Height Difference 1 — revision 7 official bulk-GML authority gate

- Slot: `height_difference_1`
- Task ID unchanged: `height-difference-1-official-boundary-elevation-samples-20260720`
- Payload revision: `7`
- Validation: `10/10`
- Network execution: not performed; canonical F portable single shared runner remains required.
- Measured rows written: `0`
- `final_ready=false`

## Official contract correction

HM Land Registry documents the free INSPIRE Index Polygon product as monthly local-authority GML delivery and lists API availability as `No`. WFS is retained only as a diagnostic cross-check. A parcel boundary can be promoted only when the monthly GML polygon, geometry, and source SHA-256 are present.

## Acceptance

A row is measured only when all conditions pass:

1. official monthly HMLR bulk GML real polygon,
2. no bulk/WFS identity or disjoint-bbox conflict,
3. EA DTM 1m polygon-masked numeric statistics,
4. independent OS Terrain 50 numeric value,
5. EA/OS absolute difference not above 8 m.

WFS-only geometry, centroid-only geometry, missing hash, source conflict, or missing independent numeric evidence remains `NO_DATA_NOT_INFERRED`.
