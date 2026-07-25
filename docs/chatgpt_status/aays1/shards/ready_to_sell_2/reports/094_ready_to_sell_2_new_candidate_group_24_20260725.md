# ready_to_sell_2 — New Candidate Group 24

- Workstream: `AAYS_21_SLOT_SAFE_PARALLEL_V1`
- Continuation key preserved: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- First unverified canonical step remains `AUTOMATION_167_DOM_PROOF`
- Publication scope: staging branch and existing draft PR only
- Promotion: forbidden

## Results

- 20/20 current first-party source records accessible.
- 20/20 exact repository duplicate preflights completed; 0 matches.
- 40/40 source and duplicate checks completed.
- 160/160 source-supported fields verified.
- 128 source-supported enrichments recorded.
- Average verification confidence: 99.3/100.
- 17 semantic-warning rows and 2 source-internal conflict rows retained fail-closed.
- Savills Lot 295 was marked Sold Prior and excluded.

## Selected records

- Pembroke & Castlemartin Social Club: freehold former social club, 4,418 sq ft, caretaker flat not self-contained and vacant possession; change-of-use potential remains subject to planning.
- 306 Maid Marion House: £7,370 p.a. source income but advertised 2.35% yield conflicts with simple guide-price arithmetic; both values retained with a blocker.
- Pizza Express, Salisbury: freehold restaurant investment, 2,987 sq ft, £56,950 p.a., lease to May 2034 without breaks.
- Sports Direct, Tottenham: freehold 10,489 sq ft retail investment producing £175,000 p.a.
- 49 & 50 South Street: Grade II former bank, 10,278 sq ft, sixteen parking spaces and vacant possession; sale remains conditional and conversion requires planning/listed-building consent.
- 15 Davy Court: freehold office investment, 10,041 sq ft, fifty parking spaces and £123,050 p.a.
- Holland & Barrett, Bangor: virtual-freehold retail investment producing £18,000 p.a.; tenant break, seller top-up and source rent-free placeholder retained fail-closed.

## Guards

- Advertised yield arithmetic conflicts were not silently corrected.
- Current leases, leases commencing on completion, tenant breaks and conditional-sale wording were stored separately.
- Development and change-of-use potential were not promoted to planning permission.
- Public guide prices were not invented where the first-party source states `Contact Us`.
- No fake data, candidate promotion, database write, migration, force push or runner duplication occurred.

## Automation blocker

Automation 167 remains queued for the existing single F-host runner. The slot heartbeat remains unclaimed/stale; no second task or runner was created.
