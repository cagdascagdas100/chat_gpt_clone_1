# Sold Buildings Status Endpoint Final Patch

status: FINAL_READY_DATA_GATE_BLOCKED
final_ready: True
production_complete: false
power_shell_required_from_user: false

checks: node_check=True | python_py_compile=True
markers: sold_icon=True | status_endpoint=True | backend_alias=True | accuracy_label=True

counts: official=106944 candidate=34 verified_rows=0 verified_parcels=0 unmatched=106910
gate: BLOCKED_MISSING_OFFICIAL_BRIDGE
