# Distance Property Types - Veri Sozlesmesi

## CSV kolonlari

parcel_id, selected_property_type, selected_color_category, nearest_industrial_unit_distance_m, nearest_detached_home_distance_m, nearest_retail_property_distance_m, nearest_apartment_building_distance_m, nearest_office_building_distance_m, nearest_mixed_building_distance_m, selected_match_distance_m, official_source_evidence, web_source_evidence, map_source_evidence, photo_ai_evidence, photo_ai_image_path, photo_ai_model_or_tool, photo_ai_observation, source_date, matching_method, conflict_status, needs_manual_review, accuracy_score_4, accuracy_label_4, explanation, last_updated, changed_in_latest_run, change_reason.

## GeoJSON feature properties

CSV kolonlari GeoJSON properties alaninda aynen bulunmali.

Ek zorunlu alanlar:

- type=FeatureCollection
- features[].type=Feature
- features[].geometry
- features[].properties.parcel_id
- features[].properties.selected_property_type
- features[].properties.accuracy_score_4

## Kategori ve renkler

- Industrial Unit = #7c2d12
- Detached Home = #16a34a
- Retail Property = #f97316
- Apartment Building = #2563eb
- Office Building = #7c3aed
- Mixed Building = #db2777
- Unknown / Manual Review = #6b7280

## Batch raporu

Her batch raporu page_key, task_id, run timestamps, row counters, output paths, safety flags, remaining blockers, and next_batch alanlarini icermeli.
