# 048 — Security Accuracy Preflight Download Plan

Goal: Build download plan for official data sources without changing active app data.

Outputs:
- planned_downloads.json
- source_health_probe.json
- licence_conditions_summary.md
- data_volume_estimate.json

Rules:
- Prefer bulk downloads over API for national-scale crime data.
- Keep API calls for sampling/validation.
- Respect licences/conditions.
- No active score update yet.
