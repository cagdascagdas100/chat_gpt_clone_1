# Human Evidence Review SOP

1. Ilgili verification_id ve listing_id eslesmesini kontrol et.
2. /api/review/status/{verification_id} ve /api/review/status/by-listing/{listing_id} endpointlerini oku.
3. Source URL canonical ve erisilebilir mi kontrol et.
4. URL ayni listing/parsel kaydina mi ait kontrol et.
5. Postcode bilgisini kaynak, payload ve harita konumu ile karsilastir.
6. Local authority/council bilgisini karsilastir.
7. Polygon/boundary kaynaginin georeferenced ve kaynaktan dogrulanabilir oldugunu kontrol et.
8. Sadece gorsel tahmin polygon varsa verified sayma.
9. url_status, postcode_status, authority_status, polygon_status alanlarini gercek kanita gore doldur.
10. checked=yes sadece URL, postcode, authority ve polygon kaniti gercekten kontrol edildiyse ver.

checked=yes icin minimum kosullar:
- url_status=checked
- postcode_status=checked
- authority_status=checked veya kanitla makul dogrulanmis
- polygon_status=checked
- evidence_notes denetlenebilir sekilde dolu

Aksi durumda checked=no ve final_decision=needs_source veya ambiguous kalir.
