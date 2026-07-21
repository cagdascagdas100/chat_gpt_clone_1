# internet_access_2 complete candidate JSONL hardening — 2026-07-21

- Fresh authoritative HEAD: `ead7b04af5ad93ffe12336a8b0f6c40906e1f158`.
- Authoritative slot remains sequence 0, `ready_for_claim`, `unclaimed`, stale heartbeat and idle task.
- Queue head remains `security_public_safety_3` attempt `008`, priority 1, `pickup_requested`.
- Official Ofcom Spring 2026 page still identifies a January 2026 snapshot and lists the fixed broadband package as 32.3 MB.

## Defects repaired

1. A valid canonical/legacy postcode absent from current Ofcom r2 was retained by the extractor as `POSTCODE_NOT_IN_CURRENT_R2`, while the old bundle verifier rejected every postcode on a `NO_DATA` example. The verifier now distinguishes `NO_POSTCODE` from `POSTCODE_NOT_IN_CURRENT_R2`.
2. A direct or legacy row could be labelled ready for review even if every published Ofcom metric was null. The complete candidate integrity audit now rejects such rows fail-closed.
3. Previously only readback totals and a maximum of nine examples were deeply audited. The new streaming verifier checks all 30,761 JSONL rows, exact order, unique IDs, status-specific confidence/method semantics, manifest totals, SHA-256 and review-only boundaries.

## Deterministic evidence

- Complete candidate JSONL integrity: 25/25 PASS.
- Published bundle truth boundaries: 23/23 PASS.
- Canonical run-and-audit wrapper: 28/28 PASS.
- Combined deterministic validation: 215/215 PASS.

No official ZIP bytes, real slot rows, scores, business rows, DB writes, migrations, deployment or final-ready state were produced.
