# 162 — Parcel Label / Distance Property Types — Tüm Satırların Site Görünürlüğü Düzeltme Raporu

## Amaç

Parcel Label / Distance Property Types sayfasında yalnızca 6 pilot satır görünmektedir. Hazırlanan gerçek internet-kaynak adayları, kaynak URL’leri, yerel kaynak/rapor/payload/queue yolları ve yeni-batch işaretleri kullanıcıya satır satır gösterilmelidir.

Bu görev veri üretimi görevi değildir. Önce mevcut 6 görünür satır + 92 hazırlanmış satırın dürüst durumlarıyla birlikte web arayüzünde görünmesi sağlanmalıdır. Bu düzeltme tamamlanmadan yeni aday batch’i oluşturulmayacaktır.

## Mevcut kanıtlı durum

- Canonical runner: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`
- Branch: `codex/aays-single-runner-v5-20260706`
- Runner self-test: PASS, PID/lock/heartbeat `24020`
- Site: `http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable`
- Mevcut görünür gerçek satır: `6`
- Önceden hazırlanmış bekleyen satır: `88`
- Task 161 yeni bekleyen satır: `4`
- Toplam izlenen satır: `98`
- Pending toplam: `92`
- Bulk completed: `0`
- `final_ready=false`
- `fake_data=false`

## Ekran görüntüsünde tespit edilen problemler

1. Üst özet yalnızca `Görünür satır: 6` gösteriyor; hazırlanmış 92 aday satır tabloda görünmüyor.
2. `Blocker: 88_prepared_rows_are_not_completed_without_real_runner_output` mesajı var, fakat bu 88 satırın kendisi incelenemiyor.
3. Task 161 ile eklenen 4 yeni aday hiç görünmüyor.
4. Üst bölümde `GeoJSON feature: not_available` ve `source_url: not_available` yazıyor; satır bazında kaynak URL’leri mevcut olmasına rağmen özet yanlış/eksik görünüyor.
5. Eski pilot satırlar `YENİ / LATEST` işareti taşıyor. Bu işaret yalnız son batch’te değişen satırlarda bulunmalı.
6. Kaynak URL, yerel kaynak dosyası, rapor, payload, queue task, evidence/GeoJSON ve runner output yolları tek yerde açık biçimde gösterilmiyor.
7. Hazırlanmış satırlar ile gerçekten tamamlanmış görünür satırlar için ayrı durum semantiği yok.
8. Tablo çok sıkışık; uzun yollar ve kanıt metinleri okunamıyor. Yatay kaydırma olsa da satır bazında kaynak incelemesi zor.
9. Son batch, bekleyen, manuel inceleme ve reddedilen satırlar için filtre yok.
10. Kullanıcı, yapılan son işlemleri önceki satırlardan ayırt edemiyor.

## Zorunlu veri modeli

Her satır aşağıdaki alanları sağlamalıdır:

- `batch_id`
- `task_id`
- `candidate_status`
- `changed_in_latest_run`
- `change_reason`
- `parcel_id`
- `name` veya `parcel_ref`
- `selected_property_type`
- `selected_color_category`
- `accuracy_score_4`
- `accuracy_label_4`
- `geometry_status`
- `selected_match_distance_m`
- `official_source_evidence`
- `web_source_evidence`
- `map_source_evidence`
- `photo_ai_evidence`
- `source_url`
- `source_date`
- `local_source_path`
- `report_path`
- `payload_path`
- `queue_task_path`
- `evidence_path`
- `runner_output_path`
- `completed_status_path`
- `last_updated`

Bir dosya indirilmemişse boş bırakılmamalı; açıkça `REMOTE_ONLY_NOT_DOWNLOADED` yazılmalıdır.

## Durum sözleşmesi

- `VISIBLE_PILOT_SOURCE_BACKED`: Mevcut 6 pilot satır; kaynak-backed fakat geometry/distance final değil.
- `PREPARED_PENDING_RUNNER`: Payload ve queue mevcut, gerçek runner output bekliyor.
- `NEW_PREPARED_PENDING_RUNNER`: Son batch’e ait yeni hazırlanmış satır.
- `NEEDS_MANUAL_REVIEW`: Runner doğrulaması yetersiz veya çelişkili.
- `REJECTED_BY_RUNNER`: Kaynak, adres veya geometri kabul edilmedi.
- `COMPLETED_VISIBLE`: Yalnız gerçek runner output + source evidence + site görünürlüğü birlikte kanıtlanırsa.

`PREPARED_PENDING_RUNNER` satırlar tabloda görünmelidir ancak completed/görünür tamamlanmış sayısına eklenmemelidir.

## Zorunlu site artifact’ları

Aşağıdaki ayrım korunmalıdır:

1. `england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json`
   - Yalnız gerçekten görünür/kabul edilmiş satırlar.
   - Şu an 6 satır.

2. `england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json`
   - 6 görünür + 92 pending dahil tüm izlenen satırlar.
   - Beklenen toplam: 98.

3. `england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json`
   - `total_tracked_count`
   - `completed_visible_count`
   - `visible_pilot_count`
   - `pending_runner_count`
   - `manual_review_count`
   - `rejected_count`
   - `latest_batch_count`
   - `blocker`
   - safety flags

4. `england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json`
   - Yalnız son batch/task değişiklikleri.
   - Task 161 için beklenen 4 satır.

5. `england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json`
   - Her satır için remote URL + yerel kaynak/rapor/payload/queue/evidence/output yolları.

## Arayüz gereksinimleri

### Özet kartları

- Toplam izlenen: `98`
- Görünür pilot: `6`
- Completed visible: `0`
- Pending runner: `92`
- Latest batch: `4`
- Manual review: `0` veya gerçek değer
- Rejected: `0` veya gerçek değer
- `final_ready=false`
- `fake_data=false`

### Filtreler

- Tümü
- Görünür pilot
- Completed visible
- Pending runner
- Son batch
- Manuel inceleme
- Reddedilen

### Satır görsel işaretleri

- Son batch: mavi `YENİ / TASK 161`
- Pending: amber `PENDING RUNNER`
- Completed: yeşil `COMPLETED VISIBLE`
- Review: mor `MANUAL REVIEW`
- Rejected: kırmızı `REJECTED`

Eski 6 pilot satırın `changed_in_latest_run` alanı `false` yapılmalıdır. Yalnız task 161’in dört satırı `true` kalmalıdır.

### Kaynak ve dosya yolları

Her satırda:

- `Kaynağı aç` — remote `source_url`
- `Kaynak yolunu kopyala`
- `Rapor yolunu kopyala`
- `Payload yolunu kopyala`
- `Queue yolunu kopyala`
- `Evidence yolunu kopyala`
- `Runner output yolunu kopyala`

Tarayıcı yerel dosyayı açamıyorsa yol yine görünür ve kopyalanabilir olmalıdır.

### Okunabilirlik

- İlk sütunlar sticky olmalı: durum, parsel/ad, mülk tipi, doğruluk.
- Uzun metinler hücre içinde kısaltılmalı; tıklanınca satır detay paneli açılmalı.
- Detay panelinde tüm kaynak kanıtları ve yollar eksiksiz gösterilmeli.
- Pagination 25 veya 50 satır olabilir.

## Veri birleştirme talimatı

- `docs/chatgpt_status/aays1/inputs/136...157...` payload’ları ve task 161 payload’ı okunmalıdır.
- Aynı `parcel_id` tekrar eklenmemelidir.
- 6 pilot satır mevcut verified CSV/GeoJSON’dan alınmalıdır.
- 88 eski hazırlanmış + 4 task 161 satırı pending olarak all-rows artifact’ına eklenmelidir.
- Kaynak doğrulanmamışsa satır silinmemeli; `NEEDS_MANUAL_REVIEW` veya `PREPARED_PENDING_RUNNER` olarak gösterilmelidir.
- `COMPLETED_VISIBLE` üretmek için completed status ve runner output path zorunludur.

## Browser kabul testleri

Gerçek Chrome/Selenium ile aşağıdakiler doğrulanmalıdır:

1. Parcel Label seçildiğinde toplam izlenen `98` görünür.
2. `Tümü` filtresi 98 satırı sayfalar halinde gösterir.
3. `Görünür pilot` filtresi 6 satır gösterir.
4. `Pending runner` filtresi 92 satır gösterir.
5. `Son batch` filtresi task 161’e ait 4 satırı gösterir.
6. Task 161 satırları farklı rozet ve arka planla ayırt edilir.
7. Her task 161 satırında source URL, payload path ve queue task path görünür.
8. Eski 6 pilot satır `YENİ/LATEST` olarak işaretlenmez.
9. Üst özet `source_url: not_available` demez; source manifest/remote source count gösterir.
10. Console error yoktur.
11. `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false` korunur.

## Çıktı ve kanıt dosyaları

Codex/runner aşağıdakileri üretmelidir:

- `docs/chatgpt_status/aays1/status/162_aays1_parcel_label_pending_rows_site_visibility_fix_20260711_completed.json`
- `docs/chatgpt_status/aays1/runner_outputs/162_aays1_parcel_label_pending_rows_site_visibility_fix_20260711_output.json`
- `docs/chatgpt_status/aays1/reports/162_parcel_label_pending_rows_site_visibility_fix_completion_report_20260711.md`
- Güncellenmiş site artifact’ları
- Chrome/Selenium browser proof JSON

## Güvenlik ve doğruluk kuralları

- Yeni veya paralel runner açma.
- Yalnız mevcut canonical shared runner kullan.
- Sahte completed/status/output üretme.
- 92 pending satırı completed olarak sayma.
- Kaynak ve geometri doğruluğunu olduğundan yüksek gösterme.
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`

## Devam kapısı

Yeni internet-kaynak aday üretimi yalnız şu üç kanıt birlikte oluştuğunda devam edecektir:

1. 162 completed status,
2. all-rows/status/latest-changes/source-manifest artifact’ları,
3. Chrome/Selenium testinde 98 total / 6 visible pilot / 92 pending / 4 latest doğrulaması.
