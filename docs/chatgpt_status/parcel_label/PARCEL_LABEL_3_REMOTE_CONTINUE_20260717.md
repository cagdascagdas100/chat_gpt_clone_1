# Parcel Label 3 - Remote-only continuation

When the user writes `parcel label 3 projesine kaldigin yerden eski yaptiklarini bir daha yapmadan cakisma olmadan devam et`, do not ask for a ZIP or old-page files.

1. Read GitHub branch `codex/aays-single-runner-v5-20260706` HEAD.
2. Read the four files under `docs/chatgpt_status/_shared/slots/parcel_label/` plus `docs/chatgpt_status/aays1/checkpoints/parcel_label_canonical_checkpoint.json`.
3. Read `docs/chatgpt_status/_shared/contracts/AAYS_ENGLAND_PARCEL_COVERAGE_AND_POLYGON_CLICK_CONTRACT_20260717.md` and `docs/chatgpt_status/parcel_label/ENGLAND_PARCEL_CONTINUATION_20260717.md`.
4. Treat Task 214 execution as terminal/non-replayable evidence. Preserve its blocked acceptance evidence; do not rerun Task 214 or earlier tasks.
5. Claim only slot `parcel_label` as page session `parcel_label_3` when ownership is unclaimed or stale. Never write another slot.
6. Continue from `BUILD_CANONICAL_92283_ROW_RECONCILIATION_MANIFEST_THEN_FIRST_UNVERIFIED_BATCH` using the existing shared runner and existing business status root `docs/chatgpt_status/aays1`.
7. Keep exactly 92,283 unique canonical parcel rows. Match official IDs first, then point-in-polygon. Do not assign an unrelated nearest point.
8. Push evidence and perform remote readback before increasing verified metrics.

No new runner, guardian, duplicate queue task or replacement architecture. `final_ready=false` until real 92,283-row value coverage and browser proof pass.
