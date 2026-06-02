# AAYS 092 Implementation Readiness Pack
Generated: 2026-05-15T02:31:33
TaskId: aays-092-implementation-readiness-pack-20260515
Mode: read-only implementation readiness; no DB writes; no UI patch.

## Policy pack excerpt
# AAYS 090 Threshold Policy Pack
Generated: 2026-05-15T02:07:34
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

## Validation template excerpt
# AAYS 091 Validation Label Template
Generated: 2026-05-15T02:11:51
TaskId: aays-091-validation-label-template-20260515
SourceCsv: E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv
Mode: read-only label template generation; no DB writes; no UI patch.
source_rows: 120
template_rows: 22
label_csv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-091-validation-label-template-20260515_021151.csv

## Allowed reviewer_label values
accept, downgrade, reject, needs_source, ambiguous

## Allowed issue_type values
none, missing_source, postcode_mismatch, authority_mismatch, geometry_unsupported, area_outlier, price_outlier, ambiguous_candidate, other

## Review instructions
1. Fill reviewer_label for every row.
2. Fill reviewer_confidence as high, medium, or low.
3. Fill evidence_checked with yes/no.
4. Use corrected_verdict only when label is downgrade or reject.
5. Do not change thresholds until all 25 rows are labeled.

## Template preview

validation_case_id verification_id       listing_id   geometry_verdict     geometry_evidence_type                 geome
                                                                                                                  try_u
                                                                                                                  ncert
                                                                                                                  ainty
                                                                                                                  _m   
------------------ ---------------       ----------   ----------------     ----------------------                 -----
VS-001             L4-00001-OTM-16748769 OTM-16748769 derived_multi_signal multi_signal_non_rectangular_candidate 18.0 
VS-002             L4-00002-OTM-17945851 OTM-17945851 derived_multi_signal multi_signal_non_rectangular_candidate 18.0 
VS-003             L4-00003-OTM-10225397 OTM-10225397 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-004             L4-00005-OTM-10371311 OTM-10371311 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-005             L4-00006-OTM-10541029 OTM-10541029 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-006             L4-00007-OTM-10693127 OTM-10693127 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-007             L4-00008-OTM-10849824 OTM-10849824 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-008             L4-00009-OTM-10854933 OTM-10854933 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-009             L4-00010-OTM-10866038 OTM-10866038 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-010             L4-00011-OTM-10905789 OTM-10905789 derived_signal       signal_based_non_rectangular_candidate 24.0 




wide_accuracy_program_percent: 60
AAYS_091_VALIDATION_LABEL_TEMPLATE_DONE=true

## Anomaly audit excerpt
# AAYS 089 Anomaly Threshold Audit
Generated: 2026-05-15T01:57:38
TaskId: aays-089-anomaly-threshold-audit-20260515
Csv: E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv
Mode: read-only anomaly audit; no DB writes; no UI patch.
total_rows: 120

## Completeness counts
missing_postcode: 0
missing_authority: 0
missing_price: 0
missing_area: 0

## Largest area candidates
verification_id | listing_id | verdict | price | area | ppm | postcode | authority | reason
L4-00019-OTM-11488586 | OTM-11488586 | derived_signal | 695000.0 | 509224.42 | 1.364821 | PL5 | Plymouth | Non-rectangular candidate from listing signals; fail-closed keeps it unverified.
L4-01217-OTM-17888180 | OTM-17888180 | derived_ai_visual | 8500000.0 | 310343.09 | 27.389042 | SW1P | Westminster | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01534-OTM-18379773 | OTM-18379773 | derived_ai_visual | 500000.0 | 175528.12 | 2.848546 | DA1 4GP | Bexley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01568-OTM-18447115 | OTM-18447115 | derived_ai_visual | 4000000.0 | 146043.81 | 27.389042 | N16 0UH | Hackney | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00091-OTM-13125000 | OTM-13125000 | derived_ai_visual | 29950000.0 | 1093503.0 | 27.389042 | W1J | Westminster | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01619-OTM-18511608 | OTM-18511608 | derived_ai_visual | 1750000.0 | 63894.17 | 27.38904 | N16 0UH | Hackney | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00017-OTM-11301465 | OTM-11301465 | derived_signal | 180000.0 | 60277.51 | 2.986188 | EX22 6EQ | Torridge | Non-rectangular candidate from listing signals; fail-closed keeps it unverified.
L4-01566-OTM-18447112 | OTM-18447112 | derived_ai_visual | 1250000.0 | 45638.69 | 27.389042 | N16 0UH | Hackney | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00010-OTM-10866038 | OTM-10866038 | derived_signal | 325000.0 | 29254.68 | 11.109334 | DY5 | Dudley | Non-rectangular candidate from listing signals; fail-closed keeps it unverified.
L4-01784-OTM-18691204 | OTM-18691204 | derived_ai_visual | 800000.0 | 29208.76 | 27.389044 | HA0 | Brent | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00465-OTM-16078389 | OTM-16078389 | derived_signal | 82500.0 | 28008.95 | 2.945487 | WC2A 3LH | Camden | Non-rectangular candidate from listing signals; fail-closed keeps it unverified.
L4-01343-OTM-18084236 | OTM-18084236 | derived_ai_visual | 700000.0 | 25557.67 | 27.389038 | HA5 | Harrow | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02275-OTM-19032477 | OTM-19032477 | derived_ai_visual | 700000.0 | 25557.67 | 27.389038 | E11 2DG | Redbridge | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01038-OTM-17651556 | OTM-17651556 | derived_ai_visual | 675000.0 | 24644.89 | 27.389045 | KT1 4ED | Richmond upon Thames | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00008-OTM-10849824 | OTM-10849824 | derived_signal | 175000.0 | 23736.98 | 7.372463 | LA18 5BH | Cumberland | Non-rectangular candidate from listing signals; fail-closed keeps it unverified.

