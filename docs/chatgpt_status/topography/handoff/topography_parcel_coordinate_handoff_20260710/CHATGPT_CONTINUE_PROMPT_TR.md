# AAYS / TerraYield — Topography Height Difference Devam Promptu

Bu ZIP'i oku ve sadece Topography / Height Difference görevine devam et. Gas Emissions dosyalarını dikkate alma.

Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `codex/aays-single-runner-v5-20260706`
Page key: `topography`
Canonical runner: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`
Canonical repo: `F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707`

Kesin kurallar:
- Yeni runner açma.
- Paralel runner isteme.
- F portable tek shared runner kullanılacak.
- C:\ canonical kabul etme.
- Sahte koordinat yazma.
- Sahte boundary/geometry yazma.
- Sahte elevation yazma.
- Sahte completed, sahte %100, sahte final_ready=true yazma.
- final_ready=false kalacak.
- fake_data=false, db_write=false, migration=false, production_deploy=false kalacak.

Önce GitHub'dan şu dosyaları oku:
- `docs/chatgpt_status/topography/current_task/topography_current_task_20260703.json`
- `docs/chatgpt_status/topography/schemas/topography_site_update_schema_20260703.json`
- `england_map_web/data/program_layer_matrix/topography.geojson`
- `docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv`
- `outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json`
- `docs/chatgpt_status/topography/status/136_topography_height_difference_source_rows_latest.json`
- `docs/chatgpt_status/_shared/queue/topography_136_height_difference_source_rows_20260710.task.json`

Runner proof dosyalarını da oku:
- `docs/chatgpt_status/aays1/status/134_f_portable_one_click_recovery_test_latest.json`
- `docs/chatgpt_status/aays1/status/130_f_portable_one_click_recovery_bootstrap_latest.json`
- `docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json`
- `docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json`
- `docs/chatgpt_status/_shared/locks/single_runner.lock`

Runner sağlıklı değilse sadece şunu söyle:
`F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd dosyasına çift tıkla, sonra bu sayfaya devam yaz.`

Devam işi:
1. Gerçek `parcel_id`, `parcel_ref`, `centroid_lat`, `centroid_lon` ve varsa boundary/geometry kaynağını bul.
2. Koordinatın hangi dosyadan geldiğini açık yaz.
3. Boundary yoksa uydurma; sadece centroid varsa centroid yaz.
4. Hiç koordinat yoksa blocker yaz.
5. En az 3 gerçek parsel için starter batch oluştur.
6. Yükseklik ancak gerçek DEM/terrain kaynakla hesaplanabiliyorsa doldur; hesaplanamıyorsa fake elevation yazma.
7. Status/output dosyalarında `final_ready=false` ve `fake_data=false` koru.

Mevcut handoff sonucu: koordinat kaynağı bulunamadı; exported_parcel_count=0, starter_batch_candidate_count=0.
