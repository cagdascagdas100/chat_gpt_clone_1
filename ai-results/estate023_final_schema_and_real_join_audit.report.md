# Estate023 Final Schema And Real Join Audit

DB_WRITE=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false

existing_join_valid=False
existing_join_valid_rows=0
existing_join_reason=wrong_schema
existing_coverage_valid=False
existing_coverage_valid_rows=0
existing_coverage_reason=no_valid_coverage_rows

strict_join_rows=0
strict_coverage_rows=0
REAL_100=false
REAL_COMPLETION_PERCENT=99

remaining_for_true_100:
- strict join rows must be > 0
- strict coverage rows must be > 0
- explicit human acceptance
- explicit DB import approval
- explicit production deploy approval

diagnostics:
- estate023_final_schema_audit.csv
- estate023_parcel_join_diagnostics.csv
- estate023_agent_coverage_diagnostics.csv
