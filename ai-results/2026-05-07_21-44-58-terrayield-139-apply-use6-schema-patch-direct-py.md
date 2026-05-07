# AAYS ChatGPT Runner V4 Result

## Task
Apply use6 schema columns to primary Plan L outputs using direct Python script

## Task ID
terrayield-139-apply-use6-schema-patch-direct-py

## Progress
100%

## Action


## Time
05/07/2026 21:46:39

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
1800

## Exit Code
0

## Output
``text
PROJECT=terrayield
TASK=terrayield-133-apply-use6-schema-patch-direct-py
MODE=apply_use6_columns_to_primary_outputs_with_backups
PLAN_BASE=D:\6 color parcells\plan_l_run01
BACKUP_DIR=D:\6 color parcells\plan_l_run01\output\qa\use6_schema_patch_backup_20260507_214459
PRIMARY_ROWS_BEFORE=34864
COMPAT_ROWS=34864
PRIMARY_FIELDS_BEFORE=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt']
COMPAT_FIELDS=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']
COMPAT_HAS_EXPECTED=PASS
ROW_COUNT_MATCH=PASS
JOIN_KEY=parcel_ref
JOIN_KEY_UNIQUE=PASS
PRIMARY_CSV_BACKUP=D:\6 color parcells\plan_l_run01\output\qa\use6_schema_patch_backup_20260507_214459\london_6color.csv
PRIMARY_ROWS_AFTER=34864
PRIMARY_FIELDS_AFTER=['parcel_ref', 'inspire_id', 'local_authority', 'area_m2', 'recommended_class', 'recommended_use6', 'class6', 'color', 'confidence_score', 'confidence_reason', 'signal_sources', 'signal_detail', 'manual_verified', 'market_excerpt', 'voa_excerpt', 'use6_class', 'use6_color', 'use6_confidence', 'use6_sources']
PRIMARY_HAS_EXPECTED_USE6=PASS
PRIMARY_MISSING_AFTER=[]
GEOJSON_CANDIDATE=D:\6 color parcells\plan_l_run01\output\london_6color.geojson FEATURES=34864 HAS_EXPECTED_BEFORE=False HAS_SOURCE_FIELDS=True
GEOJSON_PATCHED=D:\6 color parcells\plan_l_run01\output\london_6color.geojson
GEOJSON_SEEN=1
GEOJSON_PATCHED_COUNT=1
VALIDATION_SUMMARY
CSV_ROWS_34864=PASS
CSV_USE6_COLUMNS=PASS
NEXT_COMMAND=devam et
TERRAYIELD_133_APPLY_USE6_SCHEMA_PATCH_DONE

``

## Error
``text

``
