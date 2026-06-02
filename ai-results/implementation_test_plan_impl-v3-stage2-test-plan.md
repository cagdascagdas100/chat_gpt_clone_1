# Implementation Test Plan

Time: 2026-05-14 18:18:54

## Tests To Add

### Source Confidence Scoring

- Reject high confidence when source_url is missing.
- Cap confidence when parcel-specific spatial match is missing.
- Preserve fixture/stub shape while preventing high confidence.

### Parcel Matching

- Build positive/negative sample set.
- Measure precision and recall.
- Flag ambiguous join keys.

### Operational Health

- Confirm V2 queue path.
- Confirm current-task.json ignored by safe automation.
- Confirm result generation.

## Expected Completion After This Stage

95%.
