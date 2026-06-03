# CODEX HANDOFF — AAYS / TerraYield

Bu dosya Codex için hazırlanmış operasyonel handoff belgesidir. Amaç: ChatGPT konuşmasında yapılan runner, audit, doğrulama, dosya konumu ve entegrasyon işlerini Codex tarafında devam ettirebilmek ve projeye entegre edilecek adımları aynı mantıkla sürdürebilmektir.

## 1. Repo ve yerel klasörler

- GitHub bridge repo: `cagdascagdas100/chat_gpt_clone_1`
- Bridge root: `C:\Users\cagda\Documents\chat_gpt_clone_1`
- TerraYield project root: `C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence`
- ChatGPT page project: `aays1`
- Primary task file: `C:\Users\cagda\Documents\chat_gpt_clone_1\ai-tasks\current-task.json`
- Last task marker: `C:\Users\cagda\Documents\chat_gpt_clone_1\ai-tasks\.last-task-id`
- Result files: `C:\Users\cagda\Documents\chat_gpt_clone_1\ai-results\*.md`
- Heartbeat files: `C:\Users\cagda\Documents\chat_gpt_clone_1\ai-heartbeat\*.md`
- Runner logs: `C:\Users\cagda\Documents\chat_gpt_clone_1\ai-runner-logs\*.log`
- Task scripts: `C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\*.ps1`

## 2. Runner / PowerShell mimarisi

Bu konuşmada önce eski runner akışı düzeltildi, sonra otomatik çalıştırma zinciri kuruldu.

Ana runner dosyaları:

- `AAYS_CHATGPT_RUNNER_V4.ps1`
- `AAYS_AUTOPILOT_RUNNER_V5.ps1`
- `AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1`
- `AAYS_TASK_BRIDGE_CONFIG.ps1`

Önemli davranışlar:

- Runner GitHub’daki `ai-tasks/current-task.json` dosyasını izler.
- Görev ID’si `.last-task-id` ile farklıysa görevi çalıştırır.
- Çıktıyı `ai-results/` altına yazar.
- Heartbeat’i `ai-heartbeat/` altına yazar.
- Logları `ai-runner-logs/` altına yazar.
- Sonuçları GitHub’a commit/push eder.

Autopilot V5 desteklediği görev formatları:

```json
{
  "command": "PowerShell script text"
}
```

```json
{
  "script_path": "script-name-under-ai-task-scripts.ps1"
}
```

```json
{
  "action": "health_check"
}
```

```json
{
  "action": "status_check"
}
```

En güvenli format, hem V4 hem V5 tarafından çalışabildiği için `command` formatıdır:

```json
{
  "id": "example-task-id",
  "title": "Run example task",
  "progress": 0,
  "working_directory": "C:/Users/cagda/Documents/GitHub/AAYS/terrayield_land_intelligence",
  "timeout_seconds": 3600,
  "created_by": "Codex",
  "command": "$p = [IO.Path]::Combine($env:USERPROFILE,'Documents','chat_gpt_clone_1','ai-task-scripts','example.ps1'); & $p; exit $LASTEXITCODE"
}
```

## 3. Otomasyonun neden kurulduğu

Sorun: ChatGPT GitHub dosyalarını değiştirebiliyordu ama PC’deki PowerShell sürecini doğrudan başlatamıyordu. Bu yüzden PC’de sürekli açık kalacak bir runner gerekliydi.

Çözüm:

1. `AAYS_AUTOPILOT_RUNNER_V5.ps1` eklendi.
2. V5 runner yerelde başlatıldı.
3. V5 heartbeat GitHub’a push edildi.
4. `j236-v5-health` health check çalıştı ve `AAYS_AUTOPILOT_HEALTH=OK` döndürdü.
5. Sonraki görevler GitHub üzerinden queue edilip PowerShell tarafından çalıştırılabilir hale geldi.

## 4. Yapılan doğrulamalar ve sonuçlar

Önemli doğrulama sonuçları:

