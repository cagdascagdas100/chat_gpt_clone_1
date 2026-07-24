# ReadyToSell 3 — Çoklu İş ve Canlı Kaynak Hazırlığı

- SLOT_ID: `ready_to_sell_3`
- Parsel aralığı: `61523-92283`
- Task: `aays1-ready-to-sell-3-automation-167-dom-proof-20260720`
- Queue attempt: `ready-to-sell-3-20260720-003`
- Queue status: `pending`
- Runner pickup: `not_observed`

## Genişletilen çalışma

Tek shard worker aşağıdaki işleri aynı çalışmada yapacak:

1. Task 155 business state readback; terminal task replay yok.
2. Automation 167 gerçek headless-browser DOM acceptance.
3. En fazla üç eşzamanlı HTTP isteğiyle beş canlı kaynak doğrulaması.
4. Her başarılı cevap için SHA256 ve beklenen metin işaretleri.
5. Kaynak doğruluğu ile parsel/geometri doğruluğunu ayrı tutma.
6. Canonical parsel ve geometri kanıtı olmayan adayı dataset'e yükseltmeme.
7. Shard web görünümünde işlem ve adayları satır satır yayımlama.
8. Tek coordinator ile seri commit, push ve remote readback.

## İnternetten doğrulanan örnek hedefler

- 1 Springvale Terrace, London W14 0AE — canlı doğrudan satış ilanı; GBP 6,250,000; freehold; 18 konut sinyali.
  - https://www.rightmove.co.uk/properties/762013672911873
- 44-45 The Broadway, Ealing W5 5JU — canlı satış indeksinde GBP 3,750,000 ve residential-led planning permissions.
  - https://www.rightmove.co.uk/commercial-property-for-sale/W5.html
- St Clare Court, Hampton Hill TW12 — Savills doğrudan ilanı; under offer; 2.12 acre; 100 homes; planlama ref 22/2204/FUL.
  - https://search.savills.com/property-detail/b5599839-9b12-43a3-8daf-b6f1aa6da90e
- 22 & 24 Woodborough Road, London SW15 — canlı doğrudan ilan; GBP 4,000,000; iki lot.
  - https://www.rightmove.co.uk/properties/166553672
- 22-24 Woodborough Road resmi planlama geçmişi — Wandsworth Council; 2019/2331 approved with conditions ve 2024/0589 kaydı.
  - https://planning.wandsworth.gov.uk/Northgate/PlanningExplorer/Generic/StdDetails.aspx?DAURI=PLANNING&FT=Planning+Application+Details&PARAM0=518807&PT=Planning+Applications+On-Line&PUBLIC=N&TYPE=PL%2FPlanningPK.xml&XMLSIDE=&XSLT=%2FNorthgate%2FPlanningExplorer%2FSiteFiles%2FSkins%2FWandsworth%2Fxslt%2FPL%2FPLDetailsSiteHistory.xslt

## Beklenen web çıktısı

`england_map_web/data/aays_21_slots/ready_to_sell_3/index.html`

Bu sayfa işlem olaylarını, adayları, HTTP sonucu, response hash, marker sayısı, kaynak doğruluğu ve promotion blocker alanlarını satır satır gösterecek.

## Güvenlik ve doğruluk

- Araştırma adayı sayısı: 4 satış adayı + 1 resmi planlama kanıtı.
- Dataset'e yükseltilen: 0.
- Parsel eşleşme doğruluğu: henüz ölçülmedi; `0`, `not_run`.
- Kaynak doğruluğu ve parsel doğruluğu birbirine karıştırılmayacak.
- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`

## Gerçek blocker

`WAITING_CANONICAL_SINGLE_COORDINATOR_PICKUP; CURRENT_TASK_IDLE; QUEUE_PENDING`
