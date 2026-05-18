# TerraYield AI Cloud Ready Index

Bu indeks cloud-ready calismasinda olusan dosyalari ve mevcut durumu gosterir.

## Mevcut final durum

`CLOUD_READY_PENDING_PROVIDER`

## Tek sonraki aksiyon

`WAIT_FOR_USER_PROVIDER_DECISION`

## Neden pending?

- Public hosted HTTPS API URL dogrulanmadi.
- Cloud database provider ayari dogrulanmadi.
- Hosted smoke public URL uzerinden calistirilmadi.
- Public frontend runtime dogrulanmadi.
- Local kanitlar guncel ve basarili olsa da public cloud runtime kaniti sayilmaz.

## Tamamlanan local kanitlar

- 012A static validation: passed.
- 012B targeted pytest: passed.
- 014 local API smoke: passed 6/6.
- 014 local performance: passed.

## Ana dosyalar

### Runtime scaffold

- `Dockerfile.cloud`
- `render.example.yaml`
- `.env.cloud.example`
- `scripts/cloud_smoke_check.py`
- `scripts/validate_cloud_readiness_static.py`
- `scripts/validate_watchdog_readiness.py`

### Cloud dokumantasyon

- `docs/cloud_ready/STATUS.md`
- `docs/cloud_ready/PROVIDER_CHECKLIST_TR.md`
- `docs/cloud_ready/HOSTED_SMOKE_USAGE_TR.md`
- `docs/cloud_ready/FINAL_CLOUD_READY_CLOSURE_TR.md`
- `docs/cloud_ready/STATIC_CLOUD_READINESS_VALIDATION_20260517.md`
- `docs/cloud_ready/FINAL_MANIFEST_20260517.json`
- `docs/cloud_ready/CURRENT_STATUS_20260517.md`
- `docs/cloud_ready/CURRENT_STATUS_MACHINE_20260518.json`
- `docs/cloud_ready/GITHUB_ONLY_AUTONOMOUS_CLOSURE_CHECKLIST_20260518.md`
- `docs/cloud_ready/PARALLEL_EXECUTION_BOARD_20260517.md`
- `docs/cloud_ready/GITHUB_ONLY_COMPLETION_REPORT_20260518.md`
- `docs/cloud_ready/GITHUB_ONLY_AUTONOMOUS_SCOPE_MATRIX_20260518.md`
- `docs/cloud_ready/AUTONOMY_ESCALATION_PLAN_20260518.md`
- `docs/cloud_ready/EVIDENCE_INGESTION_PLAN_20260518.md`
- `docs/cloud_ready/CLASSIFICATION_UPDATE_PLAYBOOK_20260518.md`
- `docs/cloud_ready/CODEX_FIRST_NO_MANUAL_FILE_POLICY_20260518.md`
- `docs/cloud_ready/LONG_BATCH_PUBLIC_RUNTIME_PRECHECK_20260518.md`

### Watchdog / persistent runner katmani

- `docs/chatgpt_handoff/local_runner_queue/AAYS_LOCAL_RUNNER_WATCHDOG_SAFE.ps1`
- `docs/chatgpt_handoff/local_runner_queue/START_WATCHDOG_SAFE_ONCE.ps1`
- `docs/cloud_ready/PERSISTENT_RUNNER_UPGRADE_PACKAGE_20260518.md`
- `docs/cloud_ready/SAFE_RUNNER_TASK_PROTOCOL_20260518.md`
- `docs/cloud_ready/PERSISTENT_RUNNER_WATCHDOG_DESIGN_20260518.md`
- `docs/cloud_ready/WATCHDOG_RUNNER_USAGE_TR_20260518.md`
- `docs/cloud_ready/WATCHDOG_EVIDENCE_TEMPLATE_20260518.txt`
- `docs/cloud_ready/WATCHDOG_READINESS_CLOSURE_20260518.md`
- `docs/cloud_ready/RUNNER_REVIVAL_READY_20260518.md`

### Provider / hosted cloud katmani

- `docs/cloud_ready/PROVIDER_DECISION_PACKAGE_20260518.md`
- `docs/cloud_ready/FAST_PATH_DEPLOY_PLAYBOOK_TR_20260518.md`
- `docs/cloud_ready/PROVIDER_ENV_CHECKLIST_TR_20260518.md`
- `docs/cloud_ready/RUNTIME_PROOF_GAP_REGISTER_20260518.md`
- `docs/cloud_ready/HOSTED_SMOKE_RESULT_TEMPLATE_20260518.txt`

### ChatGPT/Codex handoff raporlari

- `docs/chatgpt_handoff/cloud_ready_20260517/EXECUTION_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/BLOCKERS.md`
- `docs/chatgpt_handoff/cloud_ready_20260517/LOCATION_EVIDENCE_SAMPLE.jsonl`
- `docs/chatgpt_handoff/cloud_ready_20260517/PERF_SUMMARY.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/SAFETY_SUMMARY.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/012C_GITHUB_NATIVE_STATUS_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/012A_STATIC_CLOUD_READY_VALIDATE_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/012A_STATIC_CLOUD_READY_VALIDATE_RAW.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/012B_LOCAL_TEST_SMOKE_PERF_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/012B_PYTEST_RAW.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/014_LOCAL_API_SMOKE_PERF_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/014_LOCAL_API_SMOKE_PERF_RAW.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/CODEX_CONTROL_NEXT_TASK_EXECUTION_REPORT_20260518.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/CODEX_CONTROL_NEXT_TASK_BLOCKERS_20260518.md`

### GitHub Actions

- `.github/workflows/terrayield-cloud-readiness.yml`

Workflow dosyasi vardir; connector uzerinden workflow run gorunmese de local ve direct PowerShell kanitlari publish edilmistir.

## Lokal statik kontrol

```powershell
python terrayield_land_intelligence/scripts/validate_cloud_readiness_static.py
python terrayield_land_intelligence/scripts/validate_watchdog_readiness.py
```

Beklenen basarili ciktilar:

- `STATIC_CLOUD_READINESS_VALID`
- `WATCHDOG_READY_FOR_MANUAL_ENABLEMENT`

## Hosted smoke kontrolu

Public URL olustuktan sonra:

```powershell
$env:TERRAYIELD_PUBLIC_API_URL="https://YOUR_PUBLIC_API_HOST"
python terrayield_land_intelligence/scripts/cloud_smoke_check.py
```

Hosted smoke 6/6 gecer ve cloud DB ayari dogrulanirsa siniflandirma `CLOUD_RUNTIME_READY` seviyesine cikarilabilir.

## Karar beklenen dis-provider alanlari

- Backend provider secimi
- Cloud DB/PostGIS provider secimi
- Frontend public hosting secimi
- Public backend HTTPS URL
- Hosted cloud smoke onayi

## GitHub-only / local evidence kapanis sonucu

Repo hazirligi, static validation, targeted pytest, local API smoke ve local performance kanitlari tamamlandi. Bu kanitlar public hosted runtime yerine gecmez.

## Guvenlik

- Secret degeri yazdirilmaz.
- `.env` ve `.env.local` commit edilmez.
- DB write, DDL, migration apply ve prod deploy otomatik yapilmaz.
- Local `127.0.0.1` smoke public cloud kaniti sayilmaz.
