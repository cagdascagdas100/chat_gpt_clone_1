# ready_to_sell_3 — araştırma dalgaları 1465–1468

- Continuation key korundu: `6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a`.
- İnternet araştırması dört sınırlı gruba ayrıldı; GitHub yazımları seri yapıldı.
- Resmî kaynak aileleri: Savills ve Auction House UK.
- İncelenen resmî kayıt: 17.
- Seçilen yüksek güvenli aday: 14.
- Fail-closed dışlanan: 3.
- Ortalama kaynak güveni: %99,76.
- Resmî kaynak yükseltmesi: 14 — 10 Savills güncel katalog snapshot, 1 Savills katalog+tam detay, 3 Auction House tam doğrudan sayfa.
- Temsilî exact-address depo sorgusu: 17; indeks eşleşmesi: 0. Tam kapsamlı duplicate kanıtı iddia edilmedi.
- Görünür araştırma satırı: 5.921.
- Görünür operasyon: 18.807 / 18.809 (%99,989367; artış +0,000008 yüzde puanı).

## Adaylar

1. Apartment 7, Thornlea Court, Sunderland SR2 7JZ.
2. 81 Castleview House, Runcorn WA7 2DP.
3. 209 Manor Road, Chigwell IG7 4JY.
4. Flat 2, 3 Cottage Road, London N7 8TP.
5. 23 Rhodes Cottages, Clowne S43 4LZ.
6. 17 Westgate Central, Wakefield WF1 1EW.
7. 146 Denham Way, Maple Cross WD3 9SP.
8. 164 Rake Hill, Burntwood WS7 9DE.
9. 25 Lightwood, Bracknell RG12 0TR.
10. 31 Sandhurst Close, Royal Tunbridge Wells TN2 3ST.
11. Apartment 2, 2 Lee Bank Middleway, Birmingham B15 2BE.
12. 18 Rushbrook Mill, Ipswich IP8 4BF.
13. 19 Rushbrook Mill, Ipswich IP8 4BF.
14. 2 Avery Close, Allhallows ME3 9QG.

## Fail-closed

- 49 Park View: current catalogue £105.000 guide gösterirken current full-detail sayfası `Guide price TBA` gösteriyor.
- 902 Northampton House: current August catalogue kaydı mevcut, ancak exact-address full-detail erişimi current-event yerine eski March/June sayfalarına çözümlendi.
- 89 Castleview House: current full-detail sayfası cache miss verdi; prior-event tenure/tenancy bilgisi current state olarak yeniden kullanılmadı.

## Doğruluk sınırları

Guide fiyatları değerleme veya gerçekleşen satış fiyatı sayılmadı. Kira, tenancy, yield, lease, title, new-lease-on-completion, charges, balcony, lift, parking, garage, extension, converted-garage, converted-building, ölçüm, vacancy, possession, hizmetler ve condition ifadeleri bağımsız doğrulanmış sonuca dönüştürülmedi. Savills katalog-only kayıtlar güncel katalog kanıtı dışına genişletilmedi. Parsel/geometri eşleşmesi yapılmadı ve hiçbir aday promote edilmedi.

## Kalan engel

`AUTOMATION_167_DOM_PROOF` ilk doğrulanmamış adım olarak kaldı. Port 8012 headless DOM kanıtı, public-host readback, kanonik parsel eşleşmesi ve geometri kanıtı bulunmadığından `final_ready=false` korunmuştur. İkinci runner, owner veya görev oluşturulmamıştır.
