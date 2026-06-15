# Distance 047 runner/poller block

page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
status: NOT_FINAL_READY
completion_percent: 92

Observed:
- Active queue exists and is the authoritative task.
- The page automation is present.
- No new smoke report was found after the last successful queue retry.
- The latest queue retry update attempt was blocked before commit.

Blocker:
- The single shared runner has not yet produced product acceptance evidence for Distance 047.

Expected evidence:
- A smoke report proving parcel polygons are returned.
- A status file proving the acceptance status.
- A raw run log proving the automation actually executed.

Future blockers after runner execution:
- Endpoint unavailable.
- Empty parcel FeatureCollection.
- Missing or null six distance metrics.
- Popup or panel schema incomplete.
- Export/schema mismatch.

PowerShell:
- Do not start a separate runner.
- If no evidence appears after the wait window, only diagnose the existing shared runner/poller.
