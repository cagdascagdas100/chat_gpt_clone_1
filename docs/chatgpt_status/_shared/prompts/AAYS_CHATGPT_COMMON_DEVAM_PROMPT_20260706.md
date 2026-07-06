# AAYS / TerraYield - Ortak Devam Promptu 20260706

Bu promptu her ChatGPT sayfasina aynen yapistir. Kullanici daha sonra sadece "devam" derse asagidaki kurallarla devam et.

Repo:
- cagdascagdas100/chat_gpt_clone_1

Branch:
- codex/aays-single-runner-v5-20260706

Aktif local workspace:
- C:\AAYS_WT\AAYS_REPAIR_20260706_1738

Tek runner kuralı:
- Sadece shared/canonical runner kullanilacak.
- Yeni runner, paralel runner, sayfaya ozel runner, ikinci PowerShell loop acma.
- Runner baslatmak gerekiyorsa sadece root launcher kullan:
  - START_AAYS_SINGLE_RUNNER_PANEL.cmd
  - START_AAYS_RUNNER.bat
  - AAYS_RUNNER_BASLAT.bat
  - RUN_AAYS_SINGLE_RUNNER_PANEL.cmd
- Bu launcher zaten lock kontrolu yapar; runner aktifse ikinci runner acmaz.
- V5 runner'i dogrudan elle baslatma; bootstrap/launcher uzerinden git.

Ilk okunacak dosyalar:
- docs/chatgpt_status/_shared/status/codex_single_runner_panel_repair_result_20260706.json
- docs/chatgpt_status/_shared/status/remaining_actions_decision_20260706.json
- docs/chatgpt_status/_shared/panel/page_status_index_latest.json
- docs/chatgpt_status/_shared/reports/SINGLE_RUNNER_PANEL_AND_NEW_PAGE_FLOW_FINAL_20260706.md
- docs/chatgpt_status/_shared/prompts/AAYS_CHATGPT_COMMON_DEVAM_PROMPT_20260706.md

"Devam" denince yapilacaklar:
1. Kendi page_key'ini onceki sayfa baglamindan veya panel index'teki ilgili satirdan belirle.
2. Page_key bilinmiyorsa yeni runner acma ve fake is uretme; page_key_missing blocker yaz.
3. Sadece kendi page_key klasorune yaz:
   - docs/chatgpt_status/<PAGE_KEY>/queue/
   - docs/chatgpt_status/<PAGE_KEY>/status/
   - docs/chatgpt_status/<PAGE_KEY>/heartbeat/
   - docs/chatgpt_status/<PAGE_KEY>/reports/
   - docs/chatgpt_status/<PAGE_KEY>/completed/
   - docs/chatgpt_status/<PAGE_KEY>/blocked/
4. Queue task gerekiyorsa docs/chatgpt_status/_shared/templates/NEW_CHATGPT_PAGE_QUEUE_TEMPLATE_20260706.json sablonunu kullan.
5. Task dosyasinda zorunlu alanlari gercek degerle doldur:
   - task_id
   - page_key
   - status=pending veya queued
   - target_branch=codex/aays-single-runner-v5-20260706
   - script_path veya automation_script
   - allowed_paths
   - expected_outputs
   - safety.fake_data=false
   - safety.db_write=false
   - safety.migration=false
   - safety.production_deploy=false
   - safety.final_ready_must_be_evidence_based=true
6. Eksik script_path, automation_script, allowed_paths veya safety flag varsa bunlari kendi page_key icinde gercek dosya/gercek izinle tamamla.
7. Kabul kriteri gercek output/GitHub kaniti ile saglanmadan completed, yüzde 100 veya final_ready=true yazma.
8. Gercek kanit yoksa status/report/blocked dosyasina acik blocker yaz ve final_ready=false birak.

Gerekli eksikler:
- Kendi page_key'indeki queue contract eksikleri.
- Kendi page_key'indeki missing_script_path, missing_automation_script, missing_allowed_paths, queue_not_json_or_unreadable, missing expected output gibi gercek blockerlar.
- Kendi page_key'ine ait status/report/heartbeat kanit dosyalari.
- Panel index okumasini bozan JSON/contract hatalari.

Gereksiz veya bu asamada atlanacak isler:
- Main entegrasyonu. Main merge ayri is; bu promptla yapma.
- DB write, migration, production deploy.
- Fake data uretme.
- Sahte heartbeat, sahte completed, sahte yüzde 100, sahte final_ready=true.
- F: yolunu canonical yapmak.
- Shared runner sistemini yeniden tasarlamak.
- Baska page_key'in blockerlarini kendi sayfandan duzeltmeye calismak.
- 115 output metrigini gercek GitHub kaniti olmadan artirmak veya degistirmek.
- Push/fetch OOM veya stale hatasini saklamak.

Runner/panel yorumlama:
- Panel RUNNER AKTIF diyorsa queue/status kanitlarini takip et.
- Panel RUNNER BLOCKED diyorsa sadece kendi page_key blockerlarini cozmeye calis.
- Panel RUNNER CALISMIYOR veya STALE diyorsa, yeni runner scripti yazma; sadece mevcut root launcher'i kullan veya blocker yaz.
- already_running/runner_active gorursen bu basarili lock davranisidir; ikinci runner acma.

Cevap formati:
- Once kendi page_key'ini yaz.
- Sonra yaptigin dosya degisikliklerini yaz.
- Sonra gercek test/kanit sonucunu yaz.
- Son satirda su bayraklari bildir:
  final_ready=false, product_final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false
- Eger gercek kabul kriterleri tamamlandiysa final_ready sadece kanitla true olabilir; aksi halde false kalir.
