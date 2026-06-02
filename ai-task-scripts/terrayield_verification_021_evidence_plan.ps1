$ErrorActionPreference = 'Continue'
$Project = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Start = Get-Date
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Project ".aays_next_fix\verification_021_evidence_plan_$Run"
$SummaryFile = Join-Path $ReportDir 'summary.md'
$PlanFile = Join-Path $ReportDir '3110_sale_land_verification_master_plan.md'
$BlueprintFile = Join-Path $ReportDir 'verification_pipeline_blueprint.json'
$BacklogFile = Join-Path $ReportDir 'verification_backlog_template.csv'
$InventoryFile = Join-Path $ReportDir 'local_data_inventory.txt'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log([string]$Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $SummaryFile -Value $line}
Log 'TASK: TerraYield 3110 sale land evidence-chain verification plan'
Log 'MODE: plan + local inventory + backlog schema; no destructive changes; no external scraping'
Log "PROJECT=$Project"
Log "REPORT_DIR=$ReportDir"

$inventory = @()
$patterns = @('*.csv','*.json','*.geojson','*.gpkg','*.parquet','*.sqlite','*.db')
foreach($pat in $patterns){
  Get-ChildItem -Path $Project -Recurse -File -Filter $pat -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\.git\\|node_modules|__pycache__|\.venv|venv|\.aays_next_fix' } |
    Select-Object -First 400 |
    ForEach-Object { $inventory += $_.FullName }
}
$inventory | Sort-Object -Unique | Set-Content -Encoding UTF8 -Path $InventoryFile
Log "LOCAL_INVENTORY_COUNT=$($inventory.Count)"

$plan = @'
# TerraYield 3110 Satışa Uygun Arsa Güvenilirlik ve Gerçek Boundary Ana Planı

## 0. Temel karar
3110 satış kaydı değerli bir satış adayı havuzudur; fakat her kayıt otomatik olarak gerçek/original satış boundary değildir. Sistem, kanıt zinciri tamamlanmadan hiçbir bbox, feed polygon, centroid etrafı kutu, alan ölçekli şekil veya sadece matched resmi parseli "verified sale boundary" olarak göstermeyecek.

## 1. Doğrulama hedefi
Amaç her kaydı sahte şekilde yüzde yüz göstermek değil; gerçekten kanıtlanabilen kayıtları L4 verified seviyesine çıkarmaktır. Diğer tüm kayıtlar doğru etiketle kalacaktır. Bu yaklaşım, kullanıcıya yanlış güven vermeyi engeller.

## 2. Güven seviyeleri
- L0 Unverified listing: URL/fiyat/konum sinyali var, güçlü kanıt yok. Haritada nokta.
- L1 Candidate sale record: fiyat/alan/konum sinyalleri var, satış boundary yok. Nokta ve bilgi kartı.
- L2 Matched official parcel: INSPIRE/HMLR gibi resmi parsel bağlamı var. Satış boundary değil, resmi parsel bağlamı.
- L3 Document-derived boundary candidate: public plan/red-line/title/site plan bulundu ama georeference/manual review tamam değil. Review layer.
- L4 Verified sale boundary: public belge + georeference + alan/konum/fiyat/source uyumu + ikinci kaynak veya insan onayı tamam. Sadece bu seviye koyu turuncu gerçek satış boundary olarak çizilir.

## 3. Her kayıt için ayrı ölçülecek kanıt boyutları
1. Kimlik eşleşmesi: aynı araziyi satan birden fazla URL/listing aynı fırsat mı?
2. Kaynak URL zinciri: agent, auction, portal, brochure, planning portal, official reference.
3. Konum uyumu: postcode, lat/lon, adres, yol adı, planning site address, parcel centroid mesafesi.
4. Fiyat uyumu: listing price, guide price, auction price, brochure price, tarih ve para birimi.
5. Alan/metrekare uyumu: m2, acre, hectare, sqft extraction ve polygon alan toleransı.
6. Boundary kanıtı: red-line plan, title plan, site plan, block plan, georeferenced polygon.
7. Kenar uzunlukları: perimeter, side lengths, plan ölçeği, ölçülü çizim veya georeferenced geometry karşılaştırması.
8. Resmi bağlam: INSPIRE ID, title reference, HMLR Price Paid, planning reference, brownfield reference.
9. Geliştirme uygunluğu: planning, brownfield, access, flood, utilities, constraints.
10. Son karar: L0-L4, confidence score, eksik kanıt ve next_action.

