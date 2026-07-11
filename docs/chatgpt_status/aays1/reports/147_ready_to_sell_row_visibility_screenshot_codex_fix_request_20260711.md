# AAYS / ReadyToSell — Satır Görünürlüğü, Kaynak ve Artifact Yolu Düzeltme Raporu

**Repo:** `cagdascagdas100/chat_gpt_clone_1`  
**Branch:** `codex/aays-single-runner-v5-20260706`  
**PAGE_KEY:** `aays1`  
**Canonical root:** `F:\TerraYield_AAYS_Portable`  
**Canonical site:** `http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html`  
**İlgili mevcut işler:** `147` UI görünürlük düzeltmesi ve mevcut `146` rows 1–3 evidence batch  
**Kural:** Yeni runner açma. Yeni/paralel runner oluşturma. `146` veya `147` görevini çoğaltma.

## 1. Kullanıcının doğruladığı problem

11 Temmuz 2026 tarihli tarayıcı ekranında sayfa açılıyor ve şu üst metrikler görünüyor:

- Geometry: `1264`
- İşlenmiş: `30`
- İşlenmemiş: `1234`
- Yeni bu çalışmada: `0`
- Canlı kaynak: `30`
- Vision compared: `0`
- Runner smoke: `PASS`
- `final_ready=false`
- `fake_data=false`

Tablo satırlarında kaynak URL mevcut olsa da kullanıcı yapılan işin tam kanıt zincirini göremiyor. Özellikle:

1. `Yerel kaynak yolu`, `İndirilen fotoğraf(lar)`, `Polygon render`, `Vision çıktısı`, `Status JSON` ve `Rapor` alanlarının çoğu `not_available`.
2. `docs/chatgpt_status/...` yolları tarayıcıdan açılabilir bağlantı değil.
3. Aktif batch kutusundaki status ve report yolları düz metin; tıklanabilir değil.
4. Yeni yapılan satırlar için UI desteği varmış gibi görünse de veri tarafında `new_this_run=false`; bu nedenle “YENİ BU ÇALIŞMADA” rozeti ve new-only görünümü boş.
5. Aktif batch bilgisi eskimiş: `RESUME_REQUESTED_OUTPUT_WAITING`, eski güncelleme zamanı ve eski `_shared/queue` yolu gösteriliyor.
6. 19 kolonluk tablo çok geniş. Kanıt kolonları sağ tarafta kaldığı için kullanıcı satırın kaynak/kanıt dosyalarını kolayca göremiyor.
7. Kaynak URL, kaynak sonucu ve ilan türü görünse bile indirilen kaynak snapshot’ı veya kaynak manifesti satıra bağlanmamış.
8. `146` rows 1–3 için gerçek status/report output henüz görünür değil; sahte artifact veya sahte ilerleme yazılmamalı.

## 2. Kanıtlanan veri durumu

`photo_ai_boundary_review_results.json` içinde 30 adet kaynak doğrulanmış satır var. Örnek satırlarda:

- `listing_url`
- `parcel_ref`
- `source_verification_status`
- `source_verification_result`
- `source_listing_type_verified`
- bazı satırlarda `source_area_verified`
- `source_photo_count_verified`
- `batch_id`
- `evidence_updated_at`
- `run_status`

bulunuyor.

Ancak aşağıdaki alanlar satırların çoğunda yok:

- `local_source_path`
- `source_html_path`
- `source_json_path`
- `source_manifest_path`
- `downloaded_photo_path`
- `downloaded_photo_paths`
- `polygon_render_path`
- `vision_output_path`
- `status_json_path`
- `report_md_path`
- `source_http_status`
- `source_checked_at`
- `change_summary`

Bu nedenle HTML kolonları mevcut olsa bile içerik `not_available` olarak render ediliyor. Problem yalnız CSS/HTML değil; **üretici script → JSON veri sözleşmesi → served artifact → HTML linkleme zinciri eksik**.

## 3. Zorunlu düzeltme kapsamı

### 3.1 Mevcut görev sırası

Aşağıdaki sıra korunacak:

1. Mevcut `147` UI/data görünürlük düzeltmesini tamamla.
2. Chrome/Edge browser testi ve GitHub remote readback ile `147` kabulünü kanıtla.
3. Mevcut `146` görevini yerinde devam ettir; duplicate task oluşturma.
4. `146` rows 1–3 çıktısını siteye satır satır bağla.
5. Bu kapılar geçtikten sonra daha büyük işler aynı tek shared runner içinde **ardışık** batch olarak devam etsin.

UI düzeltmesi doğrulanmadan yeni vision batch açılmamalı.

### 3.2 Satır veri sözleşmesi

İşlenen her satırda aşağıdaki alanlar açıkça bulunmalı:

