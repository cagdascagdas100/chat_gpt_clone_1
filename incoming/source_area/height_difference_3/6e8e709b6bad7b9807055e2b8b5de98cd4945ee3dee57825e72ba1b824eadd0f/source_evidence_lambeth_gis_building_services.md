# Lambeth Council GIS building services — source-area / footprint materialization evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Window: LAMBETH_GIS_BUILDING_SERVICES_DIRECTORY_AND_BOROUGH_EXTENT_20260929:1/1:COMPLETE

Official public/no-login surface
- https://gis.lambeth.gov.uk/arcgis/rest/services
- Live directory version 11.3.
- Building services listed: LambethEstateBuildings (FeatureServer/MapServer) and LambethBuildingHeights (FeatureServer/MapServer).
- The records.geojson Polygon is only the WGS84 transform of the retained official Lambeth Borough Boundary layer extent envelope EPSG:27700 [528518.9928,169648.0893,533716.1259,180688.2655]. It is not a parcel or building footprint.

Canonical evidence already resolved
- parcel_61523 / HMLR 36813904 / UPRN 100021835581 / SW16 5BS; EA DTM min 30.48, max 31.72, mean 31.356, max-min 1.24 m.
- parcel_61524 / HMLR 36818289 / UPRN 100021804719 / SW16 5AF; EA DTM min 25.57, max 30.34, mean 27.553, max-min 4.77 m.
- parcel_61525 / HMLR 36802876 / UPRN 100021819433 / SW16 5BD; EA DTM min 26.94, max 27.43, mean 27.239, max-min 0.49 m.
- Exact HMLR cadastral Polygon geometry is committed for each row.
- EA mean values were accepted only after re-reading committed official GeoTIFF bytes and exactly reproducing prior valid-cell count/min/max/range with the same cell-centre polygon mask.

Fail-closed result
Exact Lambeth building-feature query bodies could not be physically materialized through the available web transport. No building Polygon/MultiPolygon is claimed; accepted_count remains zero.

Next missing criterion
EXACT_BUILDING_FOOTPRINT_FEATURE_GEOMETRY_FOR_CANONICAL_ROWS_61523_61525_THEN_LAYER24_ACCEPTANCE
