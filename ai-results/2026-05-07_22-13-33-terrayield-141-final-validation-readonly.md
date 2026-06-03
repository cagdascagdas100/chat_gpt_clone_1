# AAYS ChatGPT Runner V4 Result

## Task
Read-only final validation after use6 patch

## Task ID
terrayield-141-final-validation-readonly

## Progress
100%

## Action


## Time
05/07/2026 22:13:59

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
900

## Exit Code
0

## Output
``text
PROJECT=terrayield
TASK=terrayield-141-final-validation-readonly
MODE=read_only_final_validation_after_use6_patch
PLAN_BASE=D:\6 color parcells\plan_l_run01
PLAN_BASE_EXISTS=True
--- CSV HEADER VALIDATION ---
CSV_EXISTS=PASS
CSV_FILE=D:\6 color parcells\plan_l_run01\output\london_6color.csv
CSV_HEADER_COUNT=19
CSV_HAS_use6_class=True
CSV_HAS_use6_color=True
CSV_HAS_use6_confidence=True
CSV_HAS_use6_sources=True
CSV_ROWS=34864
CSV_ROWS_34864=True
--- GEOJSON PROPERTY VALIDATION ---
GEOJSON_EXISTS=PASS
GEOJSON_FILE=D:\6 color parcells\plan_l_run01\output\london_6color.geojson
GEOJSON_FEATURES=34864
GEOJSON_FEATURES_34864=True
GEOJSON_HAS_use6_class=True
GEOJSON_HAS_use6_color=True
GEOJSON_HAS_use6_confidence=True
GEOJSON_HAS_use6_sources=True
--- QA REPORT VALIDATION ---
QA_REPORT_EXISTS=PASS
QA_REPORT=D:\6 color parcells\plan_l_run01\output\qa\PLAN_L_DEEP_QA_REPORT.md
QA_WARNINGS_NONE=True
QA_MISSING_EXPECTED_COLUMNS_PRESENT=False
QA_REPORT_HEAD_BEGIN
# Plan L Deep QA Report

Generated: 2026-05-07T18:58:22.403856Z

## Counts
- classified_rows: 34864
- market_rows: 3110
- voa_rows: 334617
- geojson_features: 34864

## Class counts
- Apartman: 6425
- Müstakil: 26300
- Ofis: 634
- Perakende: 747
- Sanayi: 758

## Confidence counts
- 3: 34864

## Warnings
- none

NEXT_COMMAND=devam et
QA_REPORT_HEAD_END
--- FINAL PACKAGE VALIDATION ---
FINAL_PACKAGE_DIR=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_215755
FINAL_PACKAGE_DIR_EXISTS=True
FINAL_PACKAGE_ZIP=
FINAL_PACKAGE_ZIP_EXISTS=False
--- OVERALL ---
EXPECTED_OUTCOME=CSV_AND_GEOJSON_HAVE_USE6_COLUMNS_AND_QA_WARNINGS_NONE
NEXT_COMMAND=devam et
TERRAYIELD_141_FINAL_VALIDATION_READONLY_DONE

``

## Error
``text

``
