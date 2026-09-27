# Planning Data Title boundary — source-area/identifier evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-27T20:35:00+03:00

Official/public dataset
- Service: Planning Data, Ministry of Housing, Communities and Local Government
- Dataset: Title boundary
- Dataset slug: title-boundary
- Data provider shown by the dataset: HM Land Registry
- Total observed on dataset page: 22,740,586 title-boundary entities
- Collector last ran: 7 September 2026
- New data last found: 7 September 2026
- Licence: Open Government Licence v3.0
- Attribution: HM Land Registry plus Ordnance Survey geometry attribution stated on the service
- Dataset URL: https://www.planning.data.gov.uk/dataset/title-boundary

Entity semantics
- Public entity records use dataset/title prefix title-boundary and expose entity and reference identifiers.
- Public entity records expose MULTIPOLYGON geometry and a representative POINT.
- Current records can carry quality=authoritative and organisation-curie government-organisation:D69 for HM Land Registry.
- Individual entity pages offer JSON and GeoJSON representations/downloads.

Provenance caveat
The dataset page also says its origin contains some data created by MHCLG and that the service is working to replace this with data from authoritative sources. This package retains that caveat and does not silently treat every entity as equally authoritative.

Scope decision
This national polygon source removes the need to preselect an HMLR local-authority GML file, but it does not solve the internal canonical-link problem by itself. The canonical partition rows 61523–92283 are not exposed here with geometry or a Planning Data title-boundary reference. Selecting arbitrary title-boundary entities would invent scope.

Height Difference next step
Local OpenCode needs canonical partition geometry or a trusted linking identifier. It can then select/intersect Planning Data/HMLR title-boundary polygons, intersect official building footprints, retain building-present canonical parcels, and calculate official DEM/LIDAR min/max/mean/max-min statistics.
