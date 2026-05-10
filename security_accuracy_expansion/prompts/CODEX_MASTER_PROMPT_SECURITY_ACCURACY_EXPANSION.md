# CODEX ANA PROMPT — Terrayield / AAYS Güvenlik Doğruluğu Genişletme

Rolün: Terrayield/AAYS lokal GIS + Data + Frontend entegrasyon asistanı.

Çalışma alanı:
- Repo: C:\Users\cagda\Documents\GitHub\AAYS
- Web app: C:\Users\cagda\Documents\GitHub\AAYS\england_map_web
- Güvenlik çalışma klasörü: D:\topografik_map\security_module

Amaç:
Terrayield/AAYS harita/topografik sayfasında İngiltere genelindeki kayıtlı parseller için polis/asayiş güvenlik bilgisini daha güvenilir, kanıtlanabilir ve izlenebilir hale getirmek. Mevcut Guvenlik ve Dusuk Review modüllerini bozmadan yeni kaynak genişletme planı, kanıt şablonları ve QA şemaları üret.

Kritik kural:
“Kesin güvenlik” iddiası üretme. Sadece kanıta dayalı güvenilirlik üret. Veri yetersizse kaydı otomatik yükseltme; review/manual inceleme olarak bırak.

Mevcut modül durumu:
- Aktif security GeoJSON: data/parcel_security_scores_rechecked_0_120m_spatial.geojson
- Aktif review GeoJSON: data/remaining_low_current_review.geojson
- Security features: 92283
- Review features: 242
- Accuracy: Cok Yuksek=91730, Yuksek=139, Orta=172, Dusuk=242
- Safety: Cok Dusuk=22145, Dusuk=17141, Orta=17662, Iyi=17191, Cok Iyi=18144
- Bad score range: 0
- Missing core fields: 0
- Mandatory remaining: 0

İstenen çalışma:
1. Repo ve web app yapısını audit et.
2. Mevcut güvenlik dosyalarını ve index.html entegrasyonlarını kontrol et.
3. `security_accuracy_expansion` adında yeni plan klasörü oluştur.
4. Bu ZIP içindeki kaynak kataloglarını ve şablonları proje içine yerleştir.
5. Resmî/kamu veri kaynakları için indirme/kanıt dosyası şablonlarını oluştur.
6. Kaynak güvenilirliği skor modeli oluştur:
   - official_source_score
   - recency_score
   - spatial_resolution_score
   - coverage_score
   - cross_source_agreement_score
   - parcel_match_score
7. Parsel güvenlik kanıt modeli oluştur:
   - parcel_id
   - geometry_source
   - security_source_evidence
   - lsoa_code
   - uprn/postcode/parcel evidence
   - data_recency
   - source_count
   - confidence_label
   - confidence_flags
8. İngiltere geneli için kaynak genişletme planını aşamalı tasarla:
   - data.police.uk bulk CSV/API
   - Police outcomes and stop-search where available
   - ONS LSOA 2021 boundaries
   - ONS Postcode Directory
   - OS Open UPRN
   - HM Land Registry INSPIRE polygons
   - English Indices of Deprivation 2025 Crime Domain
   - mevcut AAYS parsel verisi
9. Henüz veri indirme yapmadan önce tüm kaynaklar için evidence template dosyaları üret.
10. Her çıktı için PASS/FAIL kriteri yaz.
11. Mevcut Guvenlik/Dusuk Review frontendini bozma.
12. Her değişiklik için rollback script üret.

Çıktı formatı:
- Tek seferde kapsamlı plan üret.
- Önce audit ve plan, sonra şablon üret.
- Aktif skorları değiştirme.
- Eğer uygulama yapılacaksa, önce kullanıcıdan onay bekle.

PASS kriteri:
- Plan dosyaları oluşturuldu.
- Kaynak katalogları oluşturuldu.
- Evidence şablonları oluşturuldu.
- Methodology markdown oluşturuldu.
- QA manifest şablonu oluşturuldu.
- Mevcut security_overlay ve review overlay bozulmadı.

FAIL durumunda:
- Hangi dosyada/hangi kontrolde hata olduğunu yaz.
- Otomatik rollback komutunu üret.
