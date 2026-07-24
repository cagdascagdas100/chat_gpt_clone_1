# Ready To Sell / Geometry Review — Satır Görünürlüğü ve Yeni-İşlem Ayrımı Düzeltme Raporu

## Amaç

Kullanıcı, `http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html` sayfasında yapılan işlemleri satır satır, kaynakları ve yerel artifact yollarıyla birlikte açıkça görmek istiyor. Yeni yapılan satırlar eski satırlardan görsel olarak ayrılmalı. Veri zinciri görünür olmadan işlem ilerlemiş sayılmamalıdır.

## Ekran görüntüsünde doğrulanan mevcut durum

- Üst metrikler doğru temel sayıları gösteriyor: `Geometry 1264`, `AI sonucu 30`, `Canlı kaynak 30`, `Vision compared 0`, `final_ready=false`.
- İlk sayfada 1264 satır birlikte gösterildiği için kullanıcı, işlenmiş 30 satırın nerede olduğunu kolayca ayırt edemiyor.
- 30'dan sonraki satırlar `VISION PENDING` yazıyor; ancak bu satırlarda AI kaydı, canlı kaynak doğrulaması veya vision kuyruğu yok. Bu durum teknik olarak belirsiz ve kullanıcıya işlenmiş izlenimi veriyor.
- `Yalnız latest-run / AI sonuçlu` filtresi varsayılan olarak kapalı.
- Yeni batch satırları için `NEW_THIS_RUN`, batch kimliği, işlenme zamanı ve değişiklik özeti görünmüyor.
- Kaynak, indirilen fotoğraf, polygon render, vision output, status ve report yolları mevcutsa bile kullanıcıya belirgin ve tıklanabilir şekilde sunulmuyor.
- Aktif batch `146` henüz output üretmediği için satır 1-3 için yeni artifact yolları oluşmamış durumda; UI bunu açık bir batch durumu olarak göstermiyor.

## Kök nedenler

1. `rowStatus(a)` fonksiyonu AI kaydı olmayan satırı da `VISION PENDING` olarak etiketliyor.
2. Varsayılan görünüm tüm 1264 satırı açıyor; işlenmiş satırlar görünüm içinde kayboluyor.
3. Satır modelinde `batch_id`, `evidence_updated_at`, `new_this_run`, `run_status` alanları bulunmuyor veya render edilmiyor.
4. Yerel artifact yolları düz metin; HTTP üzerinden açılabilir relative link'e dönüştürülmüyor.
5. Aktif queue/status/report bilgisi sayfanın üstünde batch özeti olarak gösterilmiyor.
6. Yeni tamamlanan satırlar için ayrı CSS sınıfı ve kalıcı rozet yok.

## Zorunlu düzeltmeler

### 1. Durum semantiğini düzelt

Aşağıdaki durumlar birbirinden ayrılmalı:

- `NOT_PROCESSED`: AI sonucu ve canlı kaynak doğrulaması olmayan satır.
- `LIVE_SOURCE_VERIFIED / VISION_PENDING`: canlı kaynak doğrulanmış fakat fotoğraf/polygon/vision zinciri tamamlanmamış satır.
- `EVIDENCE_READY / VISION_PENDING`: gerçek fotoğraf indirilmiş ve canonical polygon render üretilmiş, vision compare bekleyen satır.
- `VISION_COMPARED`: gerçek vision output ve `visual_match_score` bulunan satır.
- `MANUAL_REVIEW_REQUIRED`: mismatch veya eksik/çelişkili kanıt bulunan satır.

AI kaydı olmayan satıra `VISION PENDING` yazılmamalıdır.

### 2. Varsayılan görünümü işlenmiş satırlara odakla

- Sayfa ilk açıldığında `Yalnız latest-run / AI sonuçlu` filtresi açık gelsin veya URL parametresiyle `?view=latest` desteklensin.
- Kullanıcı isterse tüm 1264 satıra geçebilsin.
- Üstte açıkça `30 işlenmiş / 1234 işlenmemiş` özeti gösterilsin.

### 3. Yeni yapılan satırları farklı göster

