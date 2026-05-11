# Connector Spec - Future Growth Layer

## Scope Guard
- layer_name: Future Urban Growth & Value Shift Layer
- calculation_version: future_growth_v1
- disclaimer_required: "Kesin fiyat tahmini değildir"
- confidence_guard: source_url olmayan kayıt high confidence olamaz
- evidence_guard: popup evidence sadece ilgili parsel ile spatial olarak eşleşmiş kayıtları gösterebilir

## Normalized Target Shape
- target_table: future_growth_features
- required_fields: source_key, source_url, feature_type, external_id, idempotency_key, geometry, centroid, geography_level, effective_date, observed_date, raw_payload_ref, mode, confidence_cap_reason
- allowed_modes: live, fixture, stub
- confidence_rule: live kaynak + source_url + parsel-specific spatial match olmadan high confidence üretilemez
- confidence_rule: fixture ve stub kayıtlar production-compatible typed shape taşır ancak high confidence üretmez

---

## Connector Spec - hmlr_price_paid
- source_key: hmlr_price_paid
- source_url: https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads
- mode: fixture
- input_schema:
  - format: typed fixture payload compatible with future_growth_features
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: market_momentum
  - geography_level: address/postcode/transaction
  - confidence_cap_reason: fixture mode and non-parcel-specific transaction geography
- idempotency_key:
  - rule: hmlr_price_paid:external_id:observed_date
- failure_handling:
  - missing_source_url: reject record
  - missing_geometry: disable parcel popup evidence unless typed matcher resolves parcel-specific geometry

---

## Connector Spec - planning_data_api
- source_key: planning_data_api
- source_url: https://www.planning.data.gov.uk/docs
- mode: live
- input_schema:
  - format: typed live REST JSON or GeoJSON payload compatible with future_growth_features
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: planning+policy+constraints
  - geography_level: parcel/area
  - confidence_cap_reason: none only when source_url and parcel-specific spatial match exist
- idempotency_key:
  - rule: planning_data_api:dataset:external_id
- failure_handling:
  - missing_source_url: reject record
  - schema_drift: reject affected dataset and log status

---

## Connector Spec - planning_brownfield
- source_key: planning_brownfield
- source_url: https://www.planning.data.gov.uk/dataset/brownfield-land
- mode: live
- input_schema:
  - format: typed CSV, JSON, or GeoJSON export payload
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: planning_growth
  - geography_level: site/polygon
  - confidence_cap_reason: none only when parcel-specific spatial match exists
- idempotency_key:
  - rule: planning_brownfield:external_id:observed_date
- failure_handling:
  - missing_source_url: reject record
  - missing_geometry: accept as contextual non-popup signal only

---

## Connector Spec - planning_conservation
- source_key: planning_conservation
- source_url: https://www.planning.data.gov.uk/dataset/conservation-area
- mode: live
- input_schema:
  - format: typed CSV, JSON, or GeoJSON export payload
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: planning_constraints
  - geography_level: polygon
  - confidence_cap_reason: incomplete source coverage and constraint layer
- idempotency_key:
  - rule: planning_conservation:external_id:observed_date
- failure_handling:
  - missing_source_url: reject record
  - incomplete_coverage: cap confidence below high

---

## Connector Spec - planning_listed_building
- source_key: planning_listed_building
- source_url: https://www.planning.data.gov.uk/dataset/listed-building
- mode: live
- input_schema:
  - format: typed CSV, JSON, or GeoJSON export payload
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: planning_constraints
  - geography_level: point
  - confidence_cap_reason: point representation may not equal parcel extent
- idempotency_key:
  - rule: planning_listed_building:external_id:observed_date
- failure_handling:
  - missing_source_url: reject record
  - extent_uncertainty: cap confidence unless parcel-specific spatial rule confirms match

---

## Connector Spec - planning_green_belt
- source_key: planning_green_belt
- source_url: https://www.planning.data.gov.uk/dataset/green-belt
- mode: live
- input_schema:
  - format: typed CSV, JSON, or GeoJSON export payload
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: planning_policy
  - geography_level: polygon
  - confidence_cap_reason: policy-area signal; high confidence only for parcel intersection evidence
- idempotency_key:
  - rule: planning_green_belt:external_id:observed_date
- failure_handling:
  - missing_source_url: reject record
  - stale_snapshot: keep previous successful snapshot and cap confidence

---

## Connector Spec - ons_snpp
- source_key: ons_snpp
- source_url: https://www.ons.gov.uk/releases/subnationalpopulationprojections2022based
- mode: fixture
- input_schema:
  - format: typed CSV or spreadsheet release fixture
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: demographic_demand
  - geography_level: local_authority
  - confidence_cap_reason: local authority level and fixture mode; not parcel-specific
- idempotency_key:
  - rule: ons_snpp:local_authority_code:projection_year
- failure_handling:
  - missing_source_url: reject record
  - release_schema_drift: keep previous fixture snapshot and log status

---

