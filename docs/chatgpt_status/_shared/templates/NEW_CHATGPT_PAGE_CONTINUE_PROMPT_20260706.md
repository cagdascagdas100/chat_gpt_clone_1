# AAYS / TerraYield Continue Prompt 20260706

Bu sayfada sadece devam et.

Repo:
C:\Users\cagda\Documents\GitHub\AAYS

Kurallar:
- C: ana proje yoludur. Proje dosyalarini silme.
- F: sadece kopya/test alani olarak kabul edilir.
- Tek runner kullan: docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1
- Canonical V5 runner: docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1
- Panel index: docs/chatgpt_status/_shared/panel/page_status_index_latest.json
- Her sayfa icin heartbeat: docs/chatgpt_status/<PAGE_KEY>/status/heartbeat_latest.txt
- final_ready=true yazma; sadece gercek, push edilmis ve kanitli output varsa final_ready true olabilir.
- fake_data, db_write, migration, production_deploy false kalmali.

Baslatma:
1. Kokteki AAYS_RUNNER_BASLAT.bat veya RUN_AAYS_SINGLE_RUNNER_PANEL.cmd dosyasini kullan.
2. Ucuz kontrolleri calistir: PowerShell syntax, /health, /england_map_web/, /openapi.json.
3. Kuyruk varsa sadece allowed_paths icindeki dosyalara yaz.
4. Yapilamayanlari blocker olarak docs/chatgpt_status/_shared/blocked altina yaz.

Devam komutu:
Sadece devam et.
