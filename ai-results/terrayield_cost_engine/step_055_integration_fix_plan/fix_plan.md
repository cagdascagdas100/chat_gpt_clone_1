# TerraYield Cost Engine 055 Integration Fix Plan

## Context
Step 053: engine exists and Python is found, but Python run was not OK.
Step 054: matrix completed with failures.

## Safe fix plan
1. Preserve no DB write, no migration, no secrets.
2. Capture exact Python stderr/stdout logs per failed case.
3. Validate UTF-8 handling for Turkish building_type values.
4. Validate subprocess invocation path quoting and output directory permissions.
5. Add deterministic unit test wrapper that imports estimate_cost directly before CLI mode.
6. Only after direct import succeeds, rerun CLI matrix.

## Next task
terrayield-cost-engine-056-direct-import-diagnostic

TASK_COMPLETION=100/100
