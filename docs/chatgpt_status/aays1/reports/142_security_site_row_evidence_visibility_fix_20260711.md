# AAYS1 Security / Public Safety — Satır Bazlı Kaynak, Kanıt ve Yeni-Batch Görünürlüğü Düzeltme Raporu

Tarih: 2026-07-11
Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `codex/aays-single-runner-v5-20260706`
Page key: `aays1`
Öncelik: 1

## Amaç

Security / Public Safety katmanında mevcut ve yeni üretilen gerçek verilerin kullanıcı tarafından web sitesinde satır satır görülebilmesini sağla. Her satırda resmi internet kaynağı, repo/local artifact yolları, kanıt dosyaları ve batch durumu açıkça görünmelidir. Yeni eklenen satırlar eski satırlardan güvenilir biçimde ayrılmalıdır.

Bu görev yalnız görünürlük ve kanıt sunumu düzeltmesidir. Yeni/paralel runner açma. Mevcut tek canonical runner kullanılacak. `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false` korunacak.

## Kullanıcı ekranında doğrulanan problemler

1. Sayfa `Görünür satır: 150` gösteriyor; ancak `GeoJSON feature: not_available` yazıyor.
2. Tüm eski 150 satır `YENİ / LATEST` ve `Son çalışmada değişti=True` görünüyor. Bu nedenle gerçekten yeni eklenen batch ayırt edilemiyor.
3. Satır tablosu resmi kaynak URL'sini göstermiyor; yalnız üst özet alanında `https://data.police.uk/` düz metin olarak bulunuyor.
4. Satır bazında CSV, GeoJSON, kanıt manifesti ve rapor yolları ayrı ve tıklanabilir olarak sunulmuyor.
5. `Yerel kaynak dosyası` kolonu tüm satırlarda yalnız top-level CSV yolunu tekrar ediyor; satırdaki `source_path`, `evidence_path`, `report_path` alanları tabloya bağlanmamış.
6. Kaynak ve artifact yolları düz metindir; HTTP 200 doğrulamalı tarayıcı bağlantıları yoktur.
7. `report_path` satırlarda `docs/chatgpt_status/aays1/reports/141_security_site_visibility_and_runner_recovery_result.md` değerini taşıyor, fakat bu dosya ilgili branch'te bulunmuyor. Eksik kanıt yolu kullanıcıya geçerliymiş gibi gösterilmemeli.
8. Yeni batch sayısı, önceki toplam, mevcut toplam, batch kimliği ve batch zamanı sayfada yoktur.
9. Kaynak verinin 150 CSV satırı ve 150 GeoJSON feature içerdiği status dosyasında mevcut olmasına rağmen özet sayacı yanlış alandan okuyor.

## Kod seviyesinde tespit edilen kök nedenler

### 1. GeoJSON sayaç alanı yanlış okunuyor

Dosya:
`england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`

Mevcut `renderSummary()` yalnız şunları okuyor:

- `d.geojson_feature_count`
- `s.geojson_feature_count`

Security status sözleşmesi ise `verified_geojson_features: 150` kullanıyor. Bu yüzden ekranda `not_available` çıkıyor.

### 2. Satır hücreleri bağlantı üretemiyor

`renderRows()` tüm değerleri `esc(...)` ile düz metin hücreye basıyor. `source_url`, `source_path`, `evidence_path` ve `report_path` için link renderer yok.

### 3. Security kolon sözleşmesi satır bazlı artifact alanlarını kullanmıyor

Security config içinde kaynak kolonu `$source_csv` üzerinden top-level JSON değerini her satırda tekrar ediyor. Satırdaki şu gerçek alanlar kullanılmıyor:

- `source_url`
- `source_path`
- `evidence_path`
- `report_path`
- `candidate_status`
- `ai_assurance_result`

### 4. Yeni satır işareti kalıcı boolean'a bağlı

`statusBadge()` ve `rowClass()` yalnız `changed_in_latest_run` alanını kullanıyor. Mevcut 150 satırın tamamında bu alan `True`; dolayısıyla tüm geçmiş satırlar sürekli yeni görünüyor.

### 5. Kanıt yolu varlık kontrolü yapılmıyor

