# Page 7 Codex Issue Resolution Plan

## Goal
Resolve remaining issues found after Codex backend integration without overwriting active runner tasks.

## Current safeguards
- DB write: false
- Production deploy: false
- Fake data: false
- Do not overwrite active current-task while evidence check is active.

## Known issues to resolve
1. UI icon line in england_map_web/app.js is auto-rewritten from planed_buildings.png back to future_growing_prognose.png.
2. Planned structures final Excel/data artifact must be promoted from seed to verified integration dataset.
3. Backend seed adapter/source registry/pilot script/test updates must be checked against real project paths.
4. DB integration must remain dry-run until user approval.
5. Parcel matching requires verified geometry or source boundary before final import.

## Execution plan
1. Wait for active real100v2 evidence check to finish.
2. Do not edit app.js directly unless source-of-truth generator is found.
3. Add or keep a separate planned-structures layer/mode instead of fighting watcher rewrites.
4. Verify seed file paths and source registry wiring.
5. Produce final import checklist: verified rows, missing evidence rows, DB tables, API endpoints, UI status.
6. Queue the next read-only validation task after current active task completes.

## Acceptance gate
READY_WITH_UI_ICON_NONBLOCKING_WARNING unless a source-of-truth icon generator is found and patched.
