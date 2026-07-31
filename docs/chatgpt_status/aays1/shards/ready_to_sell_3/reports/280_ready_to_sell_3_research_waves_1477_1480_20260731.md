# ready_to_sell_3 — araştırma dalgaları 1477–1480

- Continuation key korundu: `6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a`.
- Araştırma Auction House UK, SDL ve Allsop resmî sayfalarına bölündü; GitHub yazımları seri yapıldı.
- İncelenen resmî karar: 10.
- Seçilen yüksek güvenli aday: 2.
- Fail-closed dışlanan: 8.
- Ortalama kaynak güveni: %99,90.
- Resmî kaynak yükseltmesi: 2 Auction House tam doğrudan sayfa.
- Temsilî exact-address depo sorgusu: 8; indeks eşleşmesi: 0. Tam kapsamlı duplicate kanıtı iddia edilmedi.
- Görünür araştırma satırı: 5.951.
- Görünür operasyon: 18.837 / 18.839 (%99,989384; artış +0,000001 yüzde puanı).

## Adaylar

1. 6A King Georges Road, Newbiggin-By-The-Sea NE64 6HR.
2. 45 Beaufort Road, Stoke-On-Trent ST3 1RH.

## Fail-closed

- 102 Caunce Street ve 13 Third Street: 27–28 Temmuz açık artırmaları geçmiş durumda.
- Flat 202 York Place: resmî sayfa adres ve guide gösteriyor ancak belirli gelecek etkinlik veya kapanış tarihi göstermiyor.
- 10 Summersfield Road: yayıncı taşınmaz içine giremediğini ve iç yapılandırmayı doğrulayamadığını belirtiyor.
- 103 Field Lane: güncel property, tenure ve occupancy kanıtı yüksek güvenli kayıt için yetersiz.
- Apartment 6, 7 Tinker Brook Close: güncel Ağustos guide’ı ile stale Temmuz bidding paneli çelişiyor.
- Allsop: Ağustos tarihi doğrulanıyor ancak güncel Ağustos lot kataloğu görünmüyor.
- SDL: Ağustos etkinlikleri doğrulanıyor ancak yeni kullanılmamış lot ile etkinlik bağlantısı doğrulanmıyor.

## Doğruluk sınırları

Guide fiyatları değerleme veya gerçekleşen satış fiyatı sayılmadı. Title, tenure, lease, charges, garage, courtyard, access, boundaries, availability, possession, configuration, measurements, services, condition ve value-add ifadeleri bağımsız doğrulanmış sonuca dönüştürülmedi. Geçmiş, stale, çelişkili, tarihsiz veya yetersiz kanıt seçili havuza alınmadı. Parsel/geometri eşleşmesi yapılmadı ve hiçbir aday promote edilmedi.

## Teknik erişim ve kalan engel

Paralel web araması sırasında geçici `503 Service Unavailable`, doğrudan HTTP erişiminde DNS name-resolution hatası görüldü. Erişilemeyen kanıt uydurulmadı; yalnız web aramasında doğrulanmış resmî sayfalar kullanıldı. `AUTOMATION_167_DOM_PROOF` ilk doğrulanmamış adım olarak kaldı. Port 8012 headless DOM kanıtı, public-host readback, kanonik parsel eşleşmesi ve geometri kanıtı bulunmadığından `final_ready=false` korunmuştur. İkinci runner, owner veya görev oluşturulmamıştır.