```json
{
  "row_id": 1,
  "batch_id": "aays1-ready-to-sell-...",
  "new_this_run": true,
  "evidence_updated_at": "ISO-8601",
  "change_summary": "Bu batchte yapılan gerçek değişiklik",
  "listing_url": "https://...",
  "source_verification_status": "verified_live_listing_page",
  "source_verification_result": "positive_source_evidence_found",
  "source_http_status": 200,
  "source_checked_at": "ISO-8601",
  "source_page_title_verified": "...",
  "source_listing_type_verified": "...",
  "source_area_verified": "...",
  "source_planning_ref_verified": "...",
  "local_source_path": "england_map_web/data/.../source_snapshot.html",
  "source_json_path": "england_map_web/data/.../source_snapshot.json",
  "source_manifest_path": "england_map_web/data/.../source_manifest.json",
  "downloaded_photo_paths": [
    "england_map_web/data/.../source_photo_1.jpg"
  ],
  "polygon_render_path": "england_map_web/data/.../canonical_polygon_row_1.svg",
  "vision_output_path": "england_map_web/data/.../vision_manifest_row_1.json",
  "status_json_path": "england_map_web/data/aays1/artifacts/.../status.json",
  "report_md_path": "england_map_web/data/aays1/artifacts/.../report.html",
  "visual_match_score": null,
  "geometry_mismatch_flag": null,
  "confidence_after": "3/4_source_verified_vision_pending",
  "run_status": "EVIDENCE_READY_VISION_PENDING"
}
```

Alan yoksa sahte değer yazma. Gerçek dosya oluşmadıysa `null` kullan ve UI’da açıkça `DOSYA ÜRETİLMEDİ` veya `OUTPUT BEKLENİYOR` göster.

### 3.3 Güvenli artifact yayınlama

Tarayıcı `docs/chatgpt_status/...` dosyalarını doğrudan açamıyor. Aşağıdaki iki güvenli modelden biri uygulanmalı:

**Tercih edilen model — served artifact mirror**

- Status/report/source manifest dosyalarının salt-okunur kopyalarını:
  `england_map_web/data/aays1/artifacts/<task_id>/...`
  altında üret.
- Orijinal repo yolunu JSON içinde ayrıca sakla:
  - `repo_status_path`
  - `repo_report_path`
- UI’da:
  - “Site kopyası” bağlantısı
  - “Repo yolu” kopyalanabilir metin
  birlikte gösterilsin.

**Alternatif model — whitelist static route**

- Yalnız izinli `docs/chatgpt_status/aays1/status`, `reports` ve ilgili evidence yollarını salt-okunur servis eden dar kapsamlı bir endpoint ekle.
- Path traversal engellenmeli.
- Keyfi F:\ veya repo dosya erişimi açılmamalı.

### 3.4 UI değişiklikleri

1. İlk görünüm 30 işlenmiş satırı göstermeye devam etsin.
2. Satır 31+ AI/source kaydı yoksa `NOT_PROCESSED`.
3. Sol tarafta sabit/sticky kolonlar:
   - Satır
   - Durum
   - Batch/yeni
   - Kaynak URL
   - “Kanıtları Aç”
4. Geniş kolonlar yerine her satırda açılır **Kanıt Ayrıntısı** paneli ekle:
   - kaynak snapshot
   - kaynak JSON/manifest
   - indirilen fotoğraflar
   - polygon render
   - vision output
   - status
   - report
   - repo yolları
5. Gerçekten bu batchte değişen satırlara:
   - `YENİ BU ÇALIŞMADA`
   - farklı arka plan
   - batch id
   - işlenme zamanı
   - change summary
6. `Sadece yeni yapılanlar` filtresi gerçek `new_this_run=true` satırlarını göstermeli.
7. Üst metrikte:
   - yeni satır sayısı
   - indirilen fotoğraf sayısı
   - polygon render sayısı
   - vision compared sayısı
   ayrı gösterilmeli.
8. Aktif batch kutusundaki status/report/queue yolları tıklanabilir veya kopyalanabilir olmalı.
9. Aktif batch JSON eski `_shared/queue` yolunu göstermemeli; canonical yol:
   `docs/chatgpt_status/aays1/queue/...`
10. Her link için durum göster:
    - `HTTP 200`
    - `MISSING`
    - `OUTPUT WAITING`
    - `FETCH BLOCKED`
11. “Veriyi Yenile” sonrası cache-bust uygulanmalı ve yeni batch görünümü güncellenmeli.

## 4. Doğruluk ve güven kuralları

Gerçek ilan fotoğrafı indirme + canonical polygon render + gerçek vision comparison olmadan:

- `visual_match_score` yazma.
- Satırı `VISION_COMPARED` sayma.
- Confidence değerini vision kanıtı varmış gibi artırma.
- `3.5+` iddiası yazma.
- `geometry_mismatch_flag=false` varsayma; karşılaştırma yoksa `null`.

Kaynak sayfası açılmış fakat fotoğraf indirilememişse durum ayrı gösterilmeli:

- `LIVE_SOURCE_VERIFIED_VISION_PENDING`
- `LIVE_LISTING_OPENED_NO_DOWNLOADABLE_IMAGE_FOUND`
- `LIVE_LISTING_FETCH_BLOCKED`
- `EVIDENCE_READY_VISION_PENDING`
- `VISION_COMPARED`
- `MANUAL_REVIEW_REQUIRED`

## 5. `146` rows 1–3 entegrasyonu

Mevcut `146` duplicate edilmeden şu gerçek çıktıları üretmeli:

- rows 1, 2, 3 için internet ilan sayfası erişim sonucu
- kaynak snapshot/manifest
- gerçek indirilen fotoğraf yolları
- canonical polygon SVG yolu
- row-level vision manifest; score `null`
- status JSON
- report
- Git commit/push/readback kanıtı

Başarılı evidence üretiminden sonra rows 1–3:

- `new_this_run=true`
- `batch_id=146...`
- `evidence_updated_at=<gerçek zaman>`
- `change_summary=<gerçek yapılan işlem>`
- `run_status=EVIDENCE_READY_VISION_PENDING` veya gerçek blokaj durumu

olarak siteye yansıtılmalı.

Fotoğraf indirilemezse satır yeni olarak işaretlenebilir, fakat change summary ve blokaj gerçek olmalı; score artmamalı.

## 6. Kabul testleri

Aşağıdakilerin tamamı gerçek browser testi ve GitHub remote readback ile kanıtlanmadan düzeltme tamamlandı sayılmamalı:

1. URL HTTP 200:
   `http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html`
2. Varsayılan görünüm: `30/30` işlenmiş satır.
3. Tüm görünüm: `1264` satır.
4. Satır 31+: `NOT_PROCESSED`.
5. New-only görünüm:
   - `146` tamamlanmadıysa `0` ve açık `OUTPUT BEKLENİYOR`.
   - `146` gerçek output ürettiyse tam olarak değişen rows 1–3.
6. Rows 1–3 için her gerçek artifact linki HTTP 200.
7. Eksik artifact linki oluşturulmuyor; `MISSING/WAITING` gösteriliyor.
8. Status ve report site üzerinden açılabilir ya da güvenli mirror üzerinden görüntülenebilir.
9. Source URL yeni sekmede açılır.
10. Yerel/repo yolu kopyalanabilir.
11. Browser console error: `0`.
12. Aynı satırın eski ve yeni batch verisi karıştırılmıyor.
13. `visual_match_score=null` kaldığı sürece Vision compared: `0`.
14. `final_ready=false`.
15. `product_final_ready=false`.
16. `fake_data=false`.
17. `db_write=false`.
18. `migration=false`.
19. `production_deploy=false`.
20. Git commit push edilmiş ve remote readback SHA/nonce eşleşmiş.

## 7. Codex çıktıları

Codex aşağıdaki çıktıları üretmeli:

- Düzeltilen dosya listesi
- Değişiklik özeti
- Browser test JSON
- Satır link kontrol JSON’u
- rows 1–3 artifact manifest
- status/report dosyaları
- commit SHA
- push status
- remote readback kanıtı
- blocker listesi
- güvenlik flag’leri

Önerilen proof yolları:

```text
docs/chatgpt_status/aays1/status/147_ready_to_sell_row_visibility_latest.json
docs/chatgpt_status/aays1/reports/147_ready_to_sell_row_visibility_report.md
docs/chatgpt_status/aays1/runner_outputs/147_ready_to_sell_row_visibility_browser_test.json
england_map_web/data/aays1/ready_to_sell_active_batch_latest.json
england_map_web/data/aays1/artifacts/147/
```

## 8. Çalıştırma kısıtları

- Yeni runner açma.
- Paralel runner açma.
- F portable tek shared runner dışında sistem önerme.
- C:\ canonical kabul etme.
- `146` görevini çoğaltma.
- `147` görevini çoğaltma; bu raporu mevcut `147` kapsamının screenshot doğrulama eki olarak uygula.
- Sahte completed yazma.
- Sahte `%100` yazma.
- Sahte `final_ready=true` yazma.
- Gerçek output + GitHub push + remote readback olmadan metrik artırma.
- UI kabulü geçmeden yeni vision batch başlatma.

## 9. İşlem devam sırası

```text
147 UI/data/artifact görünürlüğü düzelt
→ browser + link + remote readback kabulü
→ mevcut 146 rows 1–3 evidence görevini devam ettir
→ rows 1–3 siteye “YENİ BU ÇALIŞMADA” olarak gerçek artifact yollarıyla yansıt
→ daha büyük ardışık tek-runner batchlerine devam et
```

**Mevcut durum:** `BLOCKED_BY_ROW_ARTIFACT_VISIBILITY_GATE`  
**ReadyToSell:** `30 işlenmiş / 1234 işlenmemiş / 0 yeni`  
**Vision compared:** `0`  
**final_ready:** `false`
