# London Borough of Lambeth Building Heights — source-area evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-28T02:30:00+03:00

Official source window
- Authority: London Borough of Lambeth
- Service name: LambethBuildingHeights
- Official service directory: https://gis.lambeth.gov.uk/arcgis/rest/services
- FeatureServer: https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBuildingHeights/FeatureServer
- MapServer: https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBuildingHeights/MapServer
- The official ArcGIS REST services directory currently reports server version 11.3 and lists both LambethBuildingHeights FeatureServer and MapServer.
- Lambeth open mapping guidance has previously been captured in the repo as describing free public use where rights permit under the Open Government Licence framework.

Canonical point context
A previously verified runner artifact on the same branch materialized the canonical 92,283-feature Point source from Git blob bb48164e7a0af78df875f30421a6a3068c43edb8 and extracted:
- parcel_61523: longitude -0.1387938, latitude 51.4196454
- parcel_61524: longitude -0.1407703, latitude 51.4170637
- parcel_61525: longitude -0.1398845, latitude 51.4167453

Those points are canonical identities/Point geometries only; they are not parcel polygons and no security-score fields are copied.

Access result
The official directory page itself was readable without login in this execution. Direct opens of both LambethBuildingHeights FeatureServer and MapServer returned HTTP 403 in the current web execution layer. Therefore no building polygon, raw height field, containment result, or feature identifier is invented.

Height Difference implication
The canonical-link blocker is narrowed: real canonical Point geometry exists for the first three partition rows. The next required evidence is an actual official building polygon containing each point (or another documented building-presence rule), followed by official DEM/LIDAR min/max/mean/max-min statistics. No parcel is accepted in this package.
