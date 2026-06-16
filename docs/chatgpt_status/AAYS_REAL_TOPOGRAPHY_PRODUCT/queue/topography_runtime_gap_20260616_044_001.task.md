page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
task_id: topography_runtime_gap_20260616_044_001
automation_script: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_runtime_gap_20260616_044_001.ps1
expected_report: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_chatgpt_runtime_gap_report_20260616_044_001.txt
source_handoff_zip_sha256: 4D3824B633802CE318574BA33B97EED451CB43B69FB2B11A5773F48AAC6D23D3
repo_full_name: cagdascagdas100/chat_gpt_clone_1
branch: aays-runner-v17-icon-work-20260603-232706
local_repo_root: C:\Users\cagda\Documents\GitHub\AAYS
page_root: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT
validation_goal: topography runtime endpoint, tile, source coverage and UI gap report
must_read:
  - docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_final_validation_bundle_20260614_009.txt
  - england_map_web/app.js
  - england_map_web/config/topography.overlay.json
  - terrayield_land_intelligence/app/api/routes/topography_lookup_v2.py
  - terrayield_land_intelligence/app/main.py
runtime_checks:
  - node --check england_map_web/app.js
  - python -m py_compile terrayield_land_intelligence/app/api/routes/topography_lookup_v2.py terrayield_land_intelligence/app/main.py
  - http://127.0.0.1:8010/england_map_web/
  - http://127.0.0.1:8010/topography/lookup?parcel_id=29759443&lat=51.563497&lon=0.293624
  - http://127.0.0.1:8010/topography/tiles/13/4102/2721.png
acceptance_rule: do not mark production complete unless runtime app-open, lookup, tile, popup/panel contract, source coverage and no-fake-data gates pass
no_new_runner: true
db_write: false
migration: false
deploy: false
fake_data: false
