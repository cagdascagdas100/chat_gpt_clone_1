# Source Guardrails Added

Status: PARTIAL_READY
Percent: 62
Final ready: false
PowerShell from user: not required

What changed:
- Data source restrictions were added as a GitHub-visible report.
- The task must use existing repo files, existing local C/D/F files, or open free public sources only.
- The task must not use paid, contact-required, invitation-only, or login-required sources.
- The task must not create synthetic geometry or parcel ids.
- If the data is not parcel-level, the report must use one of the explicit data-level labels.

Still blocking:
- runner output not proven
- renderable parcel geometry not proven
- non-empty endpoint feature set not proven
- popup or right panel field evidence not proven
- geometry accuracy not proven

Expected next GitHub evidence:
- status/*runner-status*.json
- status/*heartbeat*.json
- reports/*runner-output*.md
