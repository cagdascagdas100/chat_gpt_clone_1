# Ready to Sell 2 — Wave 48 first-party income/planning expansion

- Slot: `ready_to_sell_2`
- Continuation key: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Preserved first unverified step: `AUTOMATION_167_DOM_PROOF`
- Publication branch: `agent/ready-to-sell-2-wave48-preflight-20260724`
- Source snapshot: `2026-07-24`

## Result

- New first-party candidate rows: **10**
- Aggregate child candidate rows: **50**
- New line-level operations: **50**
- Aggregate child operations: **239 / 239 — 100%**
- New-batch source confidence: **99.50%**
- Aggregate source confidence: **99.68%**
- Accepted as repository-unique: **0**
- Promoted to canonical: **0**
- Canonical progress preserved: **869 / 870 — 99.89%**
- Canonical progress delta: **0.00 percentage points**
- Canonical candidates/source upgrades preserved: **514 / 477**

## Accuracy controls

1. The White Horse's current year-one rent of £30,000 is separated from stepped future contractual rents of £34,800 and £38,500.
2. Pendrill Street's current £6,600 annual rent is separated from the £13,800 fully occupied potential and the former £600 pcm rent of the vacant flat.
3. Pant Einion Hall's prior holiday-let wording is not treated as current occupation or current income.
4. Burncross Road's stated outline planning and Section 106 condition are retained as existing planning evidence.
5. Swan Farm conversion wording is retained as subject to planning and listed-building consent.
6. Austin Street's 2022 planning reference is recorded without assuming current validity or implementation.
7. All ten rows remain `HELD` because repository duplicate search failed its known control, parcel geometry is pending and real Automation 167 DOM evidence is absent.

## Candidate summary

| Candidate | Auction | Guide | Verified state | Confidence |
|---|---|---:|---|---:|
| The White Horse, Kearsley | 2026-08-26 | £250,000+ | Freehold subject tenancy; year-one rent £30,000 | 100 |
| Former Vehicle Depot, Conisbrough | 2026-08-24 | £150,000+ | Freehold commercial site; alternative use STP | 99 |
| 241 Burncross Road, Sheffield | 2026-08-24 | £950,000+ | Freehold vacant; outline planning up to 14 dwellings subject S106 | 100 |
| Swan Farm, Crewe | 2026-08-11 | £450,000 | Freehold vacant Grade II; conversion subject consents | 100 |
| Pant Einion Hall, Fairbourne | 2026-08-04 | £300,000 | Freehold; historic holiday-let wording, current occupation unknown | 99 |
| 83 Mow Cop Road | 2026-08-18 | £125,000–£160,000 | Freehold vacant | 100 |
| 59 South Road, Weston-super-Mare | 2026-08-04 | £135,000 | Freehold; occupation not stated | 99 |
| Flats 1 & 2, 11 Pendrill Street | 2026-08-18 | £90,000–£100,000 | Part tenanted/part vacant; current rent £6,600 p.a. | 100 |
| 121 Glebe Gardens, New Malden | 2026-08-18 | £425,000 | Freehold; occupation not stated | 99 |
| 113 Austin Street, Nottingham | 2026-08-18 | £90,000 | Freehold; 2022 planning reference requires portal readback | 99 |

## Blocker and safety

The Windows F-host single shared scanner is still not polling. Real port-8012 Automation 167 DOM acceptance is absent. The existing manual action remains OPEN. No second runner, parallel runner, second task, database write, migration, deployment, force push or canonical direct push was created.

`final_ready=false`
