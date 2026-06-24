# Required Patch Targets

## 1. `england_map_web/internet_access_overlay.js`

Durum:
- route var
- layer source ids var
- proxy fallback artik varsayilan olarak kapali

Gerekli kalanlar:
- gerçek parcel geometry gelirse onu ciz
- factor table alanlarini popup veya panel tarafina tasiyacak contract'i netlestir
- `no data` ile `empty because DB missing` ayrimini daha net goster

## 2. `england_map_web/app.js`

Durum:
- Internet iconu ve runtime loader markerlari var

Gerekli kalanlar:
- right-side detail panel Internet contract alanlarini gormeli
- factor table panel baglantisi gerekli
- color category, source list, matching method, calculation explanation eksikse eklenmeli

## 3. `terrayield_land_intelligence/app/api/routes/map_layers.py`

Durum:
- `/map/internet-access` route var
- DB socket yoksa fail-soft bos koleksiyon donuyor

Gerekli kalanlar:
- parcel-level tablo veya join ile gercek geometry donmeli
- factor alanlari gerekirse JSON veya satir-gruplu output olarak genisletilmeli
- import-ready tablo adlari netlestirilmeli

## 4. Yeni local ETL / build script

ChatGPT'nin yazmasi beklenen muhtemel yeni dosyalar:
- `scripts/build_parcel_internet_dataset.py`
- `scripts/import_parcel_internet_dataset.ps1`
- `scripts/validate_parcel_internet_dataset.py`

## 5. Yeni manifest / schema dosyalari

- `manifests/parcel_internet_access_manifest.json`
- factor breakdown schema
- output contract schema

## 6. DokunulmamasI gerekenler

- `terrayield_land_intelligence/app/schemas/contractor.py` icindeki import fix
- Internet layer'in varsayilan `sales-history` proxy fallback'inin kapali kalmasi