Sayfa bir repo/local yolunu göstermeden önce HTTP veya manifest varlık kontrolü yapmıyor. Eksik rapor yolu normal içerik gibi sunuluyor.

## Zorunlu veri sözleşmesi

`security_public_safety_visible_rows.json` top-level alanlarına aşağıdakileri ekle veya eşdeğer kanıtlanabilir alanlarla uygula:

- `previous_visible_rows_count`
- `visible_rows_count`
- `new_rows_in_latest_batch`
- `latest_batch_id`
- `latest_batch_created_at`
- `latest_batch_source_date`
- `verified_geojson_features`
- `verified_csv_rows`
- `source_manifest_path`
- `latest_report_path`
- `latest_runner_output_path`

Her satırda aşağıdaki alanlar bulunmalı:

- `parcel_id`
- `batch_id`
- `first_seen_at`
- `last_verified_at`
- `is_new_in_latest_batch` — boolean
- `changed_in_latest_run` — yalnız gerçekten bu batch'te değişen satır için true
- `source_url`
- `source_date`
- `source_geography_level`
- `official_source_evidence`
- `source_path`
- `evidence_path`
- `report_path`
- `source_manifest_path`
- `accuracy_score_4`
- `accuracy_label_4`
- `confidence_score`
- `spatial_score`
- `needs_manual_review`
- `candidate_status`

Eski 150 satır toplu olarak `changed_in_latest_run=true` bırakılmamalı. Son başarılı batch'ten önce gelenler `is_new_in_latest_batch=false` ve uygun biçimde `KAYNAKLI / MEVCUT` gösterilmelidir.

## Zorunlu UI düzeltmeleri

### Özet metrikleri

Security seçildiğinde üst alanda en az şunları göster:

- Toplam görünür satır
- Doğrulanmış CSV satırı
- Doğrulanmış GeoJSON feature
- Son batch'te eklenen yeni satır
- Önceki toplam → yeni toplam
- Son batch kimliği ve zamanı
- Manuel inceleme sayısı
- Blocker
- `final_ready`
- `fake_data`

GeoJSON feature sayısı için fallback sırası en az şu alanları kapsamalı:

1. `d.verified_geojson_features`
2. `s.verified_geojson_features`
3. `d.geojson_feature_count`
4. `s.geojson_feature_count`

### Satır kolonları

Security tablosuna şu kolonları ekle veya mevcut kolonları dönüştür:

- Durum: `YENİ BATCH`, `GÜNCELLENDİ`, `KAYNAKLI / MEVCUT`, `MANUEL İNCELEME`, `BLOCKED`
- Batch ID
- İlk görülme zamanı
- Son doğrulama zamanı
- Resmi kaynak URL — tıklanabilir
- Resmi kaynak kanıtı
- CSV artifact — repo yolu + tıklanabilir HTTP URL
- GeoJSON/kanıt artifact — repo yolu + tıklanabilir HTTP URL
- Manifest — repo yolu + tıklanabilir HTTP URL
- Rapor — repo yolu + tıklanabilir HTTP URL
- Kaynak varlık durumu: `HTTP 200`, `MISSING`, `NOT_CHECKED`
- Doğruluk ve güven

### Link güvenliği ve erişilebilirlik

- Ham `file://` veya `F:\...` URL'sini link olarak kullanma.
- Portable/local yol metin olarak ve kopyalanabilir gösterilebilir.
- Tıklanabilir linkler `http://127.0.0.1:8012/...` altında browser-safe route olmalıdır.
- Resmi internet kaynağı `https://data.police.uk/` ayrı tıklanabilir external link olmalıdır.
- Link text yolun tamamını göstermeli veya tooltip/copy düğmesi sağlamalıdır.
- Eksik artifact `MISSING` olarak kırmızı görünmeli; geçerliymiş gibi link verilmemelidir.

### Yeni batch görünümü

- Yalnız `row.batch_id === data.latest_batch_id` ve `is_new_in_latest_batch === true` olan satırlar yeşil `YENİ BATCH` görünümünde olmalı.
- Son batch'te değişen fakat yeni olmayan satırlar ayrı `GÜNCELLENDİ` stili almalı.
- Eski doğrulanmış satırlar nötr `KAYNAKLI / MEVCUT` stili almalı.
- Arama alanına ek olarak `Yalnız yeni batch`, `Yalnız eksik kanıt`, `Yalnız manuel inceleme` filtreleri eklenmeli.

