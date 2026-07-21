# internet_access_2 candidate postcode resolution hardening — 2026-07-21

- Detected a fail-closed mismatch: a malformed canonical postcode was selected before a valid legacy postcode, causing the later complete JSONL audit to reject the row instead of using the explicit legacy QA path.
- Added syntax-aware resolution before Ofcom lookup.
- Valid canonical postcode remains authoritative.
- Valid legacy postcode is used only when canonical postcode is missing or invalid, and remains confidence 0.70 with spatial QA required.
- When canonical and legacy postcodes are both valid but differ, canonical remains selected and the conflict is recorded.
- Invalid candidates never enter the selected `postcode` field; they remain provenance-only.
- Added complete 30,761-row postcode-resolution audit and deterministic 18/18 self-test.
- Canonical wrapper contract is 40/40 and combined deterministic validation is 314/314.
- No score, business row, DB write, migration, deployment, queue write, ownership claim or final-ready mutation occurred.
