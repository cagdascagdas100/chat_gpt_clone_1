# Gas Emissions Local Runner Pickup Blocker

Status: BLOCKED_ON_LOCAL_RUNNER_PICKUP
Page key: gas_emissions
Branch: feature/terrayield-aays-integration

## Net durum

- Kullanıcı kabul metni veya manuel stdout yapıştırması gerekmiyor.
- GitHub tarafındaki görev/queue/runner task/finalizer dosyaları hazır.
- Yüzde artmamasının nedeni eksik ürün dosyası değil; local single shared runner/poller mevcut QUEUED işi çalıştırmıyor.
- Gerçek kabul seviyesi %89 olarak kalır; current-task hedefi %99 olsa da FINAL_READY için runtime evidence gereklidir.

## Çalışması gereken mevcut script

```text
docs/chatgpt_status/gas_emissions/automation/gas_emissions_single_runner_finalizer_20260622_2300.ps1
```

## Beklenen çıktı dosyaları

```text
docs/chatgpt_status/gas_emissions/status/gas_emissions_finalizer_status_20260622_2300.json
docs/chatgpt_status/gas_emissions/heartbeat/gas_emissions_finalizer_heartbeat_20260622_2300.json
docs/chatgpt_status/gas_emissions/reports/gas_emissions_finalizer_result_20260622_2300.md
```

## Kalan blocker

```text
single_shared_runner_pickup_execution_missing
```

## Gerekli aksiyon

Mevcut açık runner/poller bu page-key görevini alıp yukarıdaki finalizer script'i çalıştırmalı. GitHub dosyası eklemek tek başına lokal runner prosesini tetiklemez.