## Eksik rapor yolu düzeltmesi

Mevcut satırların işaret ettiği fakat bulunmayan yol:

`docs/chatgpt_status/aays1/reports/141_security_site_visibility_and_runner_recovery_result.md`

İki kabul edilebilir çözümden birini uygula:

1. Gerçek, kanıtlı içeriğe sahip raporu bu yolda oluştur ve HTTP 200/browser erişimini doğrula; veya
2. Satırları mevcut gerçek rapor yoluna güncelle.

Sahte/boş rapor üretme. Rapor; kaynak satır sayısını, GeoJSON feature sayısını, browser testini, commit SHA'yı ve safety flag'lerini içermelidir.

## Browser/Selenium kabul testleri

Aşağıdaki kontroller gerçek Chrome/Selenium ile geçmeden görev tamamlanmış sayılmayacak:

1. Security katmanı açılır.
2. `Görünür satır = 150` mevcut baseline için doğru görünür.
3. `GeoJSON feature = 150` görünür; `not_available` görünmez.
4. Baseline 150 satırın tamamı `YENİ/LATEST` görünmez.
5. Son batch yeni satırı yoksa `Yeni batch satırı = 0` görünür.
6. Yeni batch oluştuğunda yalnız yeni satırlar ayrı renkte ve `YENİ BATCH` badge'iyle görünür.
7. İlk örnek satırda resmi kaynak URL'si tıklanabilir.
8. CSV, GeoJSON, manifest ve rapor linklerinin her biri HTTP 200 veya açıkça `MISSING` döner.
9. Eksik rapor yoluna sahte link verilmez.
10. Sayfalama ile toplam 150 satır gezilebilir.
11. `Yalnız yeni batch` filtresi doğru sayıyı verir.
12. Browser console error sayısı 0'dır.
13. UTF-8 Türkçe metinler bozulmaz.

Browser proof dosyası:

`docs/chatgpt_status/_shared/reports/security_row_evidence_browser_validation_20260711.json`

## Runner output sözleşmesi

Çıktı oluştur:

`docs/chatgpt_status/aays1/runner_outputs/142_security_site_row_evidence_visibility_fix.json`

En az şu alanları içersin:

- `task_id`
- `status`
- `branch`
- `commit_sha`
- `runner_pid`
- `single_runner_only`
- `before_visible_rows`
- `after_visible_rows`
- `before_geojson_features`
- `after_geojson_features`
- `new_rows_in_latest_batch`
- `clickable_source_links_checked`
- `artifact_links_http_200`
- `artifact_links_missing`
- `all_old_rows_marked_latest` — false olmalı
- `browser_smoke_status`
- `console_error_count`
- `git_push_status`
- `remote_readback_status`
- `final_ready` — false
- `fake_data` — false
- `db_write` — false
- `migration` — false
- `production_deploy` — false

## İzin verilen ana dosyalar

- `england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`
- `england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json`
- `england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json`
- `england_map_web/data/security_public_safety/security_evidence_manifest.json`
- Gerçek Security CSV/GeoJSON artifact'ları
- `docs/chatgpt_status/aays1/reports/`
- `docs/chatgpt_status/aays1/runner_outputs/`
- `docs/chatgpt_status/_shared/reports/`

## Tamamlanma kriteri

Görev ancak aşağıdakilerin tümü gerçek kanıtla sağlandığında tamamlanır:

- GeoJSON sayacı 150 gösteriyor.
- Mevcut eski 150 satırın tamamı yanlış biçimde yeni görünmüyor.
- Satır bazında resmi kaynak ve yerel/repo artifact yolları görünür.
- Resmi URL ve geçerli artifact yolları tıklanabilir.
- Eksik yollar açıkça `MISSING` olarak işaretleniyor.
- Yeni batch satırları eski satırlardan farklı görünür.
- Browser/Selenium testi PASS.
- GitHub push ve remote readback PASS.
- Safety flag'leri false.

Bu düzeltme tamamlanıp remote readback doğrulandıktan sonra mevcut Security veri işi 151+ resmi/açık kaynak satır genişletmesinden devam edecektir.
