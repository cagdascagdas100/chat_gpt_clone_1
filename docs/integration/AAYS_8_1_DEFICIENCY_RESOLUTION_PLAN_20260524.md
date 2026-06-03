# AAYS 8.1 Gelisim - Eksiklik ve Sıkıntı Çözüm Planı

Tarih: 2026-05-24
Sayfa: 8.1 Gelisim
Kök/bridge: `C:\AAYS_GITHUB_BRIDGE_CLEAN2`
Uygulama repo kökü: `C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence`

## Amaç
Codex entegrasyonu sonrası kalan eksiklikleri güvenli şekilde çözmek ve kullanıcı sadece `devam et` diyerek takip edebilsin diye işi tek runner + queue-lock modeline almak.

## Tespit edilen eksiklikler

### 1. DEM raster dosyaları ortamda bulunamadı
Beklenen dosyalar:
- `E:\AAYS_DATA\elevation\copernicus_dem_glo30\Copernicus_DSM_COG_10_N51_00_W001_00_DEM.tif`
- `E:\AAYS_DATA\elevation\copernicus_dem_glo30\Copernicus_DSM_COG_10_N52_00_W001_00_DEM.tif`

Çözüm:
- Önce `E:\AAYS_DATA\elevation\copernicus_dem_glo30` klasörü kontrol edilir.
- Dosyalar yoksa gerçek Copernicus DEM S3 URL'lerinden yeniden indirme denenir.
- İndirme başarısızsa fake raster üretilmez; eksiklik rapora yazılır.

### 2. `git pull` yerel `ai-tasks/current-task.json` değişikliği yüzünden çakışabiliyor
Çözüm:
- Runner görevleri doğrudan `current-task.json` ezmeden `ai-queue/pending` altına alınır.
- Local taraf için öneri ayrı raporlanır; otomatik destructive git reset yapılmaz.

### 3. Runner/current-task senkron kayması görülebiliyor
Çözüm:
- Görev `ai-queue/pending` içine yazılır.
- `portable-runner.md`, `.last-task-id`, result dosyası ve current-task birlikte kontrol edilir.
- Aktif görev varsa üzerine yazılmaz.

## Güvenlik kuralları
- DB write kapalı kalacak.
- Production deploy yapılmayacak.
- Fake data/fake elevation üretilmeyecek.
- Tek runner + queue-lock korunacak.
- Başka sayfaların status satırı ve current-task'i ezilmeyecek.

## Uygulama görevi
Script:
- `ai-task-scripts/aays_8_1_deficiency_resolution_20260524.ps1`

Queue dosyası:
- `ai-queue/pending/8_1_deficiency_resolution_20260524.task.json`

Beklenen çıktı:
- `ai-results/aays_8_1_deficiency_resolution_20260524.result.json`
- `ai-results/aays_8_1_deficiency_resolution_20260524.report.md`
- `docs/integration/AAYS_8_1_DEFICIENCY_RESOLUTION_STATUS_20260524.md`

## Kapanış kriteri
- DEM dosyaları bulundu veya gerçek kaynaklardan indirildi; ya da eksiklik fake data üretmeden net raporlandı.
- DB write=false.
- production_deploy=false.
- fake_data=false.
- Kullanıcıya yalnızca genel ilerleme ve bekleme süresi verilecek.
