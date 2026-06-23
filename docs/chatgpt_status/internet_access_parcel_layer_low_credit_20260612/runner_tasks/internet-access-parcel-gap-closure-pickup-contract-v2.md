# Runner Pickup Contract v2

Page key: internet_access_parcel_layer_low_credit_20260612
Task: internet-access-parcel-gap-closure

Use only the existing single shared runner. Do not start another runner.

Input files:

- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/queue/internet-access-parcel-gap-closure-runner-task.json
- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/current-task/internet-access-parcel-gap-closure-current-task.json
- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/control/internet-access-parcel-gap-closure-control.json

Automation script:

- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/internet-access-parcel-gap-closure.ps1

Required outputs:

- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/status/internet-access-parcel-gap-closure-runner-status-YYYYMMDD-HHMMSS.json
- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/status/internet-access-parcel-gap-closure-heartbeat-YYYYMMDD-HHMMSS.json
- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports/internet-access-parcel-gap-closure-runner-output-YYYYMMDD-HHMMSS.md
- docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/runner_tasks/internet-access-parcel-gap-closure-next-safe-parallel-tasks-YYYYMMDD-HHMMSS.json

Safe parallel groups:

- read-only inventory
- factor contract validation
- endpoint read-only probe

Serialized groups:

- heavy dataset build
- import only after gates open
- browser smoke only after endpoint has non-empty parcel features

Final ready is forbidden until real renderable parcel geometry and non-empty endpoint/browser evidence exist.
