# Tek Runner Is Akisi

Page key: distance_property_types

F repo: F:\chatgpt\chat_gpt_clone_1_main

Repo queue dosyasi:
F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\queue\<task_id>.task.json

Live runner queue:
C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue\pending\<task_id>.task.json

Beklenen script yolu:
F:\chatgpt\chat_gpt_clone_1_main\docs\chatgpt_status\distance_property_types\automation\distance_property_types_batch_runner.ps1

Devam mantigi:

1. Son raporu oku.
2. Eksik batch varsa yeni task hazirla.
3. Taski repo queue ve live pending queue icin kullan.
4. Tek shared runner disinda yeni runner acma.
5. Runner sonucunu rapora yaz.
6. Kanit yoksa final_ready=false kalir.

Task safety flags her zaman false olmalidir: fake_data, db_write, ddl, migration, production_deploy.
