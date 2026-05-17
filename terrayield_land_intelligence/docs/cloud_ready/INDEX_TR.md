# TerraYield AI Cloud Ready Index

Bu indeks cloud-ready calismasinda olusan dosyalari ve mevcut durumu gosterir.

## Mevcut final durum

`CLOUD_READY_PENDING_PROVIDER`

## Tek sonraki aksiyon

`WAIT_FOR_USER_PROVIDER_DECISION`

## Neden pending?

- Public hosted HTTPS API URL dogrulanmadi.
- Cloud database provider ayari dogrulanmadi.
- En son basarili runtime smoke local `127.0.0.1` uzerinden geldi.
- 012A ve 012B runner raporlari henuz GitHub'a publish edilmedi.

## Ana dosyalar

### Runtime scaffold

- `Dockerfile.cloud`
- `render.example.yaml`
- `.env.cloud.example`
- `scripts/cloud_smoke_check.py`
- `scripts/validate_cloud_readiness_static.py`

### Cloud dokumantasyon

- `docs/cloud_ready/STATUS.md`
- `docs/cloud_ready/PROVIDER_CHECKLIST_TR.md`
- `docs/cloud_ready/HOSTED_SMOKE_USAGE_TR.md`
- `docs/cloud_ready/FINAL_CLOUD_READY_CLOSURE_TR.md`
- `docs/cloud_ready/STATIC_CLOUD_READINESS_VALIDATION_20260517.md`
- `docs/cloud_ready/FINAL_MANIFEST_20260517.json`
- `docs/cloud_ready/PARALLEL_EXECUTION_BOARD_20260517.md`
- `docs/cloud_ready/012AB_NOT_PUBLISHED_STATUS_20260517.md`

### ChatGPT/Codex handoff raporlari

- `docs/chatgpt_handoff/cloud_ready_20260517/EXECUTION_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/BLOCKERS.md`
- `docs/chatgpt_handoff/cloud_ready_20260517/LOCATION_EVIDENCE_SAMPLE.jsonl`
- `docs/chatgpt_handoff/cloud_ready_20260517/PERF_SUMMARY.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/SAFETY_SUMMARY.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/012C_GITHUB_NATIVE_STATUS_REPORT.txt`

### Beklenen ama henuz publish edilmeyen runner raporlari

- `docs/chatgpt_handoff/cloud_ready_20260517/012A_STATIC_CLOUD_READY_VALIDATE_REPORT.txt`
- `docs/chatgpt_handoff/cloud_ready_20260517/012B_LOCAL_TEST_SMOKE_PERF_REPORT.txt`

### GitHub Actions

- `.github/workflows/terrayield-cloud-readiness.yml`

Workflow dosyasi vardir; ancak connector uzerinden workflow run gorunmemistir. Bu nedenle statik dogrulama raporu ve 012C GitHub-native fallback raporu eklenmistir.

## Lokal statik kontrol

```powershell
python terrayield_land_intelligence/scripts/validate_cloud_readiness_static.py
```

Beklenen basarili cikti:

`STATIC_CLOUD_READINESS_VALID`

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

## Guvenlik

- Secret degeri yazdirilmaz.
- `.env` ve `.env.local` commit edilmez.
- DB write, DDL, migration apply ve prod deploy otomatik yapilmaz.
- Local `127.0.0.1` smoke public cloud kaniti sayilmaz.