- Her satıra `batch_id`, `evidence_updated_at`, `new_this_run` alanları eklenmeli.
- Yeni batch satırları için belirgin `YENİ BU ÇALIŞMADA` rozeti ve farklı satır arka planı kullanılmalı.
- `Sadece yeni yapılanlar` filtresi eklenmeli.
- Yeni satır sayısı üst metrikte ayrı gösterilmeli.

### 4. Kaynak ve artifact yollarını tıklanabilir yap

Aşağıdaki alanlar ayrı kolonlarda ve tıklanabilir olmalı:

- `listing_url`
- `local_source_path`
- `downloaded_photo_path` ve `downloaded_photo_paths`
- `polygon_render_path`
- `vision_output_path`
- `status_json_path`
- `report_md_path`

`england_map_web/data/...` altındaki artifact'lar relative HTTP link olarak açılmalı. Repo içi `docs/...` yolları en azından tam dosya yolu ve kopyalanabilir metin olarak gösterilmeli.

### 5. Aktif batch özetini ekle

Sayfanın üstünde şu bilgiler görünmeli:

- Aktif task id
- Durum: queued / running / completed / blocked
- Hedef satırlar
- Beklenen status/report yolları
- Son güncelleme zamanı
- Bu batch'te indirilen fotoğraf sayısı
- Polygon render sayısı
- Vision compare sayısı

Aktif batch:

- Task: `aays1-ready-to-sell-vision-evidence-rows-1-3-20260711`
- Hedef: satır 1, 2, 3
- Beklenen status: `docs/chatgpt_status/aays1/status/146_aays1_prepare_vision_evidence_rows_1_3_latest.json`
- Beklenen report: `docs/chatgpt_status/aays1/reports/146_aays1_prepare_vision_evidence_rows_1_3_report.md`

Output yoksa UI `QUEUED — OUTPUT BEKLENİYOR` göstermeli; satırlara sahte artifact yazmamalı.

### 6. Satır ayrıntısını doğru bağla

`photo_ai_boundary_review_results.json` içindeki satır verileri şu alanlarla siteye yansıtılmalı:

- source verification status
- listing title/type/area/planning ref
- confidence before/after
- photo evidence status
- downloaded photo paths
- polygon render path
- vision output path
- visual match score
- geometry mismatch flag
- status/report paths
- batch id ve update zamanı

### 7. 3.5+ kuralını koru

Gerçek fotoğraf indirme + canonical polygon render + gerçek vision compare olmadan:

- `visual_match_score` yazılmamalı
- confidence `3/4_source_verified_vision_pending` üstüne çıkarılmamalı
- satır `VISION_COMPARED` sayılmamalı

## Kabul kriterleri

1. Sayfa açıldığında işlenmiş 30 satır varsayılan görünümde açıkça görünür.
2. Satır 31+ AI kaydı yoksa `NOT_PROCESSED` görünür.
3. Yeni batch tamamlandığında satır 1-3 `YENİ BU ÇALIŞMADA` rozetiyle görünür.
4. Fotoğraf, polygon, vision, status ve report yolları satır seviyesinde tıklanabilir veya açıkça kopyalanabilir olur.
5. `Sadece yeni yapılanlar` filtresi çalışır.
6. Batch özeti queued/running/completed/blocked durumunu gerçek output dosyasından gösterir.
7. Chrome/Selenium testiyle:
   - latest görünümde 30/30 satır,
   - new-only görünümde batch satırları,
   - tüm görünümde 1264 satır,
   - konsol hatası olmaması
   doğrulanır.
8. GitHub remote readback yapılmadan tamamlandı denmez.
9. `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false` korunur.

## Düzeltilecek ana dosyalar

- `england_map_web/geometry_review_3of4_columns_1264.html`
- `england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json`
- `england_map_web/data/aays1/aays1_product_status_latest.json`
- Gerekirse yeni batch-summary JSON'u: `england_map_web/data/aays1/ready_to_sell_active_batch_latest.json`

## Devam kuralı

Önce bu UI görünürlük düzeltmesi uygulanmalı ve Chrome/Selenium + GitHub remote readback ile doğrulanmalıdır. Ardından mevcut `146` batch kaldığı yerden devam etmeli. UI düzeltmesi tamamlanmadan yeni vision batch açılmamalıdır.
