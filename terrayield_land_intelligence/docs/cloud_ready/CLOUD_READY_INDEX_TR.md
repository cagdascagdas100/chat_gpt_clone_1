# TerraYield AI Cloud Ready Index

Bu indeks, cloud/free-tier hazirlik islerinin kanit dosyalarini tek yerden gosterir.

## Guncel siniflandirma

`CLOUD_READY_PENDING_PROVIDER`

## Neden pending?

- Public hosted API URL henuz dogrulanmadi.
- Cloud DB provider ayari henuz dogrulanmadi.
- Son basarili runtime smoke local `127.0.0.1` uzerinden geldi.

## Repo tarafinda tamamlananlar

- `Dockerfile.cloud`
- `render.example.yaml`
- `.env.cloud.example`
- `scripts/cloud_smoke_check.py`
- `docs/cloud_ready/STATUS.md`
- `docs/cloud_ready/PROVIDER_CHECKLIST_TR.md`
- `docs/cloud_ready/HOSTED_SMOKE_USAGE_TR.md`
- `docs/cloud_ready/FINAL_CLOUD_READY_CLOSURE_TR.md`
- `.github/workflows/terrayield-cloud-readiness.yml`

## Kontrol dosyalari

- `docs/chatgpt_handoff/cloud_ready_20260517/EXECUTION_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/BLOCKERS.md`
- `docs/chatgpt_handoff/cloud_ready_20260517/LOCATION_EVIDENCE_SAMPLE.jsonl`
- `docs/chatgpt_handoff/cloud_ready_20260517/PERF_SUMMARY.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/SAFETY_SUMMARY.txt`

## Tek sonraki aksiyon

`ADD_PROVIDER_PUBLIC_URL_AND_CLOUD_DB_SETTINGS_OUTSIDE_REPO`

## Public smoke komutu

Public HTTPS backend URL olusunca:

```powershell
$env:TERRAYIELD_PUBLIC_API_URL="https://YOUR_PUBLIC_API_HOST"
python terrayield_land_intelligence/scripts/cloud_smoke_check.py
```

Basarili olursa hedef siniflandirma:

`CLOUD_RUNTIME_READY` veya free-tier sinirlari kabul edilirse `FREE_TIER_BEST_EFFORT_READY`

## Guvenlik

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
