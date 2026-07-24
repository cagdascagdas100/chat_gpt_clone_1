# Gas Emissions — Official visible rows expansion to 28

Date: 2026-07-11  
Branch: `codex/aays-single-runner-v5-20260706`  
Status: `OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_28`

## Result

The canonical visible-row artifact was expanded from 24 to 28 exact official GOV.UK DESNZ source rows.

New rows:

1. `GHG-HPL-2005-waste-other-n2o` — source preview `L166` — 2.294280766 kt CO2e.
2. `GHG-HPL-2006-agriculture-gas-ch4` — source preview `L171` — 0.00812 kt CO2e.
3. `GHG-HPL-2006-agriculture-gas-n2o` — source preview `L172` — 0.000231 kt CO2e.
4. `GHG-HPL-2006-commercial-electricity-n2o` — source preview `L182` — 0.440147326 kt CO2e.

Source: GOV.UK DESNZ, *2005 to 2023 local authority greenhouse gas emissions dataset*, updated 19 August 2025.

## Accuracy and scope

- Matching method: `official_govuk_preview_line_exact`
- Confidence: `88%`
- Accuracy score: `3.4/4`
- New high-accuracy rows: `4`
- Visible rows after update: `28`
- Parcel-specific binding: pending
- Browser smoke for the new 28-row state: pending
- `final_ready=false`
- `fake_data=false`

No parcel allocation, geometry, derived emission percentage or final product claim was invented. The canonical runner must pull the branch, refresh the 8012 site and produce 28/28 Chrome/Selenium readback before browser smoke can be marked passed.
