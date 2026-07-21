# Height Difference 1 revision 9 output-integrity gate

## Purpose

A terminal bridge marker or an existing JSON file is not sufficient evidence of a valid official parcel result. The revision 9 result must pass content, cross-artifact and row-level evidence checks before terminal or measured status is trusted.

## Gate

The validator requires:

- exact task ID, payload revision 9 and revision 9 attempt ID;
- all safety and deployment flags to remain false;
- runner-output and website-output SHA-256 equality;
- source-snapshot task, revision, accepted count and safety consistency;
- candidate and accepted-row counts to match the actual rows;
- every accepted row to contain official HMLR monthly bulk-GML geometry and source digest;
- every accepted row to contain a valid EA DTM 1 m polygon result and at least three pixels;
- parcel height difference to be a finite non-negative EA 1 m polygon maximum-minus-minimum value;
- every accepted row to contain an independent OS Terrain 50 check;
- no unresolved HMLR conflict or human-review flag;
- measured semantics and 3.5/4 accuracy only after all gates pass.

## Validation

- Synthetic and end-to-end tests passed: `23/23`.
- Valid measured output: accepted.
- Valid no-data output: terminal trust allowed but measured-row trust forbidden.
- Wrong identity, revision, attempt, safety flag, evidence, counts, status, hash or missing snapshot: rejected.

## Runtime state

The official revision 9 runner output is still absent, so the validator has not promoted any parcel measurement. The F portable recovery and runner must execute before the integrity readback can become verified.

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
