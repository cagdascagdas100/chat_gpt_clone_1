# COST12 No-Contact Internal Approval Path — 2026-05-25

Decision: INTERNAL_APPROVAL_PATH_PREPARED_NOT_FINAL_READY

## Context

The user requested no external contact. The following no-contact methods were applied or prepared:

1. Official procurement / tender-document search
2. Public project proxy research
3. Local/internal source search
4. Internal approval path preparation

## Best remaining no-contact path

The best remaining no-contact path is an approved internal source path.

This does not mean the current seed/catalog value is production-ready by itself. It means an authorized internal approver may choose to accept a defined internal benchmark with documented limitations.

## Candidate internal evidence already found

File:

`tools/cost_uk_real_engine/config/cost_item_catalog_12cost.csv`

Retail-related row found:

- main_category: Fit-out
- sub_category: Retail
- building_group: retail
- cost_item: Retail fit-out shopfront signage
- unit: m2
- price_type: gbp_per_m2
- min/default/max: 400 / 1200 / 3500
- source_id: SRC_BCIS
- source_url_or_path: generic RICS/BCIS page
- accuracy_score_4: 1
- is_seed_based: true

## Why this is not enough alone

The row is a seed/catalog item. It is not a verified building_type rate-card source row for:

- scenario_version=cost_uk_v1
- building_type=retail
- spec_grade=mid
- region=UK
- unit=GBP per gross internal area square metre

It lacks:

- direct BCIS/RICS extract/reference
- source month/base date
- full scope and inclusions/exclusions
- high source reliability
- explicit internal approval

## How it could become an approved internal source

Only if an authorized internal approver signs off the row as an internal benchmark with limitations.

Required approval metadata:

- approved_by
- approval_date
- approval_reason
- scope_note
- limitation_note
- reliability_score
- decision_label

Recommended label if approved without stronger external source:

APPROVED_INTERNAL_SOURCE_WITH_LIMITATIONS

Not recommended label:

FINAL_READY_CONFIRMED

## Safety status

- db_write=false
- production_deploy=false
- fake_data=false
- migration=false
- production_release=false

## Final current state

- Review-mode: 100% complete
- Production-ready: 99%
- Production 100 requires approved internal sign-off or stronger external verified source.
