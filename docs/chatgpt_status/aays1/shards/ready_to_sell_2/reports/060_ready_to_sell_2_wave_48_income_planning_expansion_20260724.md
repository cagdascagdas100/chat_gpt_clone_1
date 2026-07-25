# ready_to_sell_2 — Wave 48 part 11 income/planning expansion

- Slot: `ready_to_sell_2`
- Continuation: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Branch: `agent/ready-to-sell-2-wave48-preflight-20260724`
- First unverified step: `AUTOMATION_167_DOM_PROOF`

## Published this turn

- 20 current first-party Auction House / SDL candidate rows.
- 100 line-level source, schedule, income, tenure, planning, duplicate-hold and promotion-guard operations.
- Aggregate child preflight: 165 candidates and 814/814 operations.
- New batch average source confidence: 99.40/100.
- Aggregate child source confidence: 99.46/100.
- Browser row loader extended through candidate/progress parts 11a and 11b.

## Accuracy controls

- The White Horse current year-1 income remains £30,000 p.a.; later stepped rents remain future contractual amounts.
- Flat 3, 81 East Parade current published income remains £8,700 p.a.
- 241 Burncross Road planning remains subject to Section 106 and is not unconditional buildability.
- St Andrews Green short-lease risk is retained separately.
- Blank ground-rent/service-charge fields for 4 Ashburton Road are not converted to zero.
- Historic holiday-let, STP, listed-building and occupation-unknown states remain separate.
- Repository duplicate search failed its known control; all new rows remain HELD.

## Canonical state preserved

- Canonical candidates: 514.
- Canonical source-upgrade rows: 477.
- Canonical operations: 869/870 (99.89%); delta 0.00.
- Accepted unique rows: 0; promoted rows: 0.
- Manual action remains OPEN because the F-host shared scanner is not polling and real port-8012 DOM evidence is absent.
- No second task, runner or PR was created.
- `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
