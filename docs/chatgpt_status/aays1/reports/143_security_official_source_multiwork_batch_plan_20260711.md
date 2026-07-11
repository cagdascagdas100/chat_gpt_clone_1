# AAYS1 Security / Public Safety — Official-Source Multiwork Batch Plan

Date: 2026-07-11
Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `codex/aays-single-runner-v5-20260706`
Page key: `aays1`
Canonical runner: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`

## Operating contract

Use only the existing F portable single runner. Do not start a new or parallel runner. Execute the work as one long sequential batch. Keep `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false`.

## Official internet sources prepared for the runner

1. Police API documentation: `https://data.police.uk/docs/`
2. Official Police data downloads: `https://data.police.uk/data/`
3. ONS Open Geography Portal: `https://geoportal.statistics.gov.uk/`

The official Police download page provides force-level street crime and outcome CSV data broken down by 2021 LSOA. The page currently exposes data through May 2026. Use the newest downloadable month that is actually returned by the official source at execution time; record the exact source date and checksum.

## Single-runner long-batch execution plan

1. Finish task 142 row-evidence visibility correction for the existing 150 verified records.
2. Run Chrome/Selenium proof: GeoJSON count, old/new row badges, clickable source/artifact links, pagination, filters, and zero console errors.
3. Resume the existing `aays1-137-next-batch-source-fetch-20260710` work without creating a duplicate task.
4. Fetch official data from `data.police.uk` for several force/geography candidates in one batch. Determine eligible forces from real parcel/LSOA intersections; do not assume coverage.
5. Preserve the existing Security score formula. Accept only records with official source evidence, exact source date, valid LSOA identifier, reproducible spatial match, and complete calculation explanation.
6. Require `accuracy_score_4=4` for automatic publication. Lower-confidence candidates remain excluded or `needs_manual_review=true`; they must not inflate verified totals.
7. Update the verified CSV, GeoJSON, evidence manifest, visible rows/status JSON, and `outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json` atomically.
8. Make every newly verified record visible row-by-row on the website with source URL, source date, source path, evidence path, report path, matching method, calculation explanation, confidence, spatial score, and batch ID.
9. Run browser smoke again after expansion and push all real outputs to GitHub.

## High-accuracy gate

A row may be counted as newly verified only when all conditions pass:

- official/open source URL is preserved;
- source file checksum and source date are recorded;
- LSOA code is valid and present in the official source;
- parcel-to-LSOA match is reproducible and uses the existing verified matching method;
- `accuracy_score_4=4`;
- `needs_manual_review=false`;
- CSV and GeoJSON counts agree;
- evidence manifest entry exists;
- site-visible row exists;
- browser proof confirms the row and its evidence links;
- Git push and remote readback pass.

## Output expectations

- Task 142 runner output: `docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json`
- Browser proof: `docs/chatgpt_status/_shared/reports/security_row_evidence_browser_validation_20260711.json`
- Follow-on source expansion output: use the existing task 137 output contract.
- Site-visible changes: `outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json`

No progress percentage, verified-row count, or final status may increase without real GitHub outputs and browser-visible evidence.