- `j230 closure audit`: `LONG_CLOSURE_AUDIT=100/100`, `PROGRAM_COMPLETION=100/100`
- `j234 final verifier`: `FINAL_VERIFIER=100/100`, `PROGRAM_COMPLETION=100/100`
- `terrayield-060-audit-scriptpath-final`: önce `PROGRAM_COMPLETION=99/100` verdi; tek hata `COMPILEALL_APP=FAIL` idi.
- `terrayield-063-pycache-prefix-command`: final düzeltme sonrası `COMPILEALL_APP=PASS`, `PYTEST_COLLECT=PASS`, `PASS_CHECKS=14`, `FAIL_CHECKS=0`, `LONG_CLOSURE_AUDIT=100/100`, `PROGRAM_COMPLETION=100/100` verdi.

Son kesin durum:

```text
PROGRAM_COMPLETION=100/100
LONG_CLOSURE_AUDIT=100/100
COMPILEALL_APP=PASS
PYTEST_COLLECT=PASS
PASS_CHECKS=14
FAIL_CHECKS=0
128 tests collected
```

## 5. Final audit’teki tek hata ve çözümü

Problem:

```text
PermissionError: app\schemas\__pycache__\cost.cpython-312.pyc...
COMPILEALL_APP=FAIL
```

Çözüm:

`PYTHONPYCACHEPREFIX` kullanıldı. Böylece Python bytecode cache çıktıları mevcut `__pycache__` klasörlerine yazılmak yerine ayrı bir klasöre yönlendirildi.

Eklenen script:

- `ai-task-scripts/terrayield_061_pycache_prefix_audit.ps1`

Script mantığı:

```powershell
$CacheRoot = Join-Path $ProjectRoot '.aays_pycache_compile'
$env:PYTHONPYCACHEPREFIX = $CacheRoot
python -m compileall app
python -m pytest tests --collect-only -q --ignore tests/facility-adapter-5qtl4e17
```

Başarılı final görev:

- Task ID: `terrayield-063-pycache-prefix-command`
- Result: `PROGRAM_COMPLETION=100/100`

## 6. Önemli dosya ve çıktı konumları

Bridge repo içindeki kalıcı konumlar:

- `CODEX_HANDOFF_AAYS_TERRAYIELD.md` — bu handoff dosyası
- `AAYS_AUTOPILOT_RUNNER_V5.ps1` — uzaktan görev çalıştırma runner’ı
- `AAYS_CHATGPT_RUNNER_V4.ps1` — eski/aktif runner
- `ai-tasks/current-task.json` — çalıştırılacak güncel görev
- `ai-tasks/.last-task-id` — son tamamlanan görev ID’si
- `ai-task-scripts/terrayield_061_pycache_prefix_audit.ps1` — pycache prefix final audit repair
- `ai-results/` — görev sonuçları
- `ai-heartbeat/autopilot-v5.md` — V5 heartbeat
- `ai-heartbeat/runner-v4.md` — V4 heartbeat
- `ai-runner-logs/` — runner logları

Project root içindeki önemli oluşan/kanıtlanan konumlar:

- `C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_pycache_compile`
- `C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app`
- `C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests`

Final audit’te kanıtlanan Plan L / paket çıktıları:

- `PLAN_L_FINAL_DIR_EXISTS=PASS`
- `PLAN_L_FINAL_ZIP_EXISTS=PASS`
- `PLAN_L_QA_REPORT_EXISTS=PASS`
- `PLAN_L_QA_WARNINGS_NONE=PASS`
- `PLAN_L_CLASSIFIED_34864=PASS`
- `PLAN_L_GEOJSON_34864=PASS`
- `SECURITY_EXPANSION_EXISTS=PASS`

Audit sayaçları:

```text
TOTAL_FILES=1253
HYPER_RELATED=823
ULTRA_RELATED=547
MEGA_RELATED=111
```

## 7. Database ve veri entegrasyon bilgisi

Bu konuşmada doğrudan canlı database credential’ı verilmedi ve kullanılmadı. Bu yüzden Codex gerçek secret üretmemeli veya uydurmamalıdır.

