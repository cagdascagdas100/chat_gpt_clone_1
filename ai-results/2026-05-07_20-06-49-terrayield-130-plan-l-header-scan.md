# AAYS ChatGPT Runner V4 Result

## Task
Run Plan L read-only CSV and GeoJSON header scan

## Task ID
terrayield-130-plan-l-header-scan

## Progress
100%

## Action


## Time
05/07/2026 20:08:24

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
1800

## Exit Code
0

## Output
``text
PROJECT=terrayield
TASK=terrayield-130-plan-l-header-scan
MODE=read_only_csv_geojson_header_scan
PLAN_BASE=D:\6 color parcells\plan_l_run01
PLAN_BASE_EXISTS=PASS

=== CSV HEADERS SCAN ===

CSV_FILE=D:\6 color parcells\plan_l_run01\output\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\plan_l_use6_compatibility.csv
CSV_ROWS=34864
HEADER_COUNT=19
HAS_ALL_EXPECTED_USE6=PASS
MISSING_EXPECTED=[]
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\plan_l_use6_compatibility.csv
CSV_ROWS=34864
HEADER_COUNT=19
HAS_ALL_EXPECTED_USE6=PASS
MISSING_EXPECTED=[]
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\output\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\london_6color.csv
CSV_ROWS=34864
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\london_6color_confidence_summary.csv
CSV_ROWS=1
HEADER_COUNT=3
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence_score']
FIRST_40_COLUMNS=['confidence_score', 'parcel_count', 'percent']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\london_6color_summary.csv
CSV_ROWS=5
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class6', 'color', 'avg_confidence']
FIRST_40_COLUMNS=['class6', 'color', 'parcel_count', 'percent', 'area_m2_sum', 'avg_confidence']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\plan_l_use6_compatibility.csv
CSV_ROWS=34864
HEADER_COUNT=19
HAS_ALL_EXPECTED_USE6=PASS
MISSING_EXPECTED=[]
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_area_by_class_summary.csv
CSV_ROWS=1
HEADER_COUNT=5
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count', 'area_known', 'area_sum_m2', 'mean_area_m2']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_class_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['class', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_confidence_counts_recomputed.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['confidence']
FIRST_40_COLUMNS=['confidence', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_key_coverage.csv
CSV_ROWS=6
HEADER_COUNT=6
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source']
FIRST_40_COLUMNS=['source', 'key', 'rows', 'nonempty', 'share_nonempty', 'unique_nonempty']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_keyword_hit_matrix.csv
CSV_ROWS=10
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source', 'class']
FIRST_40_COLUMNS=['source', 'class', 'keyword_row_hits', 'examples']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_local_authority_class_summary.csv
CSV_ROWS=4
HEADER_COUNT=4
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['class']
FIRST_40_COLUMNS=['local_authority', 'class', 'count', 'share']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_low_confidence_sample.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_source_counts.csv
CSV_ROWS=1
HEADER_COUNT=2
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['source_signature']
FIRST_40_COLUMNS=['source_signature', 'count']

CSV_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\qa_all\qa_suspicious_karma_rows.csv
CSV_ROWS=0
HEADER_COUNT=15
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_COLUMNS=['recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_COLUMNS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']

=== GEOJSON PROPERTY SCAN ===

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133910\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_133911\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142708\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\manifest_accept_20260507_142712\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132557\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163642\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_163643\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164820\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_164822\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_170928\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_173731\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_174646\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_200245\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\input\london_parcels_geometry.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method']

GEOJSON_FILE=D:\6 color parcells\plan_l_run01\output\london_6color.geojson
FEATURES=34864
HAS_ALL_EXPECTED_USE6=FAIL
MISSING_EXPECTED=['use6_sources', 'use6_class', 'use6_color', 'use6_confidence']
MATCHED_PROPS=['recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources']
FIRST_40_PROPS=['parcel_id', 'parcel_ref', 'local_authority', 'area_m2', 'geometry_type', 'center_lon', 'center_lat', 'geometry_bbox', 'recommended_use6', 'recommended_class', 'recommended_color', 'confidence_level_1_4', 'confidence_name_tr', 'parcel_meaning_tr', 'evidence_fields', 'upgrade_action_tr', 'source_api_endpoint', 'source_method', 'class6', 'class6_color', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified']

NEXT_COMMAND=devam et
TERRAYIELD_130_PLAN_L_HEADER_SCAN_DONE

``

## Error
``text

``
