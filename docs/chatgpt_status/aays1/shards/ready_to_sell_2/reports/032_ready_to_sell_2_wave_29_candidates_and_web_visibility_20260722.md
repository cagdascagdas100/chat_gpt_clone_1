# Ready to Sell 2 — Wave 29 Candidates and Web Visibility

- Slot: `ready_to_sell_2`
- Parcel partition: `30762-61522`
- Source snapshot: `2026-07-22`
- Remote HEAD read before work: `4dfefe6f2e3edf23d3b1a958746e6a5072241c30`
- First unverified step preserved: `AUTOMATION_167_DOM_PROOF`

## Completed in this wave

1. Re-read remote checkpoint sequence 33, idle current-task and unclaimed stale heartbeat.
2. Proved the canonical row page loaded only waves 4-27 and therefore did not display wave 28 upgrades.
3. Screened seven current official records across Acuitus, SDL, BTG Eddisons and Pugh first-party pages.
4. Ran repository duplicate preflight for six proposed candidate titles; no prior candidate rows were returned.
5. Published six research-only candidates:
   - 29 Lowther Street, Carlisle
   - 39 Vineyard Path, Mortlake
   - 49 & 50 South Street, Dorchester
   - 241 Burncross Road, Sheffield
   - Former High Well School, South Hiendley
   - 1-6 Rock Road, Torquay
6. Cross-checked 29 Lowther Street and 49 South Street against Historic England list entries 1292521 and 1291216.
7. Excluded 20-24 Chapel Street because the current direct page says `Withdrawn Prior`, despite a stale Available index representation.
8. Extended the web row loader through wave 29 and moved the canonical redirect to `ready_to_sell_2_progress_wave_29.html`.

## Quality controls

- Latest batch average source confidence: `99.17/100`.
- Planning types remain distinct: pre-application advice, outline consent subject to S106, redevelopment potential subject to planning and listed-building controls are not represented as unconditional permission.
- New candidates remain research-only with `parcel_match_confidence_score=0`, `geometry_match_status=not_run` and `promotion_allowed=false`.
- No product promotion, real vision score, Automation 167 pass, browser acceptance or final readiness is claimed.

## Metrics

- Completed operations: `302/303`
- Batch progress: `99.67%` (`+0.01` point)
- Overall progress: `99.68%` (`+0.01` point)
- Aggregate candidates: `184`
- Current/upcoming/available: `181`
- New candidates: `6`
- Source upgrades this wave: `8`; cumulative: `147`
- Integrity repairs this wave: `2`; cumulative: `10`
- Withdrawn exclusions this wave: `1`

## Remaining blocker

The existing shared runner is not visibly polling, and the required real port-8012 headless-browser Automation 167 truth artifact is absent. The global current task was not overwritten and no new or parallel runner was created.

Safety state remains: `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
