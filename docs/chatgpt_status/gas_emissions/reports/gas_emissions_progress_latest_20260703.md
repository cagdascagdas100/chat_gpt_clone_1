# Gas Emissions Progress Latest

updated_at=2026-07-03T17:39:29Z
final_ready=False
verification_score_after=1/4
blocker_count=2
source_row_gate_passed=False
ui_token_gate_passed=True
browser_smoke_passed=False

## Blockers
[
    {
        "code":  "missing_verified_source_backed_rows",
        "severity":  "blocking",
        "detail":  "No real source-backed Gas Emissions parcel rows were found in the fixture CSV."
    },
    {
        "code":  "browser_smoke_failed",
        "severity":  "blocking",
        "detail":  "Browser smoke exists but did not pass."
    }
]

## Next Action
Resolve blockers and rerun the same single bridge.
