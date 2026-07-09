# Distance Property Types - Problem Resolution Plan 20260709

status=PLAN_APPLIED_REPO_SIDE
final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false

## User-visible problem
The site still shows old/stale progress for Distance to Nearby Property Types because the site panel reads `england_map_web/data/runner_panel/page_status_index.json`, while the new DPT repo-side work was written to queue/status/report/sidecar files.

## Clarification
This is not an internet source shortage. Internet/source collection remains part of the intended pipeline. The current blocker is runner-output/site-panel synchronization.

## Actual chain
internet sources -> source_candidates CSV -> existing F single runner validation -> verified CSV/GeoJSON -> page_status_index/site panel

Current stuck point:
source_candidates CSV exists, but the existing F runner has not yet written real started/completed/runner_output or verified CSV/GeoJSON for the latest source-seed task.

## Applied actions
1. Added F portable runner hotfix script.
2. Added CMD and PS1 launchers for the existing F runner.
3. Added existing F runner start/request marker.
4. Added truthful site-side status JSON under `england_map_web/data/distance_property_types/distance_property_types_site_status.json`.
5. Verified the main panel file still contains stale DPT status: completion 35, old task id, old blockers.

## Next applied strategy
Do not fake verified data. Keep final false. Use the existing F runner only. When the F runner pulls and runs the hotfix launcher, it must:
- process the queued source seed task,
- write started/completed/runner_output,
- populate verified CSV/GeoJSON only with real validated rows,
- refresh page_status_index with non-stale DPT status.

## Site visibility fix requirement
The main site panel currently depends on `england_map_web/data/runner_panel/page_status_index.json`. Until that file is refreshed by runner or a safe patch routine, the visible site will keep showing stale/problem status even though repo-side support files exist.