## Connector Spec - ons_internal_migration
- source_key: ons_internal_migration
- source_url: https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationprojections/datasets/internalmigrationz5
- mode: fixture
- input_schema:
  - format: typed CSV or spreadsheet release fixture
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: demographic_demand
  - geography_level: local_authority
  - confidence_cap_reason: local authority level and fixture mode; not parcel-specific
- idempotency_key:
  - rule: ons_internal_migration:local_authority_code:projection_year:migration_measure
- failure_handling:
  - missing_source_url: reject record
  - release_schema_drift: keep previous fixture snapshot and log status

---

## Connector Spec - naptan
- source_key: naptan
- source_url: https://www.data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/naptan
- mode: fixture
- input_schema:
  - format: typed CSV or XML fixture
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: transport_infra
  - geography_level: point
  - confidence_cap_reason: fixture mode; parcel impact requires distance/spatial rule
- idempotency_key:
  - rule: naptan:ATCOCode
- failure_handling:
  - missing_source_url: reject record
  - invalid_coordinate: reject row

---

## Connector Spec - bods
- source_key: bods
- source_url: https://www.gov.uk/guidance/find-and-use-bus-open-data
- mode: stub
- input_schema:
  - format: typed placeholder matching future API/route payload
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: transport_infra
  - geography_level: route/stop
  - confidence_cap_reason: stub mode and no live credential/config
- idempotency_key:
  - rule: bods:operator_name:service_code:effective_date
- failure_handling:
  - missing_source_url: reject record
  - live_config_absent: remain stub and cap confidence below high

---

## Connector Spec - national_rail_darwin
- source_key: national_rail_darwin
- source_url: https://www.nationalrail.co.uk/developers/darwin-data-feeds/
- mode: stub
- input_schema:
  - format: typed placeholder matching Darwin feed station/service payload
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: transport_infra
  - geography_level: station/service
  - confidence_cap_reason: stub mode and external marketplace access requirement
- idempotency_key:
  - rule: national_rail_darwin:station_code:service_id:observed_at
- failure_handling:
  - missing_source_url: reject record
  - live_access_absent: remain stub and cap confidence below high

---

## Connector Spec - tfl_ptal
- source_key: tfl_ptal
- source_url: https://tfl.gov.uk/info-for/urban-planning-and-construction/planning-applications/planning-with-webcat?intcmp=25861
- mode: stub
- input_schema:
  - format: typed placeholder for London PTAL grid/export value
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: transport_infra
  - geography_level: london grid
  - confidence_cap_reason: London-only stub mode; no live import path
- idempotency_key:
  - rule: tfl_ptal:grid_id_or_location_id:effective_date
- failure_handling:
  - missing_source_url: reject record
  - outside_london: mark non-applicable and do not create parcel popup evidence

---

## Connector Spec - gias_schools
- source_key: gias_schools
- source_url: https://get-information-schools.service.gov.uk/
- mode: fixture
- input_schema:
  - format: typed CSV download fixture
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: social_amenity
  - geography_level: establishment
  - confidence_cap_reason: fixture mode and non-parcel-specific geocoding dependency
- idempotency_key:
  - rule: gias_schools:URN
- failure_handling:
  - missing_source_url: reject record
  - missing_location: keep contextual signal only, no popup evidence

---

## Connector Spec - nhs_ods_ord
- source_key: nhs_ods_ord
- source_url: https://digital.nhs.uk/developer/api-catalogue/organisation-data-service-ord
- mode: fixture
- input_schema:
  - format: typed API JSON or fixture JSON
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: social_amenity
  - geography_level: organisation/address
  - confidence_cap_reason: fixture mode and geocoding dependency
- idempotency_key:
  - rule: nhs_ods_ord:organisation_code
- failure_handling:
  - missing_source_url: reject record
  - api_unavailable: keep previous successful fixture snapshot

---

## Connector Spec - os_open_greenspace
- source_key: os_open_greenspace
- source_url: https://www.ordnancesurvey.co.uk/products/os-open-greenspace
- mode: fixture
- input_schema:
  - format: typed GeoPackage, Shapefile, or GeoJSON-derived fixture
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: social_amenity
  - geography_level: polygon
  - confidence_cap_reason: fixture mode; parcel relationship requires spatial intersection or distance rule
- idempotency_key:
  - rule: os_open_greenspace:external_id
- failure_handling:
  - missing_source_url: reject record
  - invalid_polygon: reject row and log reason

---

## Connector Spec - ea_flood_zones_cc
- source_key: ea_flood_zones_cc
- source_url: https://www.data.gov.uk/dataset/77931470-ee6b-4f8e-8868-82842aed2e5d/flood-map-for-planning-flood-zones-plus-climate-change
- mode: fixture
- input_schema:
  - format: typed OGC/WFS/WMS/download-derived spatial fixture
  - required_fields: source_key, source_url, external_id, observed_date, mode
- normalized_output_map:
  - feature_type: risk_penalty
  - geography_level: polygon
  - confidence_cap_reason: fixture mode; risk penalty only, not price prediction
- idempotency_key:
  - rule: ea_flood_zones_cc:flood_zone_class:climate_change_scenario:geometry_hash
- failure_handling:
  - missing_source_url: reject record
  - stale_fixture: keep previous snapshot and log warning
