# AAYS 090 Threshold Policy Pack
Generated: 2026-05-15T02:07:19
TaskId: aays-090-threshold-policy-pack-20260515
Mode: read-only policy pack; no DB writes; no UI patch.

## Verdict distribution carried forward
derived_ai_visual: 99
derived_signal: 19
derived_multi_signal: 2
L4-00001-OTM-16748769 | OTM-16748769 | derived_multi_signal | multi_signal_non_rectangular_candidate | 18.0 | DE21 5AH | Erewash | 675000.0 | 693.18
L4-00002-OTM-17945851 | OTM-17945851 | derived_multi_signal | multi_signal_non_rectangular_candidate | 18.0 | DY10 | Wyre Forest | 1250000.0 | 135.05
L4-00003-OTM-10225397 | OTM-10225397 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | CV21 | Rugby | 90000.0 | 897.8
L4-00005-OTM-10371311 | OTM-10371311 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | B64 | Sandwell | 150000.0 | 734.35
L4-00006-OTM-10541029 | OTM-10541029 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | PE12 7BZ | South Holland | 89950.0 | 700.58
L4-00007-OTM-10693127 | OTM-10693127 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | DH7 | County Durham | 725000.0 | 412.09
L4-00008-OTM-10849824 | OTM-10849824 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | LA18 5BH | Cumberland | 175000.0 | 23736.98
L4-00009-OTM-10854933 | OTM-10854933 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | NE9 6DR | Gateshead | 300000.0 | 1848.51
L4-00010-OTM-10866038 | OTM-10866038 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | DY5 | Dudley | 325000.0 | 29254.68
L4-00011-OTM-10905789 | OTM-10905789 | derived_signal | signal_based_non_rectangular_candidate | 24.0 | LS25 | North Yorkshire | 70000.0 | 23628.78
L4-00004-OTM-10278618 | OTM-10278618 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | RM8 3PA | Barking and Dagenham | 40500.0 | 220.44
L4-00013-OTM-10968251 | OTM-10968251 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | BR2 | Bromley | 18000.0 | 397.83
L4-00091-OTM-13125000 | OTM-13125000 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | W1J | Westminster | 29950000.0 | 1093503.0
L4-00102-OTM-13262366 | OTM-13262366 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | M4 | Hounslow | 1800000.0 | 4414.59
L4-00113-OTM-13405675 | OTM-13405675 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | TN16 | Bromley | 5000.0 | 99.3
L4-00116-OTM-13486283 | OTM-13486283 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | EN4 | Enfield | 3500000.0 | 1264.41
L4-00178-OTM-14105467 | OTM-14105467 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | HA8 | Barnet | 2300000.0 | 2972.48
L4-00230-OTM-14565352 | OTM-14565352 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | SE25 | Croydon | 320000.0 | 449.42
L4-00247-OTM-14648028 | OTM-14648028 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | CR2 | Croydon | 800000.0 | 98.31
L4-00250-OTM-14695987 | OTM-14695987 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | NW7 | Barnet | 3000000.0 | 6027.75
L4-00333-OTM-15166073 | OTM-15166073 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | TW8 0DT | Hounslow | 2500000.0 | 6131.37
L4-00340-OTM-15203552 | OTM-15203552 | derived_ai_visual | visual_hint_assisted_candidate | 28.0 | KT6 | Kingston upon Thames | 1150000.0 | 98.31

## Completeness counts carried forward
missing_postcode: 0
missing_authority: 0
missing_price: 0
missing_area: 0

## Suggested threshold rules carried forward
rule_area_low_review: normalized_area_m2 < 100
rule_area_high_review: normalized_area_m2 > 25000
rule_price_high_review: ask_price > 3000000
rule_geometry_visual_review: geometry_verdict == derived_ai_visual
rule_no_polygon_review: verified_polygon_geojson empty or null

## Proposed review policy v1
policy_accept_candidate: derived_multi_signal rows may be promoted only after external source URL and postcode authority check.
policy_manual_review_required: all derived_ai_visual rows remain manual_review unless georeferenced polygon evidence is present.
policy_area_low_review: normalized_area_m2 < 100 requires manual review.
policy_area_high_review: normalized_area_m2 > 25000 requires manual review.
policy_price_high_review: ask_price > 3000000 requires manual review.
policy_ppm_high_review: price_per_m2 > 5000 requires manual review.
policy_missing_core_fields: missing postcode, authority, price, or area is reject_or_needs_source.
policy_no_polygon: verified_polygon_geojson null/empty cannot be marked verified.

## Implementation backlog
1. Add deterministic risk_label field in downstream scoring.
2. Add acceptance_status enum: accept_candidate, manual_review, needs_source, reject.
3. Build 25-row manual validation truth table from AAYS 088 sample.
4. Re-run threshold audit after truth table labels are added.
5. Only then adjust scoring thresholds.

wide_accuracy_program_percent: 55
AAYS_090_THRESHOLD_POLICY_PACK_DONE=true