Kod/test kapsamından görünen database/entegrasyon katmanları:

- Supabase admin service
- Supabase parcel/admin record sync
- Supabase row ID generation
- Backend configured / not configured davranışları
- Parcel records, admin records, candidate-to-Supabase row mapping

Final test collect içinde şu Supabase testleri toplanmıştır:

- `tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_backend_filters`
- `tests/test_supabase_admin_service.py::test_list_supabase_parcel_records_uses_parcel_ref_or_filter`
- `tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_returns_saved_row`
- `tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_raises_when_backend_not_configured`
- `tests/test_supabase_sync.py::test_build_supabase_row_id_is_deterministic`
- `tests/test_supabase_sync.py::test_candidate_to_supabase_row_preserves_parcel_link_fields`
- `tests/test_supabase_sync.py::test_candidate_to_supabase_row_marks_unmatched_records_for_review`

Codex’in database tarafında yapması gerekenler:

1. Repo içinde `.env`, settings, config veya deployment secrets dosyalarını incele.
2. Supabase URL/key gibi secret varsa sadece mevcut güvenli kaynaklardan oku; yoksa kullanıcıdan iste.
3. Gerçek production credential yazma veya commit etme.
4. Supabase entegrasyonunu testlerdeki kontratlara göre bağla.
5. Backend configured değilse testlerdeki beklenen davranışı koru.
6. Her DB write işlemi için dry-run veya staging doğrulaması öner.

## 8. Codex için uygulama talimatı

Codex şu sırayla ilerlemeli:

1. `CODEX_HANDOFF_AAYS_TERRAYIELD.md` dosyasını oku.
2. `ai-results/` altındaki son audit sonucunu incele.
3. `ai-heartbeat/runner-v4.md` ve `ai-heartbeat/autopilot-v5.md` dosyalarından aktif runner durumunu doğrula.
4. `ai-tasks/current-task.json` ve `.last-task-id` dosyalarını karşılaştır.
5. Eğer yeni görev yazılacaksa V4/V5 uyumlu `command` formatını tercih et.
6. Proje kökünü `C:/Users/cagda/Documents/GitHub/AAYS/terrayield_land_intelligence` olarak kullan.
7. Testlerden önce şu iki komutu çalıştır:

```powershell
$env:PYTHONPYCACHEPREFIX = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_pycache_compile'
python -m compileall app
python -m pytest tests --collect-only -q --ignore tests/facility-adapter-5qtl4e17
```

8. Her sonuçta şu alanları raporla:

```text
COMPILEALL_APP=
PYTEST_COLLECT=
PASS_CHECKS=
FAIL_CHECKS=
PROGRAM_COMPLETION=
NEXT_ACTION=
```

## 9. Codex’e verilecek kısa başlangıç prompt’u

Aşağıdaki prompt’u Codex’e doğrudan ver:

```text
Bu repoda AAYS / TerraYield çalışmasının ChatGPT handoff dosyası var: CODEX_HANDOFF_AAYS_TERRAYIELD.md.
Önce bu dosyayı oku. Bridge repo: C:/Users/cagda/Documents/chat_gpt_clone_1. Project root: C:/Users/cagda/Documents/GitHub/AAYS/terrayield_land_intelligence.
Runner mimarisi GitHub current-task.json üzerinden çalışıyor. V4/V5 runner sonuçları ai-results, ai-heartbeat ve ai-runner-logs altında.
Son başarılı final audit: terrayield-063-pycache-prefix-command. Son durum PROGRAM_COMPLETION=100/100, LONG_CLOSURE_AUDIT=100/100, COMPILEALL_APP=PASS, PYTEST_COLLECT=PASS.
Database tarafında Supabase admin/sync katmanları test kapsamına giriyor; gerçek secret yoksa uydurma, kullanıcıdan veya güvenli env kaynağından al.
Yeni görev yazarken V4/V5 uyumlu command formatını kullan. Önce mevcut current-task ve .last-task-id dosyalarını kontrol et. Sonra proje entegrasyonu için güvenli, küçük, testlenebilir adımlar öner ve uygula.
```
