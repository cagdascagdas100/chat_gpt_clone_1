# internet_access_2 — Extractor validation and source guardrail audit

## Extractor core contract

- Tests executed: `12`
- Tests passed: `12`
- Pass rate: `100%`
- Full integration executed: `false`

Validated rules:

1. Postcodes are normalized by removing spaces and punctuation.
2. Existing matrix value strings retain level, postcode, gigabit, UFBB100, SFBB and unable30 fields.
3. The lower shard boundary `30762` is included.
4. The upper shard boundary `61522` is included.
5. Rows `30761` and `61523` are rejected.
6. Exact Ofcom v2 headers resolve for postcode, SFBB, UFBB100, gigabit and unable-30 metrics.
7. Postcode-area extraction selects only matching `202601_fixed_postcode_coverage_r2_XX.csv` files.

This is a core-contract test. It does not claim that the 32.2 MB official ZIP or the canonical 92,283-feature matrix was executed in this connector session.

## Source guardrail audit

The Ofcom Connected Nations Broadband API is official, but its product page describes subscriber plans. It is therefore rejected for the current pipeline because the project permits open/free public sources and prohibits login/subscription-required inputs. The open Ofcom Spring 2026 ZIP remains the canonical candidate.

## Counts

- Allowed official source candidates: `4`
- Rejected gated source: `1`
- Source candidate rows visible on web: `4`
- Validation rows visible on web: `12`
- Promoted parcel rows: `0`
- Actual business rows written: `0`
- `final_ready=false`
