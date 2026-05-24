# COST12 Can Codex Finish Production-Ready? — 2026-05-24

Short decision:

Codex can complete the review-mode integration work, but Codex cannot honestly complete production-ready 100% without a verified source row.

## What Codex can do

Codex can:

- Read the public proxy candidate row.
- Stage it as review-mode only.
- Preserve production_ready=false.
- Preserve db_write=false.
- Preserve production_deploy=false.
- Preserve fake_data=false.
- Add tests ensuring public_proxy rows cannot be treated as production-ready.
- Add UI/API labels showing COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY.
- Keep FINAL_READY_CONFIRMED false.

## What Codex cannot honestly do

Codex cannot:

- Invent a retail/mid/UK/cost_uk_v1 rate.
- Copy residential or warehouse rates into retail without a verified mapping source.
- Turn public proxy data into production-ready evidence.
- Mark FINAL_READY_CONFIRMED while the verified retail rate row is missing.

## Why production-ready remains blocked

The missing required source row is:

- scenario_version=cost_uk_v1
- building_type=retail
- spec_grade=mid
- region=UK
- base_rate_gbp_per_gia_m2=<verified value required>

Accepted strong evidence:

- BCIS/RICS extract or reference
- official public authority rate or fee schedule
- supplier or contractor quote
- approved internal cost source with traceable path or URL

## Current safe completion state

- Review-mode: 100% complete
- Production-ready: 99%, blocked by verified source requirement

## Codex instruction

If asked to finish now, Codex should finish only review-mode and report:

COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY

It should not report FINAL_READY_CONFIRMED unless a strong verified source row is provided.
