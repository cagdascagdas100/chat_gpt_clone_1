# Nearby Planned Developments data contract

Layer: Nearby Planned Developments
Page key: AAYS_REAL_TOPOGRAPHY_PRODUCT
Branch: aays-runner-v17-icon-work-20260603-232706

This is an import-ready contract, not sample data. Do not create fake parcel features.

Accepted runtime data inputs:
- TYLI_PLANNED_ASSETS_GEOJSON
- AAYS_PLANNED_ASSETS_GEOJSON
- PLANNED_ASSETS_PARCEL_LAYER_GEOJSON
- england_map_web/data/planned_assets_parcel_layer.geojson
- england_map_web/data/planned_buildings_parcel_layer.geojson
- terrayield_land_intelligence/data/planned_assets_parcel_layer.geojson
- F:\chatgpt\AAYS_RUNTIME\planned_buildings\sample_data\planned_assets_parcel_layer.geojson
- F:\chatgpt\AAYS_DATA\planned_assets_parcel_layer.geojson
- D:\AAYS_DATA\planned_assets_parcel_layer.geojson

Required GeoJSON shape:
- type: FeatureCollection
- features: non-empty list of GeoJSON Feature objects
- each feature represents a matched parcel only
- unmatched parcels must not be included

Required properties for acceptance:
- parcel_id
- planned_asset_count
- planned_building_1_value
- planned_building_1_probability
- planned_building_1_completion_month
- source_name
- source_date
- match_confidence_score
- relation_type
- calculation_explanation

Final acceptance must remain false when no verified FeatureCollection is found.
