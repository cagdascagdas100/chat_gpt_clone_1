# TerraYield AI Provider Checklist

Bu checklist public cloud'a gecis icin kalan dis-provider adimlarini netlestirir.

## Mevcut durum

- Local runtime API smoke gecti.
- Source-lineage guard testleri gecti.
- Cloud scaffold dosyalari repo'da var.
- Public hosted URL dogrulanmadi.
- Cloud DB provider dogrulanmadi.

## Provider tarafinda zorunlu adimlar

1. Managed Postgres/PostGIS servisi sec.
2. Provider panelinde database connection bilgisini secret olarak tanimla.
3. Backend hosting servisini Dockerfile.cloud ile bagla.
4. Backend public HTTPS URL al.
5. Frontend public URL olustur ve API base URL'yi backend public URL'ye yonlendir.
6. Hosted smoke calistir.

## Public smoke basari kriteri

Ayni public HTTPS base URL uzerinden su endpointler basarili olmali:

- `/`
- `/ops/storage-registry`
- `/ops/consistency-check`
- `/handoff/status`
- `/map/listings?limit=1`
- `/map/sales-history/combined?limit=1`

## Siniflandirma

- Public URL yoksa: `CLOUD_READY_PENDING_PROVIDER`
- Public URL var ama smoke gecmiyorsa: `BLOCKED`
- Public URL + hosted smoke gecerse: `CLOUD_RUNTIME_READY`
- Free-tier sinirlari kabul edilirse: `FREE_TIER_BEST_EFFORT_READY`

## Guvenlik

- Gercek secret degerleri repo'ya yazilmaz.
- `.env` ve `.env.local` commit edilmez.
- Prod deploy ve migration kullanici onayi olmadan yapilmaz.
