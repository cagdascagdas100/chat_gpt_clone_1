# Topography site-visible update folder

Bu klasor matrix kontrol sayfasinda gorunen Topography guncelleme ozetini tasir.

Kontrol sayfasi:

```text
http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260630-final
```

Ana dosya:

```text
latest_changes.json
```

Bu dosya ChatGPT + tek shared runner tarafindan gercek kaynaklarla guncellenmelidir.

Sahte veri yazilmaz. Gercek kaynak, AI assurance ve browser smoke kaniti yoksa `final_ready=false` kalir.

Yeni ChatGPT handoff dosyalari:

```text
docs/chatgpt_status/topography/current_task/topography_current_task_20260703.json
docs/chatgpt_status/topography/chatgpt_prompt/TOPOGRAPHY_CHATGPT_FINAL_PROMPT_20260703.md
docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv
docs/chatgpt_status/topography/automation/topography_single_runner_bridge_20260703.ps1
```
