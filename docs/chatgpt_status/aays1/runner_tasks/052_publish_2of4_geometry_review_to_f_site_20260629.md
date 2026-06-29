# 052 — Publish 2/4 Geometry Review To F Site

TASK_ID=terrayield-052-publish-2of4-geometry-review-to-f-site-20260629
PAGE_KEY=aays1
REPO_FULL_NAME=cagdascagdas100/chat_gpt_clone_1
BRANCH=main
ACTIVE_LOCAL_REPO=F:\chatgpt\chat_gpt_clone_1_main
ACTIVE_BRIDGE_ROOT=F:\AAYS_GITHUB_BRIDGE_CLEAN2
LEGACY_SOURCE_ROOT=C:\Users\cagda\Documents\GitHub\AAYS

## Goal

Run the existing Codex-created 2/4 geometry review publish package from the legacy AAYS output folder and publish the review page into the active F repo/site.

## Required local source files

- C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\geometry_review_2of4_20260629\TerraYield_2OF4_Geometry_Review_Queue_20260629.html
- C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\geometry_review_2of4_20260629\TerraYield_2OF4_Geometry_Review_Queue_20260629.csv
- C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\geometry_review_2of4_20260629\CHATGPT_2OF4_GEOMETRY_REVIEW_MASTER_PROMPT_TR.txt
- C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\geometry_review_2of4_20260629\RUN_PUBLISH_TO_F_SITE_TR.ps1
- C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\publish_2of4_geometry_review_to_f_site.py

## Expected output

- F:\chatgpt\chat_gpt_clone_1_main\england_map_web\geometry_review_2of4_20260629.html
- http://127.0.0.1:8010/england_map_web/geometry_review_2of4_20260629.html
- docs/chatgpt_status/aays1/reports/052_publish_2of4_geometry_review_to_f_site_<timestamp>.md
- docs/chatgpt_status/aays1/status/052_publish_2of4_geometry_review_to_f_site_<timestamp>.json
- docs/chatgpt_status/aays1/runner_outputs/geometry_review_2of4_20260629/*

## Safety / non-goals

- DB write yok.
- DDL yok.
- Migration yok.
- Production deploy yok.
- Fake polygon yok.
- Bu görev 1264 kaydın kanıt incelemesini tamamlamaz; sadece 2/4 review mekanizmasını F siteye yayımlar ve GitHub main'e gerçek output/status/report yollarını yazar.
- 3/4 veya 4/4 yükseltme yapılmaz.

## Acceptance criteria

1. Existing shared runner picks queue JSON under docs/chatgpt_status/aays1/queue.
2. Automation script runs from docs/chatgpt_status/aays1/automation/052_publish_2of4_geometry_review_to_f_site_20260629.ps1.
3. Script validates legacy source files before publishing.
4. Script publishes/copies review HTML to F active site.
5. Script commits and pushes generated report/status/output artifacts to GitHub main.
6. If any required local file is missing, status is BLOCKED_* with exact missing path; no fake success is written.

## User instruction source

Codex reported 1264 records with 2/4 accuracy and created a separate review mechanism. F disk direct publish failed because of Codex usage/permission limits. The user asked ChatGPT to continue by using the automatic command/runner system and to let the user continue with only `devam et` after this.
