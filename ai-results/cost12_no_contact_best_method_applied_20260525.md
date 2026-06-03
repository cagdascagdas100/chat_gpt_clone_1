# COST12 No-Contact Best Method Applied — 2026-05-25

Decision: NO_CONTACT_OFFICIAL_PROCUREMENT_SEARCH_APPLIED_NO_PRODUCTION_READY_ROW_FOUND

## Selected method

Because the user does not want external contact, the best method is official no-contact procurement/public-document search.

Sources checked conceptually and through public web research:

- GOV.UK Contracts Finder
- Find a Tender service
- public project cost/floor-area sources
- public retail/restaurant/shop fit-out guides

## Why this was the best no-contact method

- It does not require contacting BCIS, RICS, QS firms or contractors.
- It can produce production-ready evidence only if a document contains contract value, GIA or area basis, retail/shop/restaurant scope, date and inclusions/exclusions.
- It is stronger than generic blog/public project proxy if a matching official tender/award document is found.

## Result

No production-ready no-contact source row was found for:

- scenario_version=cost_uk_v1
- building_type=retail
- spec_grade=mid
- region=UK
- unit=GBP per gross internal area square metre

## Current safe output

Review-mode is complete:

COST12_READY_FOR_HUMAN_REVIEW_PUBLIC_PROXY

Production-ready remains blocked:

BLOCKED_SOURCE_REQUIRED

## Why public project examples were rejected for production

Public project examples may contain project cost and floor area, but they are not direct mid-spec retail/shop/restaurant rate-card rows and often differ in scope, date, geography, architecture and included/excluded cost items.

## Next possible no-contact improvements

1. Repeat official procurement search with narrower terms:
   - retail fit-out
   - shop fit-out
   - restaurant fit-out
   - cafe fit-out
   - GIA
   - gross internal area
   - contract value
   - square metres

2. Check downloaded tender PDFs manually if contract value and area both appear.

3. If a matching official document is found, classify as official_procurement and rerun acceptance checks.

## Safety

- db_write=false
- production_deploy=false
- fake_data=false
- migration=false
- production_release=false
