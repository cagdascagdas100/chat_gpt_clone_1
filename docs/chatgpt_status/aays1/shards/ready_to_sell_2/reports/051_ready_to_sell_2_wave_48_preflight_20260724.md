# ready_to_sell_2 — Wave 48 first-party preflight

- Slot: `ready_to_sell_2`
- Continuation key: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Canonical branch: `codex/aays-single-runner-v5-20260706`
- Publication branch: `agent/ready-to-sell-2-wave48-preflight-20260724`
- Source access: `2026-07-24T12:10:00Z`
- State: child-branch research preflight only; canonical counts unchanged.

## Verified output

- 10 current first-party auction rows prepared.
- 40 line-level preflight operations completed.
- Mean first-party source confidence: `99.90/100`.
- 0 rows accepted as repository-unique because repository-wide duplicate search was inconclusive.
- 0 rows promoted because canonical parcel geometry and Automation 167 DOM truth are absent.
- Canonical progress remains `869/870 (99.89%)`; increase `0.00` percentage points.
- Existing aggregates remain 514 researched candidates and 477 source-upgrade rows.

## Candidate rows

| # | Candidate | Auction | Guide | Verified state | Confidence | First-party source |
|---:|---|---|---|---|---:|---|
| 1 | 10 Brooklyn Avenue, Loughton | 2026-07-28 | £400,000 | Vacant; modernisation; development potential STC only | 99 | https://auctions.savills.co.uk/auctions/28-july-2026-227/10-brooklyn-avenue-loughton-essex-ig10-1bl-23983 |
| 2 | 1-10 Nissa Ashram, Birmingham | 2026-07-28 | £650,000 | Freehold; vacant; 10 flats plus office; C2 use context | 100 | https://auctions.savills.co.uk/auctions/28-july-2026-227/1-10-nissa-ashram-66a-fernley-road-birmingham-west-midlands-b11-3np-23520 |
| 3 | Flat A, 68 Rattray Road, Brixton | 2026-07-28 | £335,000 | Vacant; new 990-year lease on completion | 100 | https://auctions.savills.co.uk/component/bidding/28-july-2026-227/flat-a-68-rattray-road-brixton-london-sw2-1be-23767 |
| 4 | 10 Ryecotes Mead, Dulwich | 2026-07-28 | £500,000 | Vacant; leasehold; 40 years unexpired | 100 | https://auctions.savills.co.uk/auctions/28--29-july-2026-227 |
| 5 | Flats 1-5, 165 Chatham Street, Liverpool | 2026-07-28 | £165,000 | Freehold; vacant; Grade II listed; five flats; STC only | 100 | https://auctions.savills.co.uk/auctions/28--29-july-2026-227/flats-1-5-165-chatham-street-liverpool-l7-7az-23353 |
| 6 | Flat 4, 52 Gleneagle Road, Streatham | 2026-07-28 | £225,000 | Current periodic tenancy £24,000 p.a.; new 999-year lease | 100 | https://auctions.savills.co.uk/auctions/28-july-2026-227/flat-4-52-gleneagle-road-streatham-london-sw16-6af-23779 |
| 7 | 6 Glebe Meadow, East Dean | 2026-07-28 | £100,000 | Freehold; vacant; knotweed, severe mould and shared sewage obligations | 100 | https://auctions.savills.co.uk/auctions/28-july-2026-227/6-glebe-meadow-east-dean-salisbury-wiltshire-sp5-1he-23269 |
| 8 | 193 Whitehorse Road, Croydon | 2026-07-28 | £225,000 | Freehold; vacant; loft/rear extension STC only | 100 | https://auctions.savills.co.uk/index.php?id=24049&layout=details&option=com_bidding&view=commission |
| 9 | 25 Norman Grove, Bow | 2026-07-28 | £785,000 | Freehold; vacant; no uplift inferred | 100 | https://auctions.savills.co.uk/auctions/28-july-2026-227/25-norman-grove-bow-london-e3-5eg-23943 |
| 10 | 4, 5, 5A & 5B Alexandra Mews, Blackburn | 2026-07-29 | £177,500+ | Leasehold; occupied; £17,280 p.a. current rent; land use STC/access constrained | 100 | https://www.sdlauctions.co.uk/property/51336/for-auction-blackburn/ |

Guide prices are retained only as guide prices, not achieved sale prices.

## Recovery and safety

- The existing Automation 167 continuation and queue were not replaced.
- No second runner, parallel runner, or second business task was created.
- Manual action remains OPEN because the external Windows F-host scanner is not currently polling.
- Required host action: run only `START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd` at the F-host repository root and verify `http://127.0.0.1:8012/health`; do not start a second runner.
- `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
