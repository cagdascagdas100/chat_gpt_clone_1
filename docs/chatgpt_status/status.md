# ChatGPT Multi Page Status

Updated: 2026-05-21 00:25:00

| Page | Active task | Status | Overall progress | Wait minutes | Next command | Runner status | Blocker | DB write | Production deploy | Updated at |
|---|---|---:|---:|---:|---|---|---|---:|---:|---|
| 1.3 Ready to Sell | terrayield-cost-engine-055-integration-fix-plan-20260520 | running | 76 | 30-35 | devam et | queued | Cost Engine 054 completed with 14 failed matrix cases; 055 integration/fix plan queued. | false | false | 2026-05-20 22:10:00 |
| 3.2 Parcel Label | parcel-use6-runner-status-poll-20260520 | polling | 45 | 30-45 | devam et | polling |  | false | false | 2026-05-20 23:07:12 |
| 4.1 Topgraphy | AAYS 112-114 DEM blocker summary | blocked | 99 | 0 | devam et | finished | Usable local terrain raster is missing. Add DEM or DTM before rerunning elevation sampling. | false | false | 2026-05-21 00:10:00 |
| 6.1 Security | auto-6-security-dashboard-visibility-sync | polling | 94 | 35-45 | devam et | polling |  | false | false | 2026-05-21 00:25:00 |
| 7 Planlanan Yapılar | ty154-nsip-detail-dco-boundary-harvest | waiting | 65 | 30-40 | devam et | polling | Runner has not yet written TY154 heartbeat/result after queue update. | false | false | 2026-05-21 00:02:00 |
| 8.1 Gelisim | terrayield-cost-engine-055-integration-fix-plan-20260520 | blocked | 75 | 10-15 | devam et | stale | terrayield_cost_engine_055_integration_fix_plan_20260520.ps1 missing in repo; waiting for bridge/run recovery | false | false | 2026-05-20 23:55:00 |
| 9.1 Contractor | contractor-005-official-data-acquisition-plan-20260520 | running | 65 | 35-40 | devam et | finished |  | false | false | 2026-05-20 23:58:00 |
| 10.1 Emlakci | estate-002006-pending | waiting | 68 | 5-10 | devam et | finished | estate pending queued; result not confirmed | false | false | 2026-05-21 00:16:00 |
| 12 Cost | terrayield-cost-engine-055-integration-fix-plan-20260520 | finished | 76 | 0-2 | devam et | finished |  | false | false | 2026-05-21 00:00:00 |
| 13 Internet | terrayield-047-internet-access-score10-chatgpt-first-orchestrator | polling | 35 | 10-20 | devam et | waiting_heartbeat | External data drive and source lineage not yet confirmed; DB write and production deploy disabled. | false | false | 2026-05-21 00:12:00 |

Rules:
- Keep DB write disabled.
- Keep production deploy disabled.
- Each ChatGPT page updates only its own key in docs/chatgpt_status/multi_page_status.json.
