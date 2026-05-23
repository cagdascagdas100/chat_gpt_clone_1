# 9.1 Contractor Post-Final Eksik Denetim Planı

Bu plan, 9.1 Contractor sayfasında görünen %100 kapanışın gerçek kanıt dosyalarıyla doğrulanması için açılmıştır.

## Neden yeniden açıldı?

Final task `project-100-finalized-20260523` %100 ve `finished` görünmektedir. Ancak `ai-results/r17_scan.txt` final snapshot içinde boş kalmıştır. Bu nedenle kapanış operasyonel olarak doğru olsa bile çıktı kalitesi bakımından ek audit gereklidir.

## Uygulanacak adımlar

1. Final durum dosyalarını yeniden oku:
   - ai-tasks/current-task.json
   - ai-tasks/.last-task-id
   - ai-heartbeat/portable-runner.md
   - docs/chatgpt_status/page_fragments/9.1 Contractor.json

2. 9.1 Contractor sonuç dosyalarını varlık ve içerik bakımından denetle:
   - ai-results/contractor010_min.result.json
   - ai-results/contractor011_min.result.json
   - ai-results/contractor012_min.result.json
   - ai-results/contractor013_min.result.json
   - ai-results/c14_read.result.json
   - ai-results/c15_read.result.json
   - ai-results/r16.result.txt
   - ai-results/r17_scan.txt
   - ai-results/project_100_finalize.result.json

3. Eksik/boş dosyaları risk olarak işaretle. Şu an bilinen risk: `r17_scan.txt` boş.

4. Database ve deployment kapsamını doğrula:
   - db_write=false kalacak.
   - production_deploy=false kalacak.
   - fake_data=false kalacak.
   - Bu audit DB yazmaz, production deploy yapmaz.

5. Codex entegrasyonu için kesin kabul kriteri üret:
   - Final %100 kapanış dosyaları mevcut olmalı.
   - Eksik/boş ara çıktı varsa Codex bunu tamamlandı kabul etmemeli.
   - R17 boşluğu çözülene kadar çıktı kalitesi `needs_review` sayılmalı.

## Hedef çıktı

Audit sonucunda şu dosyalar üretilecek:

- ai-results/contractor_post100_gap_audit.result.json
- ai-results/contractor_post100_gap_audit.report.md

## Geçici değerlendirme

Operasyonel kapanış: tamamlandı.
Kanıt kalitesi: ek denetim gerekli.
R17 scan: boş çıktı nedeniyle riskli.
