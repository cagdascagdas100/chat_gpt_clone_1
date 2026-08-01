# AAYS 22 Slot Acceleration and ETA - 2026-08-01

## Operating truth

- Topology: 21 data slots plus 1 Problem Solver slot.
- Physical concurrency: at most 15 workers, not a permanent 15-worker target.
- The 16 GB profile keeps resource gates: network 8, browser research 4,
  browser acceptance 2, geometry 2, CPU-heavy 3, RAM-heavy 2, heavy disk 1,
  and Git publish 1.
- A ChatGPT `devam` message is productive only when it creates a real commit or
  a schema-v3 READY task with a tracked executable `script_path`.
- Progress percentages below are evidence-backed milestone percentages. A high
  research percentage does not mean the canonical parcel output is complete.

## Per-slot dispatch plan

| Slot | Evidence-backed current position | Next useful task | ETA after task is runnable |
|---|---|---|---|
| future_growth_1 | NO_DATA_CONTINUE; official geometry pipeline stalled | Refresh Planning Data entities, write canonical match/no-data manifest | 2-5 days |
| future_growth_2 | 330 accepted response rows; canonical export 0 | Create tracked export script and READY task for partition 30762-61522 | 2-5 days |
| future_growth_3 | Source waves completed; canonical export missing | Promote only current official entities, then bind exact partition rows | 2-4 days |
| gas_emissions_1 | 1,699 visible evidence rows; measured parcel rows 0 | Execute measured facility-to-parcel binding and browser acceptance | 2-4 days |
| gas_emissions_2 | Browser acceptance 66/100; source accuracy 99% | Finish 34 browser rows, then prove parcel binding | 1-3 days |
| gas_emissions_3 | Research 99.9987%; promotion count 0 | Run V11 browser gate and promote only passing candidates | 0.5-2 days |
| height_difference_1 | Product milestone 78%; measured rows 0 | Resolve current EA DTM 1 m coverage id, sample exact polygons | 2-5 days |
| height_difference_2 | Overall 78%; operations 340/381 | Run 3 HMLR polygons, 3 DTM samples, 3 Terrain50 checks | 1-3 days |
| height_difference_3 | Technical publication exists; runtime lineage blocked | Re-run canonical API measurement with current F: runner receipts | 1-2 days |
| internet_access_1 | 33,785 verified; 58,498 pending/no-data | Supply official Ofcom 2026 ZIP, schema-check, then bounded join | 3-7 days after ZIP |
| internet_access_2 | Dynamic ZIP join task published | Verify readback and merge only newly verified rows | 0.5-1 day |
| internet_access_3 | 594-row contract target reported 100% | Reconcile contract rows against 92,283-row canonical matrix | 1-2 days |
| parcel_label_1 | Research operations 97.35%; canonical rows 0 | Build 92,283-row reconciliation manifest and first exact batch | 3-7 days |
| parcel_label_2 | Canonical sample published; exact geometry rows 0 | Close sequence gap and bind source ids to canonical parcel ids | 2-5 days |
| parcel_label_3 | Workflow 99.983%; exact geometry rows 0 | Finish 2 operations and publish exact-geometry reconciliation | 1-3 days |
| ready_to_sell_1 | Completion 99.66% | Re-run Automation 167 DOM proof and remote readback | 0.5-1 day |
| ready_to_sell_2 | Published | Readback regression only; do not re-run without a change | done |
| ready_to_sell_3 | Visible research 99.968%; promoted rows 0 | Run DOM proof and promote only passing canonical rows | 1-2 days |
| security_public_safety_1 | 300/300 hydrated and accuracy-4 | Claim V17, run HTTP/hash/DOM/console acceptance | 0.5-1 day |
| security_public_safety_2 | Overall 40%; runtime joined rows 0 | Correct H: to F:, run official-source join and browser gate | 3-6 days |
| security_public_safety_3 | Progress 80%; 300 candidates | Run current script from queue HEAD, seal lineage and 12-page gate | 1-2 days |
| problem_solver_1 | Monitors 21 slots | Repair technical blockers; dispatch only tracked-script READY tasks | continuous |

## Completion estimate

- Optimistic: 5-7 days, if Ofcom ZIP and EA DTM identifiers are immediately
  available and 8-12 productive tasks stay runnable.
- Realistic: 10-16 days with 7/24 operation, 15-minute continuation checks,
  serial Git publishing, browser/geometry limits, and current external gates.
- Adverse: 20-35+ days if Ofcom access, canonical polygon inputs, or official
  elevation identifiers remain unavailable. Those delays are unbounded until
  the real source is supplied; they must not be closed with inferred data.

The theoretical prompt volume is 22 pages x 96 prompts/day = 2,112 prompts/day.
That is not throughput. Useful throughput is the number of commits containing
new evidence or runnable READY tasks. Repeating a prompt while the same task is
running only wastes credits and creates Git contention.

## Source and storage contract

Every new task must carry:

1. Official/free source URL and access timestamp.
2. SHA-256 of the retrieved content or bounded response.
3. Exact fields, record ids, rows, or a short relevant excerpt supported by it.
4. The output fields that the source proves.
5. License or terms URL when available.
6. Completed and target row counts for an evidence-backed progress percentage.

Git stores only:

- derived usable rows,
- one compact evidence manifest,
- one reconciliation/checkpoint file,
- a small browser acceptance artifact when required.

Large raw ZIP/JSON/raster files stay in runtime cache. Temporary files are
deleted after atomic output. Duplicate wave reports, screenshots without an
acceptance purpose, full HTML copies, and repeated raw source copies are not
stored.

## ChatGPT page completion contract

When work remains for the local runner, the page must commit and push a schema
v3 task with `status=ready`, `state=READY`, `claimable=true`,
`ready_for_claim=true`, a tracked and parseable `script_path`, bounded
`read_paths`, exact `exact_write_paths`, resource classes, source manifest
fields, and completed/target counts. A status-only commit does not start a
local worker.
