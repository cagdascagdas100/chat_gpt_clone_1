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
- DeepSeek/opencode destek ajanlari da ayni kurala tabidir: genis repo kokunu ajanlara actirarak `opencode run --model deepseek/... "..." F:\chat_gpt_clone_1` veya coklu paralel DeepSeek taramasi calistirma.
- DeepSeek ile yalniz dar dogrulama gerekiyorsa prompt once, dosyalar sonra olacak sekilde `--file` eklerini kullan veya hazir launcher'i calistir: `F:\OpenCode_Manager_Factory\Run_DeepSeek_AAYS_Parcel_Building_Type_Verify.cmd`.
- DeepSeek/opencode sureci "thinking" halinde takilirsa ayni isi yeni ajanlarla cogaltma; ilgili takili opencode surecini kapat, yalniz `--file` sinirli tek kontrollu tekrar yap.
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
9. Bu devam parcel_label_1/2/3 icin `parcel_building_type_classification_v1` ile ilgiliyse once `docs/chatgpt_status/_shared/AAYS_21_SLOT_AYRINTILI_DEVAM_SOZLESMESI_TR.md` bolum 6.2'yi ve `docs/chatgpt_status/aays1/queue/0000_030_parcel_label_<n>_parcel_building_type_classification_v1_20260808.task.json` dosyasini oku; yeni DeepSeek ajan taramasi baslatma.

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
## Runner Strategy Update 20260707

Current decision:
- Use the stable legacy worktree runner engine: docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1.
- Root launchers start docs/chatgpt_status/_shared/automation/RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1 through START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1.
- Do not call RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1 as the default continuation runner. V5 remains as evidence/diagnostic code only until separately repaired.
- The old V4 F-drive-only runner is not used directly because F is not canonical. The stable runner keeps the old worktree execution model but uses C:\AAYS_WT\AAYS_REPAIR_20260706_1738 as canonical.

When user says "devam":
1. Do not start a new or parallel runner.
2. Check docs/chatgpt_status/_shared/status/stable_runner_daemon_latest.json and docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json.
3. If daemon status is already_running or runner_started, do not start another one.
4. If no daemon is active, use START_AAYS_SINGLE_RUNNER_PANEL.cmd once.
5. Repair only your own page_key queue/status/report files.
6. Skip main integration, DB write, migration, production deploy, fake heartbeat, fake completed, fake 100 percent, fake final_ready=true, and unverified 115 metric changes.

## DeepSeek Safe Continuation Update 20260808

If the page previously failed or hung while running DeepSeek/opencode agents, continue with this bounded route:
- Do not run broad repo scans or parallel DeepSeek agents.
- Do not pass `F:\chat_gpt_clone_1` as the project/workspace for autonomous DeepSeek browsing.
- Use the existing Codex-local queue files as canonical, or run only `F:\OpenCode_Manager_Factory\Run_DeepSeek_AAYS_Parcel_Building_Type_Verify.cmd`.
- For manual `opencode run`, the safe argument order is: `opencode run --model deepseek/deepseek-v4-pro "PROMPT" --file=FILE1 --file=FILE2`.
- If a DeepSeek process exceeds the launcher timeout, terminate that process and report a timeout blocker instead of opening more agents.
