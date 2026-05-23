# 5.1 Real 100 Dependency Plan — 2026-05-24

## Objective

Do not accept a fake 100%. Reach real completion only if the required real data exists locally or in the project. Otherwise produce a precise blocker report and keep the progress below 100.

## Non-negotiable constraints

- DB write: false unless user explicitly approves later.
- Production deploy: false unless user explicitly approves later.
- Fake data: false.
- Candidate rows are not verified rows.
- Verified rows require source evidence.

## Dependency graph

### Stage 1 — independent parallel discovery jobs

These jobs can run at the same time inside one runner:

1. Search parcel master/export candidates.
2. Search verified estate-agent source rows.
3. Analyze estate-agent candidate CSV for evidence fields.
4. Check coverage/scoring/export/join contracts.
5. Inspect application integration readiness.

### Stage 2 — dependency gate

Real 100 requires all of the following:

- A real parcel master/export with parcel_id and parcel_group_id or equivalent geometry/group mapping.
- Verified estate-agent rows with source_url/evidence_summary and at least one contact/location field.
- Coverage mapping contract and scoring rules.
- Join contract from clicked parcel_id to parcel group to ranked verified agents.
- Dry-run import contract and app lookup contract.

### Stage 3 — final action

If all gates pass, mark `real_100_ready_for_user_db_approval` but still do not write DB. If any real source is absent, mark `blocked_external_data_required` and list exact missing inputs.

## Fastest safe execution model

Use one runner process. Inside it, use PowerShell jobs for read-only discovery and contract validation. No parallel DB writes. No production actions.
