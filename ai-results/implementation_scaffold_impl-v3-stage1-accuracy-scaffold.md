# Implementation Scaffold

Time: 2026-05-14 17:47:26

## Target

Move from report/matrix completion to actual implementation planning.

## Product-Level Work Items

1. Source confidence scoring
2. Parcel precision/recall test set
3. Join key / parcel ID normalization
4. Review queue validation cases
5. Keep V2 safe queue as automation control path

## Safe Implementation Constraint

No prod deploy.
No migration apply.
No secret write/update.
No production DB write/DDL/index.

## Proposed File Targets

These should be inspected before modification:

- app/etl/
- app/etl/match/
- app/api/
- tests/
- quality_reports/
- ai-results/

## Next Task

implementation_test_plan
