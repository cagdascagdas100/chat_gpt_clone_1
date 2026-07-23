# height_difference_1 — Official public source refresh 065a

- continuation_key: `de3fdcae11ec08e51e5055d36a8e3e70241cc9429f6bcb03a77d08c8dbdadc33`
- generated_at: `2026-07-23T15:02:10Z`
- source candidates validated: **11**
- official source checks: **88/88**
- source upgrades added: **32**
- methodology upgrades added: **24**
- web operation rows staged: **176** (`16593-16768`)
- parcel candidates added: **0**
- measured height rows added: **0**

## Fresh official evidence

1. HM Land Registry INSPIRE is monthly, GML-based, freehold-only indicative geometry; cross-local-authority duplicates are explicitly possible.
2. Current INSPIRE download publication is dated **5 July 2026** and lists both **London Borough of Barnet** and **London Borough of Enfield**.
3. HM Land Registry technical guidance requires projection-aware GML handling.
4. Environment Agency Composite DTM 1m covers approximately **99% of England** and is the primary high-resolution terrain source in the current task contract.
5. Environment Agency 2m composite is same-family/resampled evidence and must not be counted as an independent survey.
6. Environment Agency time-stamped DTM provides survey epoch, OS Newlyn vertical reference, 25cm/50cm/1m/2m resolutions and **±15cm RMSE** metadata.
7. Environment Agency ground-truth surveys provide independently surveyed points with **±3cm RMSE** and explicit RMSE/standard-deviation/random-error validation semantics.
8. Defra Data Services Platform documents direct use of the 1m DTM WCS endpoint.
9. OS Terrain 50 is a current official coarse independent cross-check: **50m grid**, **4m RMSE**, annual July update.
10. OS Terrain 50 grid values are pixel-centre values, supplied to nearest 0.1m; this numeric precision must not be confused with 50m spatial resolution.
11. OS Data Hub reports the current Terrain 50 version as **July 2026**.

## Guardrail

This refresh advances source identity, freshness, provenance, datum/accuracy semantics and negative-use controls only. It does **not** promote any parcel match or height-difference result because the existing F-host still lacks the required noninteractive GitHub publish-auth preflight and the exact Revision 14 remote runtime/integrity outputs.

Missing remote outputs remain:

- `runner_outputs/027_noninteractive_publish_auth_preflight_latest.json`
- `runner_outputs/016_revision_14_direct_hmlr_monthly_gml_refresh_latest.json`
- `runner_outputs/025_revision_14_output_integrity_readback_latest.json`

No second runner or logical task was created.
