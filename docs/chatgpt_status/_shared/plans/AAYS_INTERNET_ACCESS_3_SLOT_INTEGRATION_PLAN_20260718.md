# AAYS Internet Access - 3 Slot / 18 Mantıksal Slot Entegrasyon Planı

Tarih: 2026-07-18
Durum: PLAN_READY_NOT_APPLIED

## 1. Mevcut gerçek durum
- Canlı program matrisi 92.283 satırdır ve mevcut manifestte `london_yes=92283` olarak tanımlıdır.
- `england_map_web/data/program_layer_matrix/internet.geojson` içinde 33.785 gerçek eşleşmiş özellik vardır.
- 58.498 satırda internet alanı eksiktir.
- Mevcut değerler postcode düzeyindeki Ofcom kapsam oranlarından türetilmiştir: gigabit, 100+ Mbps, 30+ Mbps ve kapsam dışı oranları.
- Mevcut doğruluk `2/4` seviyesindedir; bu veri parselde ölçülmüş gerçek bağlantı hızı değildir.

## 2. Ürün tanımı
Yeni ana alan: `internet_availability_quality_percent` (0-100).
Bu alan "parselde ölçülen hız" diye sunulmayacak; posta kodu/premise kapsamına dayalı beklenen internet kullanılabilirlik kalitesidir.

Her 92.283 satır mutlaka var olacak. Eşleşme yoksa satır silinmeyecek ve uydurma skor yazılmayacak:
- `internet_status=no_data`
- `internet_availability_quality_percent=null`
- `internet_match_confidence=0`
- açık blocker ve kaynak seviyesi yazılacak.

Zorunlu alanlar:
- canonical_program_parcel_id
- hmlr_inspire_id
- parcel_centroid_lon / parcel_centroid_lat
- postcode
- source_snapshot_date
- source_url / source_file_sha256
- source_level (`PREMISE`, `POSTCODE_PROXY`, `SPATIAL_POSTCODE_PROXY`, `NO_DATA`)
- gigabit_available_pct
- ultrafast_or_100mbps_available_pct
- superfast_30mbps_available_pct
- decent_broadband_unavailable_pct (yalnız kaynak şeması bunu gerçekten veriyorsa)
- full_fibre_available_pct (kaynakta varsa)
- provider_count (kaynakta varsa)
- internet_availability_quality_percent
- internet_quality_band
- internet_match_method
- internet_match_confidence
- internet_accuracy
- calculation_explanation

## 3. Puanlama kapısı
Önce en güncel Ofcom veri şeması doğrulanacak; olmayan kolona varsayımsal ağırlık verilmeyecek.

Önerilen normalize puan, yalnız doğrulanmış kolonlarla sürümlenecek:
- hız/kapsama potansiyeli: %55
- 30 Mbps ve decent erişilebilirlik: %20
- full fibre / future-proof teknoloji: %20
- doğrulanmış sağlayıcı çeşitliliği: %5

Bir bileşen kaynakta yoksa ağırlıklar kalan doğrulanmış bileşenlere normalize edilecek ve `calculation_version` kaydedilecek. Gecikme, gerçek kullanım hızı, kesinti ve bina içi Wi-Fi kalitesi kaynakta yoksa üretilmeyecek.

## 4. 3 internet slotu
Yeni mantıksal slotlar:
- `internet_access_1`: satır 1-30761
- `internet_access_2`: satır 30762-61522
- `internet_access_3`: satır 61523-92283

Her slot yalnız kendi satır aralığına ve kendi slot yollarına yazar. Aynı parcel ID iki slotta olamaz. Nihai GeoJSON/CSV/chunk birleştirmesi yalnız tek seri publisher tarafından yapılır.

