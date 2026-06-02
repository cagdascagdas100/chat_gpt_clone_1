# Cost50 Step 012 DB Model Gap Audit

Generated: 2026-05-12T12:23:14
Task: cost50-012-db-model-gap-audit-20260512

## Scope
- Read-only DB model and migration gap audit.
- No source mutation, no DB writes, no external fetch.

## Required tables
- cost_sources: False :: official source registry with URL, source_id, priority, source_type
- cost_source_fetch_runs: False :: source fetch manifest run tracking
- cost_facts: False :: extracted source facts using template schema fields
- cost_fact_scores: False :: reliability, correctness, confidence, seed penalty scoring
- cost_estimates: True :: estimate header per parcel/run
- cost_estimate_lines: False :: itemized cost lines and material quantities
- cost_run_logs: True :: error and audit log for every failure path

## Required field signals
- source_id: True
- source_url: True
- evidence_text: True
- reliability: True
- correctness: False
- confidence: True
- is_seed: True
- material_quantity: False

## Missing tables
- cost_sources
- cost_source_fetch_runs
- cost_facts
- cost_fact_scores
- cost_estimate_lines

## Missing field signals
- correctness
- material_quantity

DB model coverage percent: 53

PLAN_PROGRESS_PERCENT=24
TASK_COMPLETION=100/100
TERRAYIELD_TASK_DONE
