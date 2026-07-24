# Topography / Height Difference — Güncel Sonuçların Site Satırlarında Görünmesi Düzeltme Raporu

Tarih: 2026-07-11
Page key: `topography`
Branch: `codex/aays-single-runner-v5-20260706`
Runner: mevcut tek shared runner; yeni/paralel runner açılmayacak.

## Kullanıcı ekranında doğrulanan problem

`Height Difference / Topography` seçildiğinde sayfa yalnızca eski koordinat handoff verisini gösteriyor:

- Başlık: `Height Difference / Topography - Koordinat Handoff`
- Data path: `data/program_layer_matrix/topography_coordinate_handoff_latest.json`
- Status: `same_data_or_not_required`
- Kaynak URL/CSV: `not_available`
- GeoJSON feature: `not_available`
- Satırlarda yalnız eski 140 raporu, koordinat ve `boundary_not_exported / dem_lidar_sampling_required` blocker bilgisi var.
- 153 boundary + DEM/LiDAR queue adımı görünmüyor.
- 154 Copernicus OData/geocell işlemi görünmüyor.
- `COP-DEM_GLO-30-DGED/2024_1`, `SAR_DGE_30_A4AD`, `N51_W001`, queue/status/report yolları ve işlem durumu görünmüyor.
- Yeni işlemler eski satırlardan görsel olarak ayrışmıyor.

## Kod kök nedeni

Dosya: `england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`

1. `topography` config eski artefakta sabitlenmiş:
   - data: `data/program_layer_matrix/topography_coordinate_handoff_latest.json`
   - status: `null`
   - rowsKey: `coordinates`

2. Güncel çalışma çıktısı olan
   `outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json`
   frontend veri zincirine bağlı değil.

3. `rowClass()` ve `statusBadge()` yalnız `row.blocker`, `needs_manual_review`, `changed_in_latest_run` alanlarına bakıyor. Şunları işlemiyor:
   - `display_badge`
   - `sampling_status`
   - `boundary_status`
   - `task_id`
   - global `blockers`
   - `height_source_discovery_status`

4. `renderSummary()` yalnız genel data/status yollarını gösteriyor; satır bazlı kaynak, rapor, status, queue, local indirme yolu ve commit kanıtını göstermiyor.

5. Mevcut source dosyası `topography_coordinate_handoff_latest.json` yalnız 140 koordinat raporunu içeriyor; sonraki 141–154 işlem zincirini içermez.

## Zorunlu düzeltme

### A. Güncel web artefaktı üret

Yeni canonical frontend dosyaları:

- `england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json`
- `england_map_web/data/program_layer_matrix/topography_visible_status_latest.json`

`topography_visible_rows_latest.json` içinde `rows` array olmalı ve şu kaynaklardan birleştirilmelidir:

1. Koordinat provenance:
   `england_map_web/data/program_layer_matrix/topography_coordinate_handoff_latest.json`
2. Güncel işlem satırları:
   `outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json`
3. En son topography status/queue/report kanıtı:
   - `docs/chatgpt_status/topography/status/*latest.json`
   - `docs/chatgpt_status/topography/queue/*.task.json`
   - `docs/chatgpt_status/topography/reports/*.md`

Her satır en az şu alanları taşımalı:

- `changed_in_latest_run`
- `display_badge`
- `task_id`
- `updated_at`
- `parcel_id`
- `parcel_ref`
- `centroid_lat`
- `centroid_lon`
- `bng_tile`
- `coordinate_status`
- `coordinate_source_path`
- `coordinate_source_lines`
- `boundary_status`
- `sampling_status`
- `height_source_discovery_status`
- `copdem_dataset`
- `copdem_product_type`
- `copdem_grid_id`
- `elevation_sea_level_m`
- `regional_average_elevation_m`
- `elevation_difference_regional_average_m`
- `source_url`
- `source_file_path`
- `local_source_path`
- `report_path`
- `status_path`
- `queue_path`
- `commit_sha`
- `confidence_percent`
- `accuracy_score_4`
- `blocker`
- `needs_manual_review`
- `final_ready`
- `fake_data`

Kanıt yoksa değer `null` / `not_available` kalmalı; dosya yolu veya ölçüm uydurulmayacak.

### B. Frontend config’i düzelt

Topography config hedefi:

- data: `data/program_layer_matrix/topography_visible_rows_latest.json`
- status: `data/program_layer_matrix/topography_visible_status_latest.json`
- rowsKey: `rows`
- title: `Height Difference / Topography - Güncel İşlem ve Kaynak Satırları`

Eski coordinate handoff JSON provenance kaynağı olarak korunmalı; ana UI kaynağı olmamalı.