## 4. Kaynak sınıfları
- Özel satış kaynakları: OnTheMarket, agent siteleri, broker siteleri, auction house sayfaları, aynı ilanın tekrar yayınlandığı portallar. Fiyat/URL/fotoğraf/brochure için kullanılır; boundary için tek başına yeterli değildir.
- Public satış dokümanları: brochure, particulars, public auction pack, red-line plan, site plan, location plan, title plan referansı. Boundary için güçlü adaydır ama georeference ve review gerekir.
- Resmi/kamu kaynakları: HMLR INSPIRE, HMLR Price Paid, planning.data.gov.uk, local authority planning documents, brownfield datasets.
- Teknik destek kaynakları: yol erişimi, flood, su/kanalizasyon, elektrik/gaz altyapı, topography, satellite/photo bağlamı. Bunlar due diligence sinyali üretir; tek başına boundary üretmez.

## 5. Veri modeli
### sale_listing
listing_id, provider_listing_id, provider, canonical_url, title, ask_price, currency, area_value, area_unit, postcode, address_text, lon, lat, status, fetched_at.

### sale_opportunity_group
Aynı araziyi satan birden fazla listingi birleştirir. group_id, canonical_listing_id, duplicate_confidence, active_sources, conflict_flags.

### sale_source_crosswalk
Her listing/group için kaynak URL zinciri. group_id, listing_id, source_url, source_type, provider, match_reason, fetch_status, content_hash.

### sale_evidence
HTML/PDF/image/brochure/planning document/title-plan reference gibi kanıt deposu. evidence_id, listing_id/group_id, url, file_hash, evidence_type, fetched_at, page_number, extraction_log, storage_policy.

### sale_metric_claim
Kaynaklardan çıkan fiyat, alan, adres, plan ölçüsü, kenar uzunluğu iddiaları. claim_type, value, unit, normalized_value, source_evidence_id, confidence, extracted_text_span.

### sale_geometry_candidate
AI/georeference/manual aday polygonlar. geometry, method, source_evidence_id, area_m2, perimeter_m, side_lengths_json, crs, georef_rmse, candidate_confidence.

### sale_boundary_verification
L4 karar tablosu. candidate_id, evidence_chain_json, reviewer_or_method, area_match_pct, location_match_m, price_match_status, status, approved_at, rejection_reason.

### sale_verification_run
Yıllık/aylık çalışma kaydı. run_id, started_at, finished_at, input_count, l0_count, l1_count, l2_count, l3_count, l4_count, errors, report_path.

## 6. 3110 kayıt için ilk pipeline
1. Mevcut 3110 kaydı inventory ile bul.
2. Her kayıt için source URL, price, area, postcode, lon/lat, current geometry, display_polygon_source ve confidence alanlarını normalize et.
3. Candidate/bbox/estimated polygonları verified olarak sayma; bunları sadece audit için sakla.
4. Matched parcel varsa L2 resmi parsel bağlamı olarak işaretle; satış boundary olarak değil.
5. Public source URL’leri evidence backlog’a al.
6. Aynı araziyi satan çoklu listingleri URL, fiyat, alan, postcode, agent ref, foto hash ve metin benzerliğiyle sale_opportunity_group altında birleştir.
7. Public PDF/brochure/site plan/link bulunan kayıtları L3 review kuyruğuna yükselt.
8. Georeference + area/side-length/location/source consistency + review tamamlananları L4 yap.

## 7. AI/görüntü analizi kullanımı
AI fotoğraf ve planları şu amaçla kullanılır:
- red-line veya boundary sinyali tespiti,
- plan ölçeği, kuzey oku, yol isimleri, parsel köşeleri ve ölçü yazılarını çıkarma,
- candidate polygon mask üretme,
- foto/site/location consistency skoru üretme.
AI çıktısı tek başına verified değildir. AI sadece L3 candidate üretir. L4 için georeference, tolerans kontrolü ve ikinci kaynak/insan onayı gerekir.

## 8. Alan ve kenar uzunluğu kontrolü
- Kaynak alandan normalized_area_m2 üret.
- Polygon area_m2 ve perimeter_m hesapla.
- Side lengths JSON üret: ordered edges, length_m, bearing_deg, suspicious_short_edge, self_intersection flag.
- Güçlü belge planlarında önerilen alan toleransı +/-5%; ilan metinlerinde +/-10%.
- Tolerans aşılırsa L4 verilemez, conflict_flags içine yazılır.

## 9. Konum doğrulama
- Listing lat/lon ile official parcel centroid mesafesi.
- Postcode centroid ve adres metni uyumu.
- Planning application site address ve road label uyumu.
- Public plan georeference control point RMSE.
- High confidence için aynı yer sinyalinin en az iki bağımsız kaynaktan gelmesi gerekir.

## 10. Fiyat doğrulama
- Aynı arazi için portal/agent/auction/brochure fiyatları toplanır.
- Price date ve source priority saklanır.
- HMLR Price Paid aktif listing fiyatı değildir; geçmiş satış kalibrasyonu ve comparable history için kullanılır.
- Fiyat çelişkisi varsa canonical current price seçilir ve conflict flag açılır.

