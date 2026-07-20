# ReadyToSell Shard 2 — Official Candidate Wave 4

- SLOT_ID: `ready_to_sell_2`
- Parcel range: `30762-61522`
- Snapshot date: `2026-07-20`
- Result: `OFFICIAL_CANDIDATE_WAVE_4_PUBLISHED`
- New candidates: `4`
- Total research candidates visible on shard web page: `16`
- Latest-wave average source confidence: `98.0/100`
- Aggregate average source confidence: `97.63/100`
- Promoted product rows: `0`

## New official-source candidates

1. **St Cuthbert's Church, Hartlepool** — guide GBP 210,000; 0.74 acres; freehold vacant church site. The direct Savills record explicitly says there is no current planning permission and alternative uses remain subject to consent.
2. **Bordesley House, Birmingham** — guide GBP 180,000; 8,049 sq ft former offices with rear car park. Development/conversion potential is catalogue-level and subject to consents; no granted permission is claimed.
3. **452 Denton Road, Newcastle upon Tyne** — current July guide remains TBA. The prior April available price of GBP 330,000 is recorded only as historical context. The medical-centre investment has development potential subject to consents, not a proven permission.
4. **Flats 1-5, 165 Chatham Street, Liverpool** — guide GBP 165,000; Grade II listed, vacant five-flat property requiring refurbishment. Further development is subject to consents.

## Accuracy controls

- `subject to consents` was not converted into granted planning permission.
- Historical price evidence was not substituted for a current guide price.
- Grade II listing and explicit no-permission status remain blockers.
- No candidate was bound to a parcel or promoted without canonical geometry evidence.
- No fake data, database write, migration or production deployment occurred.

## Web evidence

- Aggregate page: `england_map_web/ready_to_sell_2_progress.html`
- Wave data: `england_map_web/data/aays_21_slots/ready_to_sell_2/candidate_wave_4_latest.json`
- Progress data: `england_map_web/data/aays_21_slots/ready_to_sell_2/progress_latest.json`

## Remaining blocker

`EXISTING_SHARED_RUNNER_REMOTE_HEARTBEAT_STALE_AND_AUTOMATION_167_PICKUP_NOT_PROVEN`

Automation 167 still requires genuine execution by the existing canonical single shared runner, a real port-8012 headless-browser DOM readback, commit/push and remote readback. No new or parallel runner was created.

`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.