## Smallest area candidates
verification_id | listing_id | verdict | price | area | ppm | postcode | authority | reason
L4-02426-OTM-19088750 | OTM-19088750 | derived_ai_visual | 1000.0 | 13.9 | 71.942446 | CR0 2LP | Croydon | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01660-OTM-18560410 | OTM-18560410 | derived_ai_visual | 525000.0 | 99.3 | 5287.009063 | SW6 | Hammersmith and Fulham | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00113-OTM-13405675 | OTM-13405675 | derived_ai_visual | 5000.0 | 99.3 | 50.352467 | TN16 | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01335-OTM-18066851 | OTM-18066851 | derived_ai_visual | 5000.0 | 11.72 | 426.62116 | DA14 4BE | Bexley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02239-OTM-19002859 | OTM-19002859 | derived_ai_visual | 16500.0 | 15.45 | 1067.961165 | A23 | Lambeth | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01501-OTM-18317780 | OTM-18317780 | derived_ai_visual | 500000.0 | 246.7 | 2026.753141 | N11 | Haringey | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02791-OTM-19230021 | OTM-19230021 | derived_ai_visual | 60000.0 | 27.46 | 2184.996358 | SM5 | Merton | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02347-OTM-19058119 | OTM-19058119 | derived_ai_visual | 500.0 | 32.97 | 15.165302 | BR6 7GZ | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01972-OTM-18845028 | OTM-18845028 | derived_ai_visual | 38000.0 | 49.11 | 773.773162 | N10 | Barnet | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01715-OTM-18629244 | OTM-18629244 | derived_ai_visual | 35000.0 | 49.16 | 711.960944 | CR0 6TG | Croydon | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02945-OTM-19281696 | OTM-19281696 | derived_ai_visual | 60000.0 | 524.3 | 114.438299 | SE27 0HZ | Lambeth | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02372-OTM-19064785 | OTM-19064785 | derived_ai_visual | 90000.0 | 59.58 | 1510.574018 | DA7 6AU | Bexley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02435-OTM-19091340 | OTM-19091340 | derived_ai_visual | 245000.0 | 59.58 | 4112.11816 | SW4 | Lambeth | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00696-OTM-16930731 | OTM-16930731 | derived_ai_visual | 1000000.0 | 63.15 | 15835.312747 | EN5 | Barnet | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01039-OTM-17653723 | OTM-17653723 | derived_ai_visual | 50000.0 | 70.22 | 712.04785 | CR8 | Croydon | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.

