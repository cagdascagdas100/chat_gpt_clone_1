# Cost50 023 Safe Cleanup Audit Inventory

Generated: 2026-05-12T21:54:19

TASK=cost50-023-safe-cleanup-audit-inventory-20260512
MODE=inventory_only_no_delete
DELETE_EXECUTED=False
PROTECTED_TOUCH_COUNT=0
PROTECTED_SCOPES=
DB files / PostgreSQL data; source manifests; quality_reports; handoff zip files; application source files under project root
ACTIVE_RUNNER_LOG_EXCLUDED=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_214003.log
AI_TMP_OLD_COUNT=0
RUNNER_LOG_OLD_COUNT=94
TIMESTAMP_RESULT_COPY_OLD_COUNT=385
CANDIDATE_TOTAL_COUNT=479
CANDIDATE_TOTAL_BYTES=16939234
RECOMMENDATION=Review this inventory first; if safe, run a delete-only-temp-log task. Do not delete DB/source manifests/quality_reports/handoff zips/app source.
PLAN_PROGRESS_PERCENT=45
TASK_COMPLETION=100/100

## Candidate inventory preview

| Bucket | Relative path | Bytes | LastWriteTime | AgeMinutes |
|---|---:|---:|---:|---:|
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\autopilot-v5-20260511_182504.log | 4159 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\autopilot-v5-20260511_184300.log | 12168 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j232.20260511_135303.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j232.20260511_135303.log | 26702 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j234.20260511_143501.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j234.20260511_143501.log | 1244 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j234.20260511_153832.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j234.20260511_153832.log | 1244 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j236.20260511_161140.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j236.20260511_161202.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j236.20260511_161140.log | 26704 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\j236.20260511_161202.log | 26704 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-203-final-pack.20260511_031822.err.log | 2560 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-203-final-pack.20260511_031822.log | 3408 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-203-final-pack.20260511_032604.err.log | 2560 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-203-final-pack.20260511_032604.log | 3408 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-206-zip-repair.20260511_040231.log | 1300 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-206-zip-repair.20260511_040231.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-206-zip-repair.20260511_040727.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-206-zip-repair.20260511_040727.log | 1300 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-208-final-verifier.20260511_041708.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-208-final-verifier.20260511_042119.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-208-final-verifier.20260511_041708.log | 1244 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\job-208-final-verifier.20260511_042119.log | 1244 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\runner-v4-20260511_143809.log | 42015 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\runner-v4-20260510_174900.log | 220613 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\runner-v4-20260511_142631.log | 45585 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\runner-v4-20260510_215411.log | 27183 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\runner-v4-20260511_153927.log | 21925 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\runner-v4-20260511_160531.log | 12965 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\terrayield-047-bridge-contractor-bootstrap-probe.20260511_164937.log | 21558 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\terrayield-047-bridge-contractor-bootstrap-probe.20260511_164937.err.log | 0 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\user-mode-watchdog.log | 55347 | 2026-05-11T23:25:29 | 1348.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260511_232532.log | 38652 | 2026-05-11T23:37:44 | 1336.6 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-004-db-config-smoke-audit-20260512-stdout.log | 2180 | 2026-05-12T00:24:06 | 1290.2 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-004-db-config-smoke-audit-20260512-stderr.log | 5 | 2026-05-12T00:24:06 | 1290.2 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_002400.log | 35949 | 2026-05-12T00:33:00 | 1281.3 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_003644.log | 111890 | 2026-05-12T01:11:33 | 1242.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_011154.log | 54220 | 2026-05-12T01:28:17 | 1226 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-006-schema-migration-draft-audit-20260512-stdout.log | 1545 | 2026-05-12T02:08:45 | 1185.6 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-006-schema-migration-draft-audit-20260512-stderr.log | 5 | 2026-05-12T02:08:45 | 1185.6 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_020835.log | 5793 | 2026-05-12T02:10:18 | 1184 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_021125.log | 1497 | 2026-05-12T02:11:27 | 1182.9 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_021313.log | 20852 | 2026-05-12T02:20:02 | 1174.3 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_022125.log | 85 | 2026-05-12T02:21:25 | 1172.9 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-008-route-contract-audit-20260512-stdout.log | 2306 | 2026-05-12T02:28:55 | 1165.4 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-008-route-contract-audit-20260512-stderr.log | 5 | 2026-05-12T02:28:55 | 1165.4 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_022626.log | 33392 | 2026-05-12T02:34:07 | 1160.2 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-009-route-stub-gap-audit-20260512-stdout.log | 1469 | 2026-05-12T02:39:29 | 1154.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-009-route-stub-gap-audit-20260512-stderr.log | 5 | 2026-05-12T02:39:29 | 1154.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_023626.log | 30428 | 2026-05-12T02:44:14 | 1150.1 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_023931.log | 18295 | 2026-05-12T02:44:24 | 1149.9 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-010-route-patch-plan-audit-20260512-stderr.log | 5 | 2026-05-12T02:45:47 | 1148.5 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-010-route-patch-plan-audit-20260512-stdout.log | 1451 | 2026-05-12T02:45:47 | 1148.5 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_024546.log | 897575 | 2026-05-12T07:11:33 | 882.8 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_041000.log | 604791 | 2026-05-12T07:12:09 | 882.2 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_042139.log | 563990 | 2026-05-12T07:12:24 | 881.9 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_111127.log | 104851 | 2026-05-12T11:40:56 | 613.4 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-012-packaging-readiness-audit-20260512-stdout.log | 1159 | 2026-05-12T12:20:59 | 573.3 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-012-packaging-readiness-audit-20260512-stderr.log | 5 | 2026-05-12T12:20:59 | 573.3 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-013-artifact-manifest-audit-20260512-stdout.log | 5 | 2026-05-12T13:23:15 | 511.1 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-013-artifact-manifest-audit-20260512-stderr.log | 189 | 2026-05-12T13:23:15 | 511.1 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-013b-artifact-manifest-audit-retry-20260512-stdout.log | 2671 | 2026-05-12T13:28:16 | 506 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-013b-artifact-manifest-audit-retry-20260512-stderr.log | 5 | 2026-05-12T13:28:16 | 506 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-014-report-index-20260512-stdout.log | 2166 | 2026-05-12T13:52:36 | 481.7 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-014-report-index-20260512-stderr.log | 5 | 2026-05-12T13:52:36 | 481.7 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-014b-report-index-20260512-stdout.log | 2166 | 2026-05-12T13:54:54 | 479.4 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-014b-report-index-20260512-stderr.log | 5 | 2026-05-12T13:54:54 | 479.4 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-015-handoff-closure-audit-20260512-stdout.log | 1710 | 2026-05-12T14:14:53 | 459.4 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-015-handoff-closure-audit-20260512-stderr.log | 5 | 2026-05-12T14:14:53 | 459.4 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-016b-source-outputs-materialize-20260512-stdout.log | 1044 | 2026-05-12T14:23:25 | 450.9 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\cost50-016b-source-outputs-materialize-20260512-stderr.log | 5 | 2026-05-12T14:23:25 | 450.9 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_130501.log | 244315 | 2026-05-12T14:25:40 | 448.6 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_132113.log | 201973 | 2026-05-12T14:25:41 | 448.6 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_134958.log | 124430 | 2026-05-12T14:25:47 | 448.5 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_141501.log | 34224 | 2026-05-12T14:25:47 | 448.5 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_114257.log | 484775 | 2026-05-12T14:25:48 | 448.5 |
| runner-log-old | C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-runner-logs\portable-runner-no-spawn-20260512_144251.log | 39324 | 2026-05-12T14:54:36 | 419.7 |
