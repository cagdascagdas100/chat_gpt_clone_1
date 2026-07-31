# ready_to_sell_3 — araştırma dalgaları 1501–1504

- Continuation key korundu: `6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a`.
- İnternet araştırması Auction House UK, SDL, Savills ve Allsop resmî kaynak gruplarına ayrıldı; kullanılmamış karar-verilebilir kayıtlar Auction House UK ve SDL üzerinden tutuldu.
- GitHub yazımları seri yapıldı.
- İncelenen resmî kayıt: 18.
- Seçilen yüksek güvenli aday: 16.
- Fail-closed dışlanan: 2.
- Ortalama kaynak güveni: %99,83.
- Resmî kaynak yükseltmesi: 16; bunların 13'ü current full-direct page, 2'si bounded current direct-page snapshot ve 1'i current auction lot-list snapshot.
- Temsilî exact-address depo sorgusu: 18; indeks eşleşmesi: 0. Tam kapsamlı duplicate kanıtı iddia edilmedi.
- Görünür araştırma satırı: 6.037.
- Görünür operasyon: 18.923 / 18.925 (%99,989432; artış +0,000009 yüzde puanı).

## Adaylar

1. Former High Well School, High Well Hill Lane, South Hiendley, Barnsley S72 9DF.
2. Woolley Hall, New Road, Woolley, Wakefield WF4 2JR.
3. Land at Newton Street, Crewe CW1 2NE.
4. 5 Evesham Street, Alcester B49 5DS.
5. 15 Coundon Road, Coventry CV1 4AR.
6. 76 Mallard Avenue, Nuneaton CV10 9LW.
7. 122 Main Street, Calverton NG14 6FB.
8. The White Horse, 217 Bolton Road, Kearsley BL4 8NG.
9. 10 Holly Road, Bromsgrove B61 8LJ.
10. 60 Wood Street, Ilkeston DE7 8GE.
11. Apartment 31, Broadwater Boulevard Flats, Worthing BN14 8JF.
12. 3 The Green, Seamer TS9 5LS.
13. Richards House, Crosby Road, Northallerton DL6 1AE.
14. 241 Burncross Road, Chapeltown, Sheffield S35 1RZ.
15. 31B Stanley Street, Luton LU1 5AL.
16. 93 Dale Grove, Leyburn DL8 5GA.

## Fail-closed

- Former Vehicle Sales Site, Burcroft Hill, Conisbrough DN12 3EF.
- Former Vehicle Depot Site, Burcroft Hill, Conisbrough DN12 3EF.

İki lot aynı adresi kullanıyor ve resmî sayfalarda 0,30 ve 0,25 acre olarak ayrı tanımlanıyor; ancak legal-pack planları ve title boundaries olmadan fiziksel parsel kapsamları güvenle ayrıştırılamadığı için ikisi de fail-closed tutuldu.

## Doğruluk sınırları

Snapshot kayıtları güncel resmî kanıt dışına genişletilmedi. Guide fiyatları değerleme veya gerçekleşen satış fiyatı sayılmadı. Tenancy, rent, yield, FRI lease, HMO, title, tenure, lease, freehold composition, VAT, service charges, parking, listed-building obligations, commercial/residential use, site area, possession, occupancy, measurements, services, condition ve planning ifadeleri bağımsız doğrulanmış sonuca dönüştürülmedi. Parsel/geometri eşleşmesi yapılmadı ve hiçbir aday promote edilmedi.

## Kalan engel

`AUTOMATION_167_DOM_PROOF` ilk doğrulanmamış adım olarak kaldı. Port 8012 headless DOM kanıtı, public-host readback, kanonik parsel eşleşmesi ve geometri kanıtı bulunmadığından `final_ready=false` korunmuştur. İkinci runner, owner veya görev oluşturulmamıştır.
