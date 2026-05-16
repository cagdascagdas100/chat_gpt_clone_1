# ChatGPT Review Index - Source Lineage / Parcel 477

Generated UTC: 2026-05-16T21:02:47.5560142Z

## Purpose
GitHub-visible handoff folder for source lineage, Parcel 477, and high-confidence guard review.

## Current finding
- source_url olmayan kayıt high confidence olmamalı.
- Parcel 477 has geometry evidence but missing source_url/source file lineage.
- Main implementation candidate: app/etl/match/parcel_matcher.py.
- Confidence guard files: app/quality/source_confidence_integration.py and app/quality/source_confidence_rules.py.

## Key files
- MANIFEST.csv
- MISSING_FILES.md
- SECRET_SCAN_SUMMARY.txt
- GIT_STATUS.txt
- GIT_DIFF_CURRENT.patch
- GIT_DIFF_CHECK.txt
- evidence/
- source_snapshot/

## Safety
- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false

## Commit policy
This step commits only docs/chatgpt_handoff/github_visible_source_lineage_20260516.
Application source files are snapshotted here only.
Final movement into application folders happens after review.
