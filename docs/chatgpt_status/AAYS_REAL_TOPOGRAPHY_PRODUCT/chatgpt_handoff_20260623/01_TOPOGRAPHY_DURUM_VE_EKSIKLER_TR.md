# Topography Durum ve Eksikler - 2026-06-23

## 1. Codex tarafinda tamamlananlar

| Konu | Durum | Kanit |
|---|---|---|
| Local app open | PASS | `http://127.0.0.1:8010/england_map_web/` -> 200 |
| Local topography lookup route | PASS | `http://127.0.0.1:8010/topography/lookup?parcel_id=29759443` -> 200 |
| Static frontend contract | PASS | `england_map_web\static\js\app.js` icinde `normalizeTopographyLookupForPopup`, `buildTopographyPopupRowsHtml`, `hight_differance.png` |
| Backend lookup contract | PASS | `terrayield_land_intelligence\app\api\routes\topography_lookup_v2.py` |
| Canonical local final report | PASS | `pb_runtime_finalization_single_runner_20260617T000000Z.txt` |
| Canonical local final status | PASS | `pb_runtime_finalization_single_runner_20260617T000000Z.status.txt` |

## 2. Hala eksik veya ayri takip edilmesi gerekenler

### 2.1 Remote branch sync eksigi

- Local final report 100 oldu.
- Ama finalizer icindeki push denemesi `non-fast-forward` ile reddedildi.
- Yani local dogrulama tamam, GitHub branch senkronu tamam degil.

### 2.2 England-wide veri kapsami eksigi

Codex tarafinda su yol varliklari kontrol edildi:

- `D:\AAYS_DATA\topography\england\raw` -> kanitli degil
- `D:\AAYS_DATA\topography\england\tiles` -> kanitli degil
- `D:\AAYS_DATA\topography\england\processed` -> kanitli degil

Kanitli kalanlar:

- `D:\topografik_map\london\terrarium_tiles`
- `F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz`

Sonuc:

- Local acceptance, `London_only` coverage ile 100 oldu.
- Ama urun seviyesinde England-wide kapsam hala tamam kanitlanmis degil.

### 2.3 Parcel veri dolulugu eksigi

Sample lookup:

- `parcel_id=29759443`

Endpoint artik 200 donuyor ama veri su bicimde donebilir:

```json
{
  "parcel_id": "29759443",
  "center_elevation_m": null,
  "region_average_elevation_m": null,
  "elevation_difference_from_region_average_m": null,
  "status": "no_data"
}
```

Bu su anlama gelir:

- route ayakta
- contract dogru
- ama veri dolulugu parceller icin tam degil

### 2.4 Manuel UI smoke eksigi

Static contract ve endpoint var.
Ama su kabul halen manuel UI smoke gerektirir:

- haritada parsel sec
- topography panel veya popup ac
- alanlarin sag panelde gozukmesi
- `no_data` durumunun kullaniciya anlamli gosterilmesi

### 2.5 Naming debt / page-key kirliligi

Topography page-key altinda canonical final dosyalari `pb_*` isimleriyle duruyor:

- `pb_runtime_finalization_single_runner_20260617T000000Z.txt`
- `pb_runtime_finalization_single_runner_20260617T000000Z.status.txt`

Bu teknik olarak calisiyor ama temiz mimari degil.

## 3. ChatGPT'ye verilebilecek isler

- bu eksiklerin operator odakli checklist'e cevrilmesi
- remote sync icin guvenli karar agaci
- England-wide veri kapsami icin dosya/folder manifesti
- UI manual smoke checklist
- kullanici tarafinda calistirilacak PowerShell script metinleri

## 4. ChatGPT'nin yapamayacagi ve local operator/Codex gerektiren isler

- F worktree icindeki gercek dosya varliklarini okumak
- 8010 runtime'i gercekten kaldirmak
- git divergence'i gercek branch durumuna gore cozmek
- D/F disklerinde gercek veri coverage auditini canli calistirmak
- browser uzerinde gercek parcel click smoke'u yapmak
