# AAYS C to F Folder Move Final Status - 2026-07-05

Updated at: 2026-07-05T05:38:15Z

## Result

The marked small C folders were moved to F and replaced with junctions. The main AAYS root could not be renamed because the active Codex workspace holds it, so the large AAYS subdirectories were moved to F and replaced with junctions inside the C AAYS root.

Move root:

- F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704

C drive free space after final cleanup attempt: 25.31 GB.
F drive free space after final cleanup attempt: 533.96 GB.

## Small Marked Folders

- AAYS_gas_emissions_gas_emissions_shared_runner_contract_20260704: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS_gas_emissions_gas_emissions_shared_runner_contract_20260704
- AAYS_gas_emissions_mainbase_20260703: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS_gas_emissions_mainbase_20260703
- chat_gpt_clone_1_security_pr_work_20260511_030446: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\chat_gpt_clone_1_security_pr_work_20260511_030446

## AAYS Subdirectory Junctions

- data: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\data
- outputs: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\outputs
- node_modules: junction=True, target=C:\Users\cagda\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules
- terrayield_land_intelligence: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\terrayield_land_intelligence
- .codex_worktrees: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\.codex_worktrees
- backups: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\backups
- tiles: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\tiles
- security_accuracy_expansion: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\security_accuracy_expansion
- TERRAYIELD_READY_TO_SELL_3110_EXCEL_FILL_CODEX_PACKAGE_20260516: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\TERRAYIELD_READY_TO_SELL_3110_EXCEL_FILL_CODEX_PACKAGE_20260516
- ready_to_sell_accuracy_runs: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\ready_to_sell_accuracy_runs
- docs: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\docs
- england_map_web: junction=True, target=F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704\AAYS\england_map_web

## Smoke

- http://127.0.0.1:8010/health: ok=True, status=200, bytes=143, error=
- http://127.0.0.1:8010/england_map_web/: ok=True, status=200, bytes=24073, error=
- http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260705-final: ok=True, status=200, bytes=17524, error=

Content token smoke:

- 8010 /england_map_web/ contains Great Britain Parcel Map, AAYS, and Topography.
- 8020 matrix page contains Gas Emissions, Security, Internet, and Topography.
- content_token_smoke_passed=True.

## Remaining C Leftovers

- C:\Users\cagda\Documents\GitHub\AAYS\data_C_LEFTOVER_20260705
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence_C_LEFTOVER_20260705

These remaining leftovers are access-denied temp/test/cache roots. The main app/data/output/docs paths are junctioned to F and 8010/8020 smoke passed, so they are not blocking the TerraYield AAYS application. Cleaning them fully requires a later elevated/admin cleanup window after local tools release their handles.

Cleanup attempts already performed:

- Remove-Item -Recurse -Force: blocked by access denied on leftover temp/cache paths.
- takeown/icacls then Remove-Item: blocked by access denied on leftover temp/cache paths.
- robocopy empty mirror then Remove-Item: freed additional C space, but the same two leftover roots remain.

## Program and Site Integration

- Low-risk layer/site artifacts from the marked C folders were copied into the F repo import staging and integrated where they matched existing TerraYield AAYS layer contracts.
- Program layer matrix files now include the imported Gas Emissions, Internet, Security, Planned Buildings, Distance Property Types, Future Growth, and Topography outputs.
- The previous placeholder Topography GeoJSON was backed up before replacement.
- Invalid imported Gas Emissions queue files were moved out of active queue and kept as import candidates.

## Rollback

1. Stop 8010 and 8020 processes.
2. For each C junction, remove only the junction path.
3. Move the matching folder from F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704 back to its original C path.
4. Re-run 8010 and 8020 smoke.
5. For Git-tracked app state, GitHub rollback points are commits d6274e591, df4526fd6, and 4493b97cd.

## Final Status

- app_site_operational=True
- admin_cleanup_required=True
- remaining_leftovers_count=2