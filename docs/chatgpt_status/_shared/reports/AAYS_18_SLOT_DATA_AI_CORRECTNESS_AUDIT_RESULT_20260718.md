# AAYS 18 Slot Veri ve AI Doğruluk Denetimi

Tarih: 2026-07-18
Workstream: `AAYS_18_SLOT_SAFE_PARALLEL_V1`
Canonical portable root: `F:\TerraYield_AAYS_Portable`
Branch: `codex/aays-single-runner-v5-20260706`

## Sonuç

Altyapı ve güvenlik sözleşmesi çalışıyor, fakat ürün ve bütün İngiltere veri kapsamı final değildir.
18 sayfanın her biri `devam et` yazmış gibi in-memory dry-run edildi: 18/18 doğru slot kabul
edildi, 18/18 yanlış slot yolu reddedildi. Test gerçek queue veya business verisi yazmadı.

Gerçek uzak queue denetiminde yeni 18-slot v3 görevi yoktur. 18 slotun tamamı IDLE durumundadır.
Mevcut 204 eski queue JSON dosyasının hiçbirinde `slot_id` veya 18-slot `workstream_id` yoktur.
Dolayısıyla ChatGPT sayfaları henüz yeni sözleşmeyle gerçek görev yayımlamamıştır.

## Uygulama ve Kontrol Siteleri

- Ana uygulama: HTTP 200, `Great Britain Parcel Map` açıldı.
- Parsel katman matrisi: HTTP 200, gerçek kalite kapısı görünür.
- ReadyToSell AI/geometri sayfası: HTTP 200, `canonical_geometry`, `load_state=ready`.
- Matris: 92.283 Londra canonical satırı, 923 chunk, chunk başına 100 satır.
- 92.283 sayısı bütün İngiltere parsel toplamı değildir.
- `/health`: uygulama çalışıyor; database durumu `degraded` ve gerçek blocker olarak kalır.

## Gerçek Veri Örnekleri

### Parcel Label / Distance

- Manifestteki yanlış `92,283 feature` beyanı gerçek dosya sayısı olan 14'e düzeltildi.
- Ayrı durum dosyasında 198 izlenen satır ve 57 source-upgraded satır vardır.
- Örnek: Westfield London, Retail Property, kaynak URL mevcut, doğruluk 3/4.
- Sonuç: pilot veri; 92.283-parsel katmanı değildir.

### Height Difference / Topography

- 77.970 point feature vardır.
- Örnek `parcel_1`: deniz seviyesi 4.77 m, Londra örnek ortalamasına fark -41.31 m,
  doğruluk 2/4.
- EA LiDAR sayısal örneği 0, OS Terrain sayısal örneği 0, HMLR boundary match 0.
- Sonuç: proxy/fallback; resmi parcel elevation ölçümü değildir.

### Gas Emissions

- 3.533 point feature vardır; 100 resmi kaynak destekli görünür örnek satır vardır.
- Kaynak DESNZ local-authority greenhouse gas veri setidir.
- `parcel_binding_gate_passed=false`; kaynak yerel yönetim alanı seviyesindedir.
- Sonuç: `AREA_LEVEL_PROXY`; ölçülmüş parsel emisyonu değildir.

### Security / Public Safety

- 92.283 point feature görünür.
- 300 resmi kaynak destekli görünür satır ve 26 resmi API LSOA doğrulaması vardır.
- Örnek `parcel_1`: `Cok Dusuk; score=12.1`, doğruluk 2/4.
- Sonuç: LSOA proxy; 92.283 satırın tamamı parcel-level suç ölçümü değildir.

### Internet Access

- 33.785 postcode coverage eşleşmesi, 58.498 `NO_DATA` canonical satırı vardır.
- Çalıştırma testi 33.785 feature yükledi.
- Örnek `parcel_3 / RM82LL`: gigabit %100, UFBB %100, SFBB %100, unable30 %0.
- Sonuç: `POSTCODE_COVERAGE_PROXY_NOT_MEASURED_PARCEL_SPEED`.
- Arayüz artık olmayan fallback yerine mevcut matris verisini yükler ve ölçülmüş hız iddiası kurmaz.

### Planned Buildings

- Manifestteki yanlış 0 sayısı gerçek dosya sayısı 47'ye düzeltildi.
- Satırlar `CANDIDATE_NOT_PARCEL_MATCHED` ve manuel inceleme olarak kalır.

## AI Kontrolü

