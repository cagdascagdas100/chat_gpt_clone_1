# Review-Gate Endpoint Contract

## GET /api/review/gates
- production_acceptance_gate daima NOT_READY_FOR_AUTO_ACCEPT kalir.
- can_production_auto_accept daima false kalir.
- evidence_checked_yes=0 ise production gate acilamaz.
- all_required_files_present sadece dosya varligini gosterir; kabul anlami tasimaz.

## GET /api/review/status/by-listing/{listing_id}
- Listing ID uzerinden review, risk ve evidence durumunu dondurur.
- risk_label_v2 sadece inceleme onceligidir.
- acceptance_status_strict=manual_review ise UI kabul edilmis gibi gostermemelidir.
- has_source_url=true tek basina verified degildir.
- checked=no ise evidence verified degildir.

## GET /api/review/status/{verification_id}
- Verification ID uzerinden fail-closed status bilgisi dondurur.
- Bilinmeyen kayitlarda production gate kapali kalir.

## GET /api/review/risk-preview/{verification_id}
- Risk preview bilgisi verir; kabul karari vermez.

## GET /api/review/tracking/{verification_id}
- Insan evidence review tracking durumunu verir.
- checked=yes sadece gercek insan kanit kontrolunden sonra verilebilir.
