# ReadyToSell 3 — Research waves 479–481

## Published scope
- 3 waves containing 17 research-only candidates.
- Official sources: Auction House London live current-auction index plus official aggregate crosscheck.
- Auction date: 29–30 July 2026.
- Source confidence: 17/17 high-confidence; average 98.9/100.
- Visible research rows: 2,933 → 2,950 (+17).
- Promotion, parcel match and geometry match: 0 / 0 / 0.

## Source filtering
- Lots 224–242 excluded because the live index marks all 19 `Sold Prior`.
- Lot 214 excluded because Swansea is outside the England scope.
- Nine North West/South West recent-region overlap-risk rows excluded.
- Eight representative exact-address repository searches returned no prior match.
- Three official snapshot disagreements were retained explicitly.

## Semantics
- Guide prices are not achieved sale prices.
- Auction date, lot, address and tenure come from the official live current-auction index.
- Guide and marketing type were crosschecked against the official aggregate.
- No legal-title, lawful-use, parcel or geometry inference was made.
- Duplicate checking is bounded; it is not a complete historical title or UPRN scan.

## Runtime state
- Same continuation key retained.
- Owner remains unclaimed; no second task, runner or owner was created.
- External blocker remains `CANONICAL_RUNNER_EXTERNAL_BLOCKED_DOM_PROOF_ABSENT`.