## Highest price candidates
verification_id | listing_id | verdict | price | area | ppm | postcode | authority | reason
L4-00091-OTM-13125000 | OTM-13125000 | derived_ai_visual | 29950000.0 | 1093503.0 | 27.389042 | W1J | Westminster | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01217-OTM-17888180 | OTM-17888180 | derived_ai_visual | 8500000.0 | 310343.09 | 27.389042 | SW1P | Westminster | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00555-OTM-16460389 | OTM-16460389 | derived_ai_visual | 5250000.0 | 191682.5 | 27.389042 | W5 3HP | Ealing | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01568-OTM-18447115 | OTM-18447115 | derived_ai_visual | 4000000.0 | 146043.81 | 27.389042 | N16 0UH | Hackney | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00116-OTM-13486283 | OTM-13486283 | derived_ai_visual | 3500000.0 | 1264.41 | 2768.089465 | EN4 | Enfield | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00250-OTM-14695987 | OTM-14695987 | derived_ai_visual | 3000000.0 | 6027.75 | 497.698146 | NW7 | Barnet | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00333-OTM-15166073 | OTM-15166073 | derived_ai_visual | 2500000.0 | 6131.37 | 407.739217 | TW8 0DT | Hounslow | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02850-OTM-19252323 | OTM-19252323 | derived_ai_visual | 2400000.0 | 81.43 | 29473.167137 | CR0 | Croydon | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00178-OTM-14105467 | OTM-14105467 | derived_ai_visual | 2300000.0 | 2972.48 | 773.764668 | HA8 | Barnet | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01732-OTM-18640375 | OTM-18640375 | derived_ai_visual | 2250000.0 | 2812.95 | 799.87202 | DA17 6LY | Bexley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01882-OTM-18774177 | OTM-18774177 | derived_ai_visual | 2000000.0 | 2808.89 | 712.025035 | CR7 6AD | Croydon | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01654-OTM-18555242 | OTM-18555242 | derived_ai_visual | 2000000.0 | 2584.76 | 773.76623 | EN5 | Barnet | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00991-OTM-17567927 | OTM-17567927 | derived_ai_visual | 1999950.0 | 4904.98 | 407.738666 | TW3 3TU | Hounslow | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00102-OTM-13262366 | OTM-13262366 | derived_ai_visual | 1800000.0 | 4414.59 | 407.738884 | M4 | Hounslow | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00391-OTM-15740059 | OTM-15740059 | derived_ai_visual | 1800000.0 | 823.79 | 2185.022882 | SW19 | Merton | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.

## Lowest price candidates
verification_id | listing_id | verdict | price | area | ppm | postcode | authority | reason
L4-02347-OTM-19058119 | OTM-19058119 | derived_ai_visual | 500.0 | 32.97 | 15.165302 | BR6 7GZ | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02426-OTM-19088750 | OTM-19088750 | derived_ai_visual | 1000.0 | 13.9 | 71.942446 | CR0 2LP | Croydon | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00775-OTM-17103484 | OTM-17103484 | derived_ai_visual | 3000.0 | 2046.56 | 1.465874 | BR2 6AR | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02522-OTM-19139156 | OTM-19139156 | derived_ai_visual | 5000.0 | 329.67 | 15.166682 | SE20 7SX | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01335-OTM-18066851 | OTM-18066851 | derived_ai_visual | 5000.0 | 11.72 | 426.62116 | DA14 4BE | Bexley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00113-OTM-13405675 | OTM-13405675 | derived_ai_visual | 5000.0 | 99.3 | 50.352467 | TN16 | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02589-OTM-19167220 | OTM-19167220 | derived_ai_visual | 15000.0 | 159.87 | 93.826234 | BR5 3DT | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-01345-OTM-18087053 | OTM-18087053 | derived_ai_visual | 15000.0 | 121.15 | 123.813454 | TW13 | Hounslow | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02239-OTM-19002859 | OTM-19002859 | derived_ai_visual | 16500.0 | 15.45 | 1067.961165 | A23 | Lambeth | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-02566-OTM-19160820 | OTM-19160820 | derived_ai_visual | 17000.0 | 321.48 | 52.880428 | BR2 | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.
L4-00013-OTM-10968251 | OTM-10968251 | derived_ai_visual | 18000.0 | 397.83 | 45.245457 | BR2 | Bromley | Visual/photo hints exist, but not georeferenced. Candidate remains derived only.

## Implementation spec v1
field_risk_label_values: low, medium, high, critical
field_acceptance_status_values: accept_candidate, manual_review, needs_source, reject
risk_rule_critical_no_polygon: verified_polygon_geojson null/empty -> critical + manual_review or needs_source
risk_rule_high_ai_visual: derived_ai_visual -> high + manual_review
risk_rule_high_price: ask_price > 3000000 -> high + manual_review
risk_rule_high_area: normalized_area_m2 > 25000 -> high + manual_review
risk_rule_high_ppm: price_per_m2 > 5000 -> high + manual_review
risk_rule_low_area: normalized_area_m2 < 100 -> high + manual_review
risk_rule_medium_signal: derived_signal -> medium + manual_review until validation labels exist
risk_rule_medium_multi_signal: derived_multi_signal -> medium + accept_candidate only if source evidence is checked

## Test plan v1
test_1: no missing core fields should pass completeness audit.
test_2: all derived_ai_visual rows produce high/manual_review.
test_3: no polygon rows cannot be marked verified.
test_4: high area/price/ppm rows are surfaced in review queue.
test_5: validation label CSV accepted values only.

## Next gates
gate_6_implementation_spec: done
gate_7_code_patch_or_config_patch: next
gate_8_unit_tests: next_after_patch
wide_accuracy_program_percent: 65
AAYS_092_IMPLEMENTATION_READINESS_PACK_DONE=true