## 11. Yıllık tekrar modeli
- Her yıl verification_run açılır.
- Değişmeyen kaynak hashleri tekrar indirilmez.
- Yeni/değişmiş listingler önceliklendirilir.
- Kaynak kapanırsa son bilinen URL/hash/metadata korunur.
- Her yıl verification_delta_report üretilir: fiyat değişimi, area değişimi, source değişimi, geometry decision değişimi, confidence değişimi.

## 12. E diski ve taşınabilir veri
Ağır HTML/PDF/image/OCR/cache C diskine taşınmayacak. Ağır kaynaklar E diskindeki external root altında tutulacak. Programın taşınabilir paketine sadece final CSV/GeoJSON, verified polygon, evidence manifest, confidence score, audit report ve küçük kritik kanıt parçaları girecek.

## 13. Kabul kriterleri
- 3110 kayıt için evidence backlog oluşur.
- Her kayıt L0-L4 seviyesine atanır.
- Candidate/bbox/feed polygon verified çizilmez.
- Matched official parcel satış boundary diye adlandırılmaz.
- Sadece L4 koyu turuncu verified boundary olur.
- Endpoint metadata içinde confidence breakdown ve missing evidence döner.
- Annual run ve delta report tekrar üretilebilir.

## 14. Sprint planı
### Sprint 1: Yanlış geometriyi kilitle
/map/listings mevcut davranışını koru: unmatched point, matched official parcel polygon. feed polygon gerçek boundary olmaz.

### Sprint 2: Evidence warehouse
sale_evidence, sale_metric_claim, sale_source_crosswalk ve sale_opportunity_group tablolarını ekle.

### Sprint 3: Backlog ve skor motoru
3110 kayıt için eksik kanıt, source URL, price/area/location/polygon conflict raporu üret.

### Sprint 4: Document pipeline
Public brochure/site plan/title/red-line/planning doc linklerini indir, hashle, OCR/vision candidate üret.

### Sprint 5: Georeference ve side-length verification
Planlardan candidate polygon üret, alan/perimeter/kenar uzunluğu/konum toleransı hesapla.

### Sprint 6: Review UI
L3 -> L4 manual/second-source review workflow ekle.

### Sprint 7: Annual rerun
verification_run, delta_report, changed source detection, E disk cache policy.

## 15. İlk uygulama görevi
Bir sonraki kod görevi migration ve API metadata patch olmalı:
- evidence tabloları migration,
- L0-L4 enum,
- /map/listings response properties içine verification_level, confidence_breakdown, missing_evidence, display_polygon_warning,
- 3110 backlog export endpointi,
- sadece L4 için verified_sale_boundary style flag.
'@
Set-Content -Encoding UTF8 -Path $PlanFile -Value $plan

$blueprint = [ordered]@{
  project = 'TerraYield Land Intelligence'
  dataset_target = 3110
  verification_levels = @('L0_unverified_listing','L1_candidate_sale_record','L2_matched_official_parcel','L3_document_boundary_candidate','L4_verified_sale_boundary')
  strict_rules = @(
    'candidate_bbox_feed_geometry_is_never_verified_boundary',
    'matched_inspire_parcel_is_official_context_not_sale_boundary',
    'only_public_documents_and_georeferenced_review_can_promote_to_L4',
    'ai_output_is_candidate_only_until_georeferenced_and_reviewed',
    'source_url_hash_date_extraction_log_are_required_for_evidence'
  )
  core_tables = @('sale_listing','sale_opportunity_group','sale_source_crosswalk','sale_evidence','sale_metric_claim','sale_geometry_candidate','sale_boundary_verification','sale_verification_run')
  annual_outputs = @('verification_delta_report','changed_sources','changed_prices','changed_areas','changed_geometry_decisions','confidence_distribution')
}
$blueprint | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $BlueprintFile

$headers = 'listing_id,group_id,current_level,target_level,listing_url,source_count,price_status,area_status,location_status,geometry_status,side_length_status,official_context_status,document_status,missing_evidence,next_action,priority'
$headers | Set-Content -Encoding UTF8 -Path $BacklogFile
Log "PLAN_FILE=$PlanFile"
Log "BLUEPRINT_FILE=$BlueprintFile"
Log "BACKLOG_TEMPLATE=$BacklogFile"
Log 'RESULT=verification_plan_created'
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
Log "ELAPSED_SECONDS=$elapsed"
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "PLAN_FILE=$PlanFile"
Write-Output "BLUEPRINT_FILE=$BlueprintFile"
Write-Output "BACKLOG_TEMPLATE=$BacklogFile"
Write-Output "LOCAL_INVENTORY=$InventoryFile"
Write-Output 'RESULT=verification_plan_created'
Write-Output 'VERIFICATION_021_EVIDENCE_PLAN_DONE'
exit 0
