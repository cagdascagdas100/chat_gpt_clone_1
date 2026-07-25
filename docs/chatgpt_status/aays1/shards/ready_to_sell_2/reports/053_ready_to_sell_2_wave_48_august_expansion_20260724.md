# ready_to_sell_2 — Wave 48 August first-party expansion

- Continuation key: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Preserved first unverified step: `AUTOMATION_167_DOM_PROOF`
- Publication branch: `agent/ready-to-sell-2-wave48-preflight-20260724`

## Verified result

- New current first-party candidate rows: **10**
- New row-level operations: **50 / 50**
- Aggregate child candidate rows: **40**
- Aggregate child operations: **189 / 189**
- New batch source confidence: **99.50%**
- Aggregate child source confidence: **99.73%**
- Canonical candidates/source upgrades preserved: **514 / 477**
- Canonical progress preserved: **869 / 870 — 99.89%**
- Canonical progress increase: **0.00 percentage points**
- Unique rows accepted: **0**
- Rows promoted: **0**

## New examples

- 86 Windsor Road: two existing flats; conversion-back wording held as marketing only.
- 19 Rushbrook Mill: leasehold apartment with 104 years remaining; refurbishment only.
- Flat 3, 207 Stuart Road: vacant leasehold renovation lot.
- Apartment 58, Lovell House: £795 pcm is a comparable listing signal, not current income.
- Woolley Hall: Grade II* listed, freehold, vacant, 18.7 acres; redevelopment remains STP.
- Former High Well School: freehold vacant 12.7-acre site; redevelopment remains STP.
- 9 Hungerton Street: current £2,426.67 pcm / £29,120.04 annual HMO income retained.
- 164 Rake Hill: vacant freehold; extension potential remains subject to consent; guide remains TBA.

## Accuracy and safety

Repository code search still returns a false negative for the known Wave 47 control `97 Mandeville Court`; all new rows therefore remain HELD. Canonical parcel geometry and real port-8012 Automation 167 DOM evidence remain absent. No second runner, parallel runner, second task, DB write, migration, deployment, fake data or canonical direct push was created. `final_ready=false`.