- Canonical geometri: 1.264/1.264, null geometri 0.
- Canlı kaynak sayfası doğrulanan: 911.
- Fotoğraf dosyası bulunan: 781.
- Poligon render dosyası bulunan: 782.
- Vision manifesti bulunan: 782.
- Üç kanıtı birlikte bulunan: 781.
- Gerçek `visual_match_score` bulunan: 0.
- Yanlış `VISION_COMPARED` işaretlenen: 0.
- `final_ready=false`.

AI sistemi kanıt hazırlama aşamasında fail-closed çalışmaktadır. Fotoğraf ve poligon dosyasının
varlığı AI görsel karşılaştırmasının yapıldığı anlamına gelmez. Gerçek skor ve karşılaştırma
çıktısı olmadan güven 3.5+ veya `vision compared` üretilemez.

## Uygulanan Koruma Önlemleri

1. Slot kimliği artık path substring ile değil tam path segmentiyle doğrulanır.
2. Yazma yalnız slotun canonical business/status/web köklerine yapılabilir.
3. `final_ready=true` taşıyan görev reddedilir.
4. Yeni 18-slot v3 görevinde `data_quality_contract` zorunludur.
5. Kaynak URL, kaynak tarihi, measurement level, parcel binding, confidence yöntemi,
   `NO_DATA_NOT_INFERRED`, AI rolü ve insan inceleme kuralı kaydedilir.
6. Kaynak araştırması bitmeden web yayını reddedilir.
7. Postcode/LSOA/local-authority/grid verisi parcel measurement olarak yayımlanamaz.
8. Kontrol sitesinde scope, kalite etiketi, measurement level ve AI vision sayısı görünür.
9. Program matrisi manifestindeki iki yanlış sayım ve C-hardcoded yollar düzeltildi.
10. Internet fallback gerçek 33.785 postcode kapsam satırını yükler; satış geçmişinden internet
    kalitesi üretmez ve ölçülmüş hız iddiası yazmaz.
11. 8012 health yanıtı geçici geciktiğinde portu yanlışlıkla başka servis sayan preflight hatası
    üç sınırlı yeniden deneme ve son port kontrolüyle düzeltildi.
12. Windows okuyucu kilidi `coordinator_status_latest.json` atomik replace işlemini engellediğinde
    daemon artık kontrollü retry ve fsync fallback uygular; hata daemon'u düşürmez.

## Portable Başlatma Doğrulaması

- Uygulama health: HTTP 200, TerraYield Land Intelligence, database `degraded`.
- 8012 preflight: PASS, `port_8012_state=TERRAYIELD_ACTIVE`.
- Koordinatör başlatma: PASS.
- Gözlenen canlı PID: 12064.
- 30 saniye canlılık testi: PASS; aynı PID ve yenilenen heartbeat.
- Temiz stop testi: PASS, `STOPPED_CLEAN`.
- Başlangıç/lock düzeltmelerinin remote implementation commit'i: `b99d659`.

## Test Sonuçları

- Python syntax/import: PASS.
- JavaScript syntax: PASS.
- JSON parse: PASS.
- 18-slot dry-run: PASS, 18 valid, 18 wrong-slot blocked.
- Incomplete-source web publish block: PASS.
- Non-parcel measured publish block: PASS.
- GeoJSON count/manifest integrity: PASS, hardcoded C path false.
- Browser smoke: 3/3 HTTP 200.
- Internet overlay smoke: PASS, 33.785 feature, proxy label present.
- Portable preflight with active 8012: PASS.
- Coordinator 30-second heartbeat persistence: PASS.
- Coordinator clean stop: PASS.
- Fake business data written: 0.

## Kalan Gerçek Blockerlar

- Ulusal bütün İngiltere canonical parsel envanteri kanıtlanmadı.
- ChatGPT sayfalarından gerçek 18-slot v3 queue görevi henüz gelmedi.
- AI gerçek visual comparison satırı 0.
- Topography resmi sayısal parcel doğrulaması yok.
- Gas emissions parcel binding yok.
- Security 92.283 satırın tamamında resmi kaynak doğrulaması yok.
- Internet için 58.498 canonical satır `NO_DATA`.
- Bu bilgisayar 7.31 GB RAM nedeniyle en fazla 5 child worker çalıştırır; 18 slot mantıksaldır,
  18 fiziksel worker aynı anda çalışmaz.
- Backend health database durumu `degraded`.

`final_ready=false`
`product_final_ready=false`
`fake_data=false`
`db_write=false`
`migration=false`
`production_deploy=false`
