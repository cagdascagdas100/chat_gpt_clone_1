# future_growth_3 — waves 2148–2327 — 2026-07-26

## Sonuç
- 180 gerçek resmî Planning Data araştırma/audit satırı.
- 11 strict uygun, 169 fail-closed.
- Uygun ortalama kaynak güveni: 98.80/100.
- 29 otorite grubu araştırıldı; 6 otorite grubu strict uygun kayıt üretti.
- Web görünümü: 180 aday satırı + 1,260 QA işlem satırı.
- Direct protokol: 19 unique aday, 24 çağrı, 14 PASS, 5 retry-sonrası FAIL, 5 tek güvenli retry, üçüncü retry 0.
- Direct-PASS kalite dışlaması: 3.
- Search-only promotion: 0.

## Strict uygun örnekler
BR00099 (2426), BR00190 (1989), BR00268 (7), BR3 (30–44), UBLR/17/008 (9–15), BLR144 (23), BLR159 (6), SA105 (100), 20/02203/F (6), BLR30 (71–303), BLR70 (144).

## Güçlendirilen resmî kanallar
London Borough of Brent; Central Bedfordshire Council; Uttlesford District Council; London Borough of Lambeth; Bristol City Council; Coventry City Council.

## Fail-closed kalite örnekleri
- BR00003: direct entity ile search snapshot arasında source-version/entry-date çelişkisi.
- 7632: structured maximum net dwellings yok.
- 3105: eski izin tarihi nedeniyle currentness semantiği konservatif biçimde reddedildi.
- BR00008, BR00180, LBBD75/CH, LBBD96/WB, BFR_0030: bir güvenli retry sonrasında direct readback başarısız.

## Canonical
İki bounded exact repository araması bu dalgada 0 eşleşme verdi. Kümülatif audit 253/0. Canonical 61,523–92,283 export, stable parcel identity/geometry, row-count receipt ve CRS declaration hâlâ bulunmadı. Bu veri-yokluğu kullanıcı eylemi değildir; `NO_DATA_CONTINUE` sürer.

Canonical parcel assignment, nearest-parcel inference, future-growth score, DB write, migration veya production deploy yapılmadı.