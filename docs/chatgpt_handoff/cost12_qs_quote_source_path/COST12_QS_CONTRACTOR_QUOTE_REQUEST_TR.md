# COST12 QS / Contractor Quote Request — Retail Mid UK

Amaç:
COST12 production-ready kapanışı için `retail / mid / UK / cost_uk_v1` rate-card satırını doğrulanmış QS/contractor quote kaynağıyla üretmek.

## İstenen veri

Lütfen aşağıdaki kapsam için GBP per gross internal area m² maliyet benchmarkı veya aralığı verin:

- Building type: retail / shop / restaurant
- Specification grade: mid specification
- Region: UK average veya belirttiğiniz UK bölgesi
- Unit: GBP per gross internal area m²
- Date basis: YYYY-MM
- Scope: shell / fit-out / shell + fit-out açıkça belirtilecek
- Included/excluded: preliminaries, fees, MEP, kitchen/cooling, VAT, contingency, design/professional fees

## Gerekli cevap formatı

- company_or_person:
- qualification_or_role:
- quote_date:
- applicable_region:
- applicable_scope:
- area_basis: GIA / NIA / other
- low_rate_gbp_per_m2:
- mid_rate_gbp_per_m2:
- high_rate_gbp_per_m2:
- recommended_rate_gbp_per_gia_m2:
- source_document_or_email_reference:
- applicability_note:
- exclusions:
- confidence_note:

## Kullanım

Bu bilgi yalnız TerraYield AAYS COST12 rate-card production candidate satırı için kullanılacak.
DB write, deploy veya migration yapılmadan önce read-only doğrulama çalıştırılacak.
