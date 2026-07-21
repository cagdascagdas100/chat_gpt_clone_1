# future_growth_2 wave 15, missing spatial locator and Greenwich provider safeguards

- Scope remains `future_growth_2` only.
- Six official Greenwich brownfield records researched: three eligible, one held because both official geometry and point are empty, one held because the official notes say `Started`, and one historical completed record excluded.
- Exact repository searches for all six entity/reference pairs returned no prior candidate match.
- Point evidence is a candidate locator, not a site boundary, and remains capped at 65 after exact point-in-polygon.
- The Sorting Office (`RBG-101`) has no usable official spatial locator and remains held with cap 0.
- Former Greenwich District Hospital (`RBG-03`) remains held for commencement ambiguity; its experimental alternative-source polygon is diagnostic-only and cannot be promoted.
- Former Royal Military Academy (`RBG-04`) is excluded with official end date `2018-12-17` and completion evidence.
- Greenwich provider quality reports `4/18` authoritative datasets, `1` URL error, `7` datasets that can improve and a Brownfield endpoint `404`; this is a quality warning with no confidence uplift.
- Wave registry/spatial validation: `12/12 PASS`.
- Missing spatial locator guard: `8/8 PASS`.
- Commencement ambiguity guard: `8/8 PASS`.
- Provider endpoint error/no-uplift guard: `8/8 PASS`.
- New executable controls: `36/36 PASS`; remote official evidence/API/HMLR audit: `14/14 PASS`.
- Direct `period=current` responses, actual HMLR downloads, exact intersections, real shard exports, product parcel matches and product scores remain `0`.
- `final_ready=false`.