## 5. 15'ten 18'e güvenli geçiş
- Yeni bağımsız runner/guardian açılmaz.
- Aynı tek adaptive coordinator korunur.
- Yeni workstream: `AAYS_18_SLOT_SAFE_PARALLEL_V1`.
- Mevcut 15 slot checkpointleri taşınmaz veya silinmez; compatibility readback ile korunur.
- Yeni canonical manifest `_shared/slots_18/manifest_latest.json` olur.
- Eski `_shared/slots_15` yolları geçiş boyunca salt okunur fallback kalır.
- Coordinator BASE_SLOT_SPECS'e yalnız `internet_access` eklenir.
- Panel slot listesini hardcode etmek yerine manifestten okur ve 18 satır gösterir.
- Donanım scheduler'ı 18 mantıksal slotu görür ama aynı anda açılan child sayısını RAM/CPU sınırlamasına göre belirler. 18 slot, 18 ağır işin zorunlu eşzamanlı çalışması anlamına gelmez.

## 6. Eşleştirme sırası
1. Parselin doğrulanmış postcode/UPRN eşleşmesi varsa doğrudan kullan.
2. Doğrulanmış adres-postcode eşleşmesi varsa kullan.
3. Yalnız centroid varsa resmi postcode referansına mekansal proxy uygula; aynı yerel yönetim ve sıkı mesafe kapısı zorunlu.
4. Kapıyı geçemeyen satırı `NO_DATA` bırak.
5. Aynı postcode içindeki parsellere aynı postcode kapsam oranı verilebilir; her satırda `POSTCODE_PROXY` açıkça yazılır.

## 7. Kaynaklar
Öncelik en güncel Ofcom Connected Nations postcode coverage indirmesidir. 2024 sonrası postcode düzeyinde actual performance yayınlanmadığı için coverage ile measured performance karıştırılmaz. ONS postcode referansı yalnız konum/eşleştirme için kullanılır.

## 8. Web ve program entegrasyonu
- `program_layer_matrix/internet.geojson` 92.283 satırlık canonical index ile uyumlu üretilecek; değer olmayanlar ayrı no-data manifestinde tutulacak.
- Harita rengi poligon katmanında yüzdeye göre gösterilecek; nokta tıklaması zorunlu olmayacak.
- Parsel poligonu tıklandığında canonical parcel ID üzerinden internet kaydı bulunacak.
- Popup: yüzde, bant, ham faktörler, kaynak tarihi, proxy seviyesi, güven ve açıklama.
- Program katman matrisi ve geometry kontrol sayfası publisher sonrası `SYNC_AAYS_CONTROL_SITES_TO_PORTABLE_WEB.ps1` ile 8012'ye yansıyacak.

## 9. Kabul testleri
- 92.283 canonical satır; duplicate parcel ID=0; shard overlap=0; shard gap=0.
- Sayısal değer taşıyan her satırda kaynak, tarih, yöntem ve güven mevcut.
- NO_DATA satırları korunuyor; sahte yüzde yok.
- Üç slotta lock/lease/checkpoint/heartbeat/current_task/status mevcut.
- İki aynı slot görevi eşzamanlı başlayamıyor.
- Publisher seri merge, commit, push ve remote readback PASS.
- 8012 ana uygulama ve iki kontrol sayfası HTTP 200.
- Browser testinde poligona tıklama, renk ve popup alanları kanıtlanıyor.

## 10. İngiltere geneli ikinci faz
İlk faz mevcut 92.283 Londra matrisini tamamlar. İngiltere geneli için önce PMTiles içinden kalıcı parcel ID içeren ulusal canonical envanter ve gerçek toplam satır sayısı çıkarılmalıdır. Bu sayı üretilmeden 92.283 bütün İngiltere toplamı diye kullanılamaz. Envanter hazır olduğunda aynı postcode eşleştirme ve puanlama sözleşmesi bölgesel shardlarla genişletilir.

## 11. Uygulama sırası
1. Ofcom 2026 postcode şema/snapshot doğrulaması.
2. 92.283 canonical postcode gap analizi.
3. Üç internet slot contract/checkpoint kurulumu.
4. 33.785 mevcut satırın yeni şemaya kayıpsız migrasyonu.
5. 58.498 eksik satır için doğrulanmış direct/spatial postcode eşleştirmesi.
6. Puanlama ve confidence hesaplama.
7. Seri publisher merge.
8. Program + iki kontrol sitesi + poligon tıklama browser testi.
9. Remote readback sonrası ancak gerçek tamamlanma oranı.

Güvenlik: `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
