# Frontend Layer Spec

## Metadata
- layer_name: Future Urban Growth & Value Shift Layer
- calculation_version: future_growth_v1
- api_contract_version: future_growth_api_v1
- methodology_note: Bu katman kesin fiyat tahmini değildir; planlama, ulaşım, satış, demografi ve sosyal erişim verilerine dayalı gelişim potansiyeli skorudur.
- output_positioning: decision_support_not_price_prediction

## Control
- toggle_id: showFutureGrowth
- label_tr: Gelecek Gelişim
- label_en: Future Growth
- default_visible: false
- depends_on_endpoint: /api/future-growth/layer
- loading_state_text_tr: Gelecek gelişim katmanı yükleniyor
- empty_state_text: No parcel-specific evidence available
- error_state_text_tr: Gelecek gelişim katmanı şu anda yüklenemiyor

## Legend
- color_scale_source: config/future-growth-layer.json
- score_field: future_growth_percent
- numeric_score_required: true
- color_class_required: true
- hex_color_required: true
- note_text: Bu katman kesin fiyat tahmini değildir; planlama, ulaşım, satış, demografi ve sosyal erişim verilerine dayalı gelişim potansiyeli skorudur.
- classes:
  - color_class: strong_growth
    label_tr: Güçlü gelişim potansiyeli
    score_min: 75
    score_max: 100
    hex_color: "#2f9e44"
  - color_class: moderate_growth
    label_tr: Orta gelişim potansiyeli
    score_min: 60
    score_max: 74.9
    hex_color: "#82c91e"
  - color_class: limited_growth
    label_tr: Sınırlı gelişim potansiyeli
    score_min: 45
    score_max: 59.9
    hex_color: "#ffd43b"
  - color_class: constrained_or_uncertain
    label_tr: Kısıtlı veya belirsiz
    score_min: 0
    score_max: 44.9
    hex_color: "#ff922b"

## Hover
- enabled: true
- trigger: parcel_feature_hover
- fields: [parcel_id, future_growth_percent, color_class, confidence_score, confidence_label]
- format_rules:
  - future_growth_percent: one_decimal_0_100
  - confidence_score: integer_0_100
  - never_show_price_prediction: true
- hover_disclaimer_short: Kesin fiyat tahmini değildir

## Click Popup
- enabled: true
- endpoint: /api/future-growth/parcels/{parcelId}
- sections: [score_summary, score_breakdown, top_reasons, evidence_list, warnings, methodology_note]
- score_summary_fields: [score_total, future_growth_percent, confidence_score, confidence_label, color_class, hex_color, calculation_version]
- evidence_rules:
  - requested_parcel_only: true
  - evidence_parcel_id_must_equal_clicked_parcel_id: true
  - exclude_other_parcel_evidence: true
  - empty_state_text: No parcel-specific evidence available
  - source_url_required_for_high_confidence: true
- warning_rules:
  - show_source_url_missing_warning: true
  - show_fixture_stub_confidence_warning: true
  - show_area_level_not_parcel_specific_warning: true
  - when_geography_level_same_local_authority: show_warning=true
  - local_authority_warning_text: Bu veri parsel özelinde değil, bağlı local authority düzeyinde kullanılmıştır.
  - no_parcel_specific_evidence_text: No parcel-specific evidence available
- popup_disclaimer_text: Kesin fiyat tahmini değildir

## Evidence List Rendering
- endpoint: /api/future-growth/parcels/{parcelId}/evidence
- allowed_relation_types: [INTERSECTS_PARCEL, WITHIN_250M, WITHIN_500M, WITHIN_1000M, WITHIN_2000M]
- blocked_relation_types: [SAME_LSOA, SAME_MSOA, SAME_LOCAL_AUTHORITY, CITY_LEVEL_ONLY]
- render_fields: [source_title, source_publisher, source_url, data_date, publication_date, relation_type, distance_m, impact_weight, confidence, display_warning]
- source_link_behavior: open_in_new_tab
- empty_state_text: No parcel-specific evidence available

## Vector Display
- enabled: true
- endpoint: /api/future-growth/local-authorities/{code}/vector
- style: line-color from config/future-growth-layer.json vectorColor
- show_on_zoom_min: 10
- show_on_zoom_max: 14
- arrow_head_enabled: true
- tooltip_fields: [direction_label, strength_score, confidence_score]
- parcel_popup_evidence_allowed: false
- vector_warning_text: Bu yön vektörü local authority düzeyinde bağlam sinyalidir; parsel özelinde kesin etki göstermez.

## Frontend Guards
- calculation_version_must_equal: future_growth_v1
- display_disclaimer_on_legend: true
- display_disclaimer_on_popup: true
- do_not_render_price_prediction_language: true
- require_numeric_score: true
- require_color_class: true
- require_hex_color: true
- do_not_render_high_confidence_when_source_url_missing: true
- do_not_render_other_parcel_evidence: true
- show_no_parcel_specific_evidence_empty_state: true

## Demo UI Payload Expectations
- layer_feature:
    parcel_id: 12345
    future_growth_percent: 52.4
    color_class: limited_growth
    hex_color: "#9fd356"
    confidence_score: 63
    confidence_label: medium
    calculation_version: future_growth_v1
- popup_empty_evidence:
    parcel_id: 12345
    evidence: []
    warnings:
      - No parcel-specific evidence available
      - Bu veri parsel özelinde değil, bağlı local authority düzeyinde kullanılmıştır.
