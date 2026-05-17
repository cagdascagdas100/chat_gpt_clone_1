# TerraYield/AAYS Review-Gate Freeze Mode

Bu klasor review-gate entegrasyonu icin freeze-mode dokumantasyon paketidir.

Kapsam:
- Read-only guvenlik sertlestirmesi
- Endpoint contract dokumantasyonu
- Insan evidence review SOP/checklist
- GO/NO-GO tablosu

Kesin yasaklar:
- production_acceptance_gate acilmayacak
- DB write/scoring promotion yapilmayacak
- evidence_checked=yes ve verified polygon/source olmadan accept/high-confidence onerilmeyecek
- review-gate disi feature konularina girilmeyecek

Beklenen sistem durumu:
- production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT
- can_production_auto_accept: false
- safe_output_gate: READY_FOR_HUMAN_EVIDENCE_REVIEW
