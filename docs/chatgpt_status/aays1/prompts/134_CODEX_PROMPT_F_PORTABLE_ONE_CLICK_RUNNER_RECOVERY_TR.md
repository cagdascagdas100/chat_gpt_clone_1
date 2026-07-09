# CODEX PROMPT — AAYS F Portable Tek Buton Runner Recovery

Bu görevi mevcut repo/branch üzerinde uygula.

Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `codex/aays-single-runner-v5-20260706`
PAGE_KEY: `aays1`
Canonical portable root: `F:\TerraYield_AAYS_Portable`
Runner repo: `F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707`

## Ana hedef

PC yeniden başlatıldığında, runner kapandığında veya F diski başka Windows PC'ye takıldığında, kullanıcı tek buton/tek CMD ile tüm AAYS runner yapısını ayağa kaldırabilsin.

Mevcut yapı bozulmayacak. Yeni/paralel runner açılmayacak. Sadece mevcut F portable single-runner sistemi toparlanacak, başlatılacak, test edilecek ve GitHub'a kanıt dosyaları push edilecek.

## Zorunlu kurallar

- Yeni runner sistemi kurma.
- Paralel runner başlatma.
- Tek lock, tek daemon, tek queue runner mantığını koru.
- Sahte `completed`, sahte `%100`, sahte `final_ready=true` yazma.
- `final_ready=false` kalacak.
- DB write, migration, production deploy yok.
- Lock dosyasını sadece gerçek çalışan runner PID için oluştur/güncelle.
- Stale lock varsa sadece PID canlı değilse temizle.
- Heartbeat gerçek runner döngüsünden üretilmeli; fake heartbeat yazma.
- GitHub'a push edilmemiş local rapor ChatGPT tarafından doğrulanamaz; bu nedenle her bootstrap/test raporu branch'e push edilmeli.

## Tek buton launcher gereksinimi

Aşağıdaki launcher sistemini oluştur veya mevcutsa düzelt:

1. Disk kökünde çalışacak launcher:
   - `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`
2. Aynı launcher'ın PowerShell backend'i:
   - `F:\TerraYield_AAYS_Portable\runner_system\scripts\START_AAYS_PORTABLE_SINGLE_RUNNER.ps1`
3. Launcher bulunduğu diskten portable root'u otomatik algılamalı:
   - CMD içinde `%~dp0`
   - PowerShell içinde `$PSScriptRoot` / script parent path
   - Drive letter değişse bile portable root göreli yoldan bulunmalı.
4. Env set edilmeli:
   - `AAYS_PORTABLE_ROOT=<detected portable root>`
   - `AAYS_REPO_ROOT=<portable root>\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707`
   - `AAYS_RUNNER_WORKROOT=<portable root>\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES`
5. Başlatma öncesi doğrulama:
   - Git var mı?
   - Repo klasörü var mı?
   - Branch doğru mu?
   - Remote erişilebilir mi?
   - Queue klasörleri var mı?
   - Lock var mı?
   - Lock PID canlı mı?
6. Başlatma davranışı:
   - Lock PID canlıysa ikinci runner açma; mevcut runner aktif kabul et ve sadece status yaz/push et.
   - Lock stale ise lock'u temizle, sonra tek runner başlat.
   - Heartbeat eskiyse runner döngüsünü başlat veya mevcut PID ile heartbeat yenile.
   - Queue scan yap.
   - PAGE_KEY `aays1` queue/status/report dosyalarını kontrol et.

## GitHub proof/output sözleşmesi

Her açılışta ve self-test sonunda bu dosyalar GitHub branch'e push edilecek:

- `docs/chatgpt_status/aays1/status/130_f_portable_one_click_recovery_bootstrap_latest.json`
- `docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json`
- `docs/chatgpt_status/_shared/locks/single_runner.lock`
- `docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json`
- `docs/chatgpt_status/aays1/status/132_f_portable_runtime_self_check_latest.json`
- `docs/chatgpt_status/aays1/status/134_f_portable_one_click_recovery_test_latest.json`
- `docs/chatgpt_status/aays1/reports/134_f_portable_one_click_recovery_test_report.md`

ChatGPT bu dosyaları GitHub `fetch_file` ile kontrol edebilmeli. Bu nedenle dosyalar localde kalmamalı; commit + push kanıtı olmalı.

## Açılış self-test içeriği

`134_f_portable_one_click_recovery_test_latest.json` şu alanları içermeli:

```json
{
  "page_key": "aays1",
  "status": "one_click_recovery_test_done",
  "portable_root_detected": "...",
  "repo_root_detected": "...",
  "branch": "codex/aays-single-runner-v5-20260706",
  "git_remote_ok": true,
  "single_runner_lock_exists": true,
  "single_runner_lock_pid": 1234,
  "single_runner_lock_pid_alive": true,
  "heartbeat_exists": true,
  "heartbeat_runner_active": true,
  "heartbeat_fresh_within_5m": true,
  "queue_scan_ok": true,
  "aays1_queue_count": 0,
  "latest_aays1_status_path": "...",
  "github_push_ok": true,
  "chatgpt_can_verify_from_github": true,
  "final_ready": false,
  "fake_data": false,
  "db_write": false,
  "migration": false,
  "production_deploy": false
}
```

## Kabul kriterleri

- Kullanıcı herhangi bir Windows PC'de F diski takıp tek CMD'ye çift tıklayınca runner ayağa kalkmalı.
- Zaten çalışan runner varsa ikinci runner açılmamalı.
- PID canlılığı lock dosyasından doğrulanmalı.
- Heartbeat güncel olmalı.
- Bootstrap F portable yolu göstermeli.
- Test raporu GitHub'a push edilmeli.
- ChatGPT GitHub üzerinden şu üç şeyi doğrulayabilmeli:
  1. Runner canlı mı?
  2. Lock PID canlı mı?
  3. Son output/report GitHub'a geldi mi?
- Problem varsa `BLOCKED` veya `PARTIAL` status yaz, ama sahte başarı yazma.

## Beklenen final çıktı

Uygulama bitince şu dosyaları üret ve push et:

- `docs/chatgpt_status/aays1/status/134_f_portable_one_click_recovery_test_latest.json`
- `docs/chatgpt_status/aays1/reports/134_f_portable_one_click_recovery_test_report.md`
- Gerekirse güncellenmiş launcher/script dosyaları.

Rapor kısa olsun: ne düzeltildi, hangi dosyalar üretildi, GitHub push çalıştı mı, runner sağlıklı mı, kalan blocker var mı.
