# Distance 047 in-repo repair bundle

Bu klasör, dış ZIP bağımlılığını kaldırmak için branch içine eklenmiştir.

Çalıştırma yeri:

```powershell
Set-Location "F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706"
git fetch origin aays-runner-v17-icon-work-20260603-232706
git pull --rebase --autostash origin aays-runner-v17-icon-work-20260603-232706
powershell -ExecutionPolicy Bypass -File "docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\automation\distance_047_repair_bundle\RUN_DISTANCE_047_REPAIR.ps1"
```

Script beklenen raporu şu dizine yazar:

```text
docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/terrayield_047_distance_property_types_apply_patch_smoke_<timestamp>.md
```

DB write/import/backfill yapmaz; sadece dar patch, static check, endpoint smoke ve rapor/status üretir.