### C. Tablo kolonlarını genişlet

Topography tablosunda aşağıdaki kolonlar görünmeli:

1. İşlem durumu / badge
2. Yeni işlem mi?
3. Task ID
4. Güncelleme zamanı
5. Parsel / parsel ref
6. Enlem / boylam / BNG tile
7. Koordinat kaynağı + kaynak satırları
8. Boundary durumu
9. Sampling durumu
10. DEM/LiDAR ürün adı
11. Dataset / product type / grid ID
12. Deniz seviyesine göre elevation
13. Bölgesel ortalama
14. Height difference
15. İnternet kaynak URL’si
16. Yerel indirilen kaynak dosyası
17. Rapor yolu
18. Status yolu
19. Queue yolu
20. Commit SHA
21. Güven / doğruluk
22. Blocker
23. Manuel inceleme
24. final_ready / fake_data

### D. Yeni işlemleri farklı göster

- `changed_in_latest_run=true`: belirgin yeşil/teal satır veya sol şerit.
- `display_badge` değeri satırın ana badge’i olarak gösterilmeli.
- `queued`: mavi/sarı.
- `blocked`: kırmızı.
- `source_backed_elevation_ready`: yeşil.
- Aynı satır hem yeni hem blocked ise iki badge birlikte görünmeli; blocked yeni bilgisini ezmemeli.
- Varsayılan sıralama: en yeni işlem önce.
- `Sadece yeni işlemler` filtresi eklenmeli.

### E. Kaynak yollarını kullanıcıya görünür yap

- `source_url`: tıklanabilir harici bağlantı.
- Repo-relative `source_file_path`, `report_path`, `status_path`, `queue_path`: monospace tam yol ve kopyalanabilir değer.
- `local_source_path`: yalnız gerçekten indirilmiş dosya varsa gösterilmeli; yoksa `not_available`.
- Browser’ın `F:\...` yolunu açamayabileceği durumda yol yine metin olarak eksiksiz görünmeli.

## Mevcut güncel işlem satırlarında görünmesi gereken örnekler

Aşağıdaki üç satır güncel işlem olarak görünmeli:

- `parcel_2757`
- `parcel_2758`
- `parcel_2759`

Güncel işlem bilgisi:

- `display_badge=COPERNICUS_ODATA_QUERY_CONTRACT_READY`
- `copdem_dataset=COP-DEM_GLO-30-DGED/2024_1`
- `copdem_product_type=SAR_DGE_30_A4AD`
- `copdem_grid_id=N51_W001`
- `source_file_path=docs/chatgpt_status/topography/queue/154_topography_copdem_odata_geocell_sampling_20260711.task.json`
- `sampling_status=official_odata_query_contract_ready_waiting_for_runner_readback`
- `boundary_status=pending_real_source`
- Numeric elevation alanları `null`
- `final_ready=false`
- `fake_data=false`

## Kabul testleri

1. `Height Difference / Topography` seçilince data path artık `topography_visible_rows_latest.json` olmalı.
2. Status path `same_data_or_not_required` olmamalı; gerçek `topography_visible_status_latest.json` görünmeli.
3. En az 3 satır render edilmeli.
4. Üç satırda 154 OData dataset/product/grid alanları görünmeli.
5. Satır bazında coordinate provenance ve güncel queue/status/report yolları birlikte görünmeli.
6. Yeni işlem badge’i eski coordinate satırından görsel olarak ayrılmalı.
7. `source_url`, local source path, report/status/queue path kolonları görünmeli.
8. Numeric elevation kanıt yoksa `null/not_available` kalmalı.
9. Browser Selenium testi:
   - rendered_rows >= 3
   - console_errors = []
   - `COPERNICUS_ODATA_QUERY_CONTRACT_READY` görünür
   - `N51_W001` görünür
   - queue path görünür
   - final_ready=false
   - fake_data=false
10. GitHub remote readback ile HTML, visible rows, status ve browser proof doğrulanmalı.

## Çıktılar

- Frontend HTML/JS düzeltmesi
- `topography_visible_rows_latest.json`
- `topography_visible_status_latest.json`
- Browser proof:
  `docs/chatgpt_status/topography/reports/155_topography_site_latest_results_browser_validation_20260711.json`
- Completion status:
  `docs/chatgpt_status/topography/status/155_topography_site_latest_results_visibility_fix_latest.json`

## Güvenlik ve doğruluk

- Yeni/paralel runner yok.
- Fake geometry yok.
- Fake elevation yok.
- DB write yok.
- Migration yok.
- Production deploy yok.
- Gerçek boundary ve raster sampling oluşana kadar `final_ready=false`.