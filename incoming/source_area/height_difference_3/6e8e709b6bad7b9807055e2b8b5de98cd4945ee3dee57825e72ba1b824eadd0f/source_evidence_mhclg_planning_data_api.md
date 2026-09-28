# MHCLG Planning Data API entity search — source-area / canonical-link bridge evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-28T02:30:00+03:00

Official service
- Publisher/service: Ministry of Housing, Communities and Local Government / Planning Data
- API documentation: https://www.planning.data.gov.uk/docs
- Search endpoint: /entity.{extension}
- Supported extensions: json and geojson
- q parameter: search by postcode or Unique Property Reference Number (UPRN)
- Coordinate search: latitude + longitude can return entities whose geometries intersect the point
- Geometry search: WKT geometry with configurable relations including within, intersects, contains, covers, overlaps and others
- Core returned fields documented by the service include geometry and point.

Public entity evidence
- Public example entity: https://www.planning.data.gov.uk/entity/7002112005
- The entity page exposes a MULTIPOLYGON geometry, POINT (-1.499874 50.916716), UPRN 100060501821, address text including postcode SO40 8WE, and quality=authoritative.
- This example proves that Planning Data entity records can co-locate UPRN, address/postcode, representative point and real polygon geometry in one public record; it is not part of the canonical partition and is not accepted as a parcel record.

Public access
The documentation, example API-response links and entity pages are publicly accessible without an authentication/login step.

Scope decision
No API query is issued for canonical partition rows 61523–92283 because the execution context still does not expose a trusted canonical postcode, UPRN, latitude/longitude or geometry. Querying arbitrary identifiers would fabricate scope.

Height Difference next step
Local OpenCode must expose one trusted canonical key/geometry. It can then query or bulk-match Planning Data by postcode/UPRN/coordinate/geometry, connect to OS Open UPRN / OS Open Linked Identifiers as needed, verify a real building footprint, and calculate official DEM/LIDAR min/max/mean/max-min statistics.
