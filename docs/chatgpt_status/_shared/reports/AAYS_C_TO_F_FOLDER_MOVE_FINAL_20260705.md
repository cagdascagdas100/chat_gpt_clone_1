# AAYS C to F Folder Move Final Status - 2026-07-05

Updated at: 2026-07-04T23:48:22Z

## Result

The marked small C folders were moved to F and replaced with junctions. The main AAYS root could not be renamed because the active Codex workspace holds it, so the large AAYS subdirectories were moved to F and replaced with junctions inside the C AAYS root.

Move root:

- F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704

C drive free space after cleanup: 22.37 GB.
F drive free space after cleanup: 534.09 GB.

## Junctions

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

- http://127.0.0.1:8010/health: ok=True, status=200, error=
- http://127.0.0.1:8010/england_map_web/: ok=True, status=200, error=
- http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=final-c-to-f: ok=True, status=200, error=

## Remaining C Leftovers

- data_C_LEFTOVER_20260705
- terrayield_land_intelligence_C_LEFTOVER_20260705

The remaining leftovers are access-denied temp/test/cache leftovers. Main app/data/output/docs paths are junctioned to F and smoke passed.

## Rollback

1. Stop 8010 and 8020 processes.
2. For each C junction, remove only the junction path.
3. Move the matching folder from F:\chatgpt\C_DRIVE_GITHUB_MOVED_20260704 back to its original C path.
4. Re-run 8010 and 8020 smoke.
5. For Git-tracked app state, GitHub rollback point is available via commits d6274e591 and df4526fd6.
## Final Content Token Smoke

- 8010 /england_map_web/ contains Great Britain Parcel Map and AAYS.
- 8020 matrix page contains Gas Emissions, Security, Internet, and Topography.
- content_token_smoke_passed=true.
