# ready_to_sell_2 — Wave 48 part 14 income and vacancy expansion

- Slot: `ready_to_sell_2`
- Continuation: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Branch: `agent/ready-to-sell-2-wave48-preflight-20260724`
- First unverified step preserved: `AUTOMATION_167_DOM_PROOF`

## This expansion

- 30 additional first-party Auction House rows
- 150 additional line-level operations
- Aggregate child candidates: 235
- Aggregate child operations: 1164/1164 (100%)
- New-batch source confidence: 98.97/100
- Aggregate first-party source confidence: 99.37/100
- Accepted unique rows: 0
- Promoted rows: 0

## Accuracy guards

- 101 New Road preserves vacant possession, approximately 927 lease years and fixed £5 ground rent.
- 5 Glenholme records only the current £500 pcm contractual rent (£6,000 p.a.).
- 10 Glenholme records only the current £465 pcm contractual rent (£5,580 p.a.).
- 14 Regent House records only the current £635 pcm contractual rent (£7,620 p.a.).
- 90 Balfour Road records only the current £400 pcm contractual rent (£4,800 p.a.).
- 8 Villette Path preserves vacant possession and freehold tenure without inventing future rent.
- 30 Park Village keeps HMO/student-let wording as potential only; licensing and income remain unproven.
- Catalogue-partial rows remain unknown for tenure, occupation, charges and income rather than inferred.

## Canonical preservation

- Canonical candidates: 514
- Canonical source upgrades: 477
- Canonical operations: 869/870 (99.89%)
- Canonical percentage delta: 0.00
- `canonical_progress_advanced=false`
- `final_ready=false`

## Blocker

The Windows F-host single shared scanner is still not polling. Owner remains unclaimed, heartbeat is stale and real port-8012 Automation 167 DOM acceptance is absent. No second task, runner or PR was created. Manual action remains OPEN.

## Web visibility

The Wave 48 progress page loads twenty-two candidate packages and twenty-two progress packages, rendering 235 candidate rows and 1164 operation rows individually.