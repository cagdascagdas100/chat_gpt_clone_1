# ReadyToSell 3 — Research waves 391–402

## Published scope
- 12 waves × 6 rows = 72 research-only candidates.
- Official source: Auction House East Anglia current aggregate catalogue.
- Source confidence: 72/72 at 98.0; average 98.0/100.
- Visible research rows: 2,405 → 2,477 (+72).
- Promotion, parcel match and geometry match: 0 / 0 / 0.

## Source filtering
- Six explicit status rows were excluded: lots 17, 27, 39, 52, 72 and 76.
- Six active rows already published in waves 389–390 were excluded from this source slice.
- `1 Newmans Cottages` was excluded because the official page also exposes a prior sold result.
- `The Annex, Fishermans Lodge` was captured in wave 390 but is now marked `Withdrawn`; this conflict is preserved and not silently rewritten.

## Semantics
- Guide prices are not achieved sale prices.
- Lot, address and marketing type are retained only as publisher facts.
- Auction date and tenure are `not_exposed` on the aggregate page.
- No legal-title, lawful-use, parcel or geometry inference was made.
- Duplicate checking is bounded to recent waves/current batch; it is not a complete historical title or UPRN scan.

## Publication
- Lightweight web view contains the latest 12 waves and 48 operation events.
- Older wave groups remain archive links.
- Same continuation key retained; no new task, runner or owner.
- External blocker remains `CANONICAL_RUNNER_EXTERNAL_BLOCKED_DOM_PROOF_ABSENT`.
