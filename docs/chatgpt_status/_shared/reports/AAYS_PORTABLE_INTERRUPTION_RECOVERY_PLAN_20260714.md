# AAYS Portable Kesinti Recovery Planı - 20260714

## Uygulanan minimal mimari

- ProgramData üzerinde yalnız sağlık/orchestration yapan tek guardian.
- F portable disk üzerinde mevcut tek canonical runner.
- Guardian veri üretmez, queue yazmaz, worktree oluşturmaz.
- Disk kimliği sırası: volume GUID, volume serial/label, portable marker, fallback root.
- Tek Windows görevi: `AAYS Portable Runner Guardian`.
- Tetikleyiciler: kullanıcı logon, Power-Troubleshooter resume EventID 1, dakikalık self-heal tetikleyicisi.
- Task ve guardian mutex politikası: `IgnoreNew` + global/local named mutex.
- Ağ retry: 15, 30, 60, 120, en fazla 300 saniye.
- Disk stabilite süresi: 12 saniye.
- Lock doğrulaması: canlı PID + process başlangıç zamanı + canonical command line.
- Kritik Git yazma durumu varsa runner başlatılmaz.
- 5x5/25 görev planı uygulanmadı.

## Dosyalar

- `docs/chatgpt_status/_shared/automation/AAYS_PORTABLE_RESUME_GUARDIAN.ps1`
- `docs/chatgpt_status/_shared/automation/INSTALL_AAYS_PORTABLE_RESUME_GUARDIAN.ps1`
- `docs/chatgpt_status/_shared/config/AAYS_PORTABLE_RESUME_GUARDIAN.json`
- F root launcher: `RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.ps1`
- ProgramData runtime: `C:\ProgramData\AAYS\portable_runner_guardian.ps1`
- ProgramData state: `C:\ProgramData\AAYS\guardian_state.json`
- Rollback XML: `C:\ProgramData\AAYS\legacy_single_runner_task.xml`

## Başka PC akışı

F diskteki `RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd` tıklanır. Guardian task yoksa launcher aynı diskteki installer'ı bir kez çalıştırır. Installer volume/marker kimliğini yeni PC'ye kaydeder, tek guardian task kurar ve mevcut canonical runner'ı açar.

## Güvenli manuel test rehberi

1. Disk testi: yalnız runner idle ve `current.task` terminal durumdayken diski çıkar. `C:\ProgramData\AAYS\guardian_state.json` içinde `waiting_for_portable_disk` bekle. Disk geri gelince en az 15 saniye bekle ve `runner_healthy` doğrula.
2. Ağ testi: interneti normal Windows arayüzünden kes; runner kapanmamalı ve durum `waiting_for_network` olmalı. Geri getirince aynı task/checkpoint devam etmeli.
3. Uyku testi: aktif yazma yokken bilgisayarı uyut/uyandır. Canlı PID varsa korunmalı; ölü PID varsa guardian tek runner başlatmalı.

Aktif Git yazması veya aktif veri publish sırasında fiziksel disk çıkarma testi yapılmaz.

## Geri alma

`INSTALL_AAYS_PORTABLE_RESUME_GUARDIAN.ps1 -Uninstall -RestoreLegacyTask`

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
