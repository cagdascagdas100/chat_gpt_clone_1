# AAYS Tek Tuş Runner Recovery + GitHub Smoke Test Raporu

## Amaç

F portable kontrol panelindeki **Tek Runner Başlat** düğmesi tek tıklamayla aşağıdaki işlemlerin tamamını gerçek kanıtla yapmalıdır:

1. Canonical F portable repo/branch/launcher doğrulaması.
2. Mevcut runner PID, lock, heartbeat ve panel PID tutarlılık kontrolü.
3. Canlı runner varsa ikinci runner açmama.
4. Runner yoksa veya gerçekten ölü/stale ise güvenli recovery yapıp yalnızca tek runner başlatma.
5. Yeni heartbeat'in taze olduğunu ve PID/lock/heartbeat değerlerinin eşleştiğini doğrulama.
6. Gerçek runner üzerinden küçük bir smoke-test dosyası üretme.
7. Smoke-test dosyasını hedef GitHub branch'ine commit ve push etme.
8. Remote branch'ten dosyayı geri okuyarak push/readback doğrulaması yapma.
9. Panelde PASS/FAIL, dosya yolu, commit SHA, PID, heartbeat zamanı ve blocker bilgisini gösterme.

## Sabitler

- Repo: `cagdascagdas100/chat_gpt_clone_1`
- Branch: `codex/aays-single-runner-v5-20260706`
- Portable root: `F:\TerraYield_AAYS_Portable`
- Repo root: `F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707`
- Canonical launcher: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`
- Tek runner zorunlu.

## Mevcut Problem Kanıtı

Panel yeni PID gösterebilmesine rağmen GitHub heartbeat dosyası eski PID/zaman gösterebiliyor. Ayrıca `processed_task_count=0` kalıyor. Bu nedenle yalnızca panelde `AKTIF` yazması başarı kabul edilmemelidir.

## Tek Tuş Akışı

### A. Ön kontroller

Düğmeye basıldığında panel aşağıdaki kontrolleri satır satır göstermelidir:

- F portable root mevcut mu?
- Repo root mevcut ve git worktree mi?
- Aktif branch doğru mu?
- Remote doğru repo mu?
- Rebase/merge durumu var mı?
- Working tree dirty mi?
- Lock dosyası var mı?
- Lock PID gerçekten canlı mı?
- Heartbeat yaşı kaç saniye?
- Heartbeat PID, lock PID ve panel PID eşleşiyor mu?
- Başka runner PID'si var mı?

### B. Güvenli recovery

- Canlı ve tutarlı runner varsa `existing_runner_active_no_new_bootstrap=true` ile mevcut runner kullanılmalı.
- Lock PID ölü ise stale lock temizlenebilir.
- Lock PID canlıysa lock silinmemeli ve ikinci runner açılmamalı.
- Dirty worktree varsa isimli stash oluşturulmalı; başarı doğrulanmadan stash silinmemeli.
- Pull/rebase işlemi başarısızsa sahte başarı yazılmamalı.
- PID/lock/heartbeat uyuşmazlığı çözülmeden smoke test başlatılmamalı.

### C. Taze runner kanıtı

Başarı için bütün koşullar birlikte sağlanmalıdır:

- `runner_active=true`
- `pid_alive=true`
- `lock_valid=true`
- Heartbeat yaşı en fazla 60 saniye
- Panel PID = lock PID = heartbeat PID
- Launcher path canonical F portable path
- Branch hedef branch

### D. Gerçek smoke-test

Runner, normal backlog'dan bağımsız fakat **aynı tek runner içinde**, öncelikli bir kontrol görevi olarak küçük bir dosya üretmelidir.

Sabit ChatGPT-okunabilir artifact yolu:

`docs/chatgpt_status/_shared/smoke_tests/one_click_runner_smoke_latest.json`

Dosya en az şu alanları içermelidir:

```json
{
  "schema_version": "1.0",
  "test_name": "one_click_runner_github_roundtrip",
  "status": "PASS",
  "generated_by_real_runner": true,
  "run_id": "unique_timestamp_or_uuid",
  "generated_at_utc": "ISO-8601",
  "runner_pid": 0,
  "lock_pid": 0,
  "heartbeat_pid": 0,
  "heartbeat_age_seconds": 0,
  "portable_root": "F:\\TerraYield_AAYS_Portable",
  "repo_root": "F:\\TerraYield_AAYS_Portable\\runner_system\\AAYS_WT\\AAYS_RUNNER_HEALTHY_20260707",
  "branch": "codex/aays-single-runner-v5-20260706",
  "launcher_path": "F:\\TerraYield_AAYS_Portable\\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd",
  "payload": "AAYS_ONE_CLICK_RUNNER_SMOKE_OK",
  "remote_readback_ok": true,
  "single_runner_only": true,
  "new_runner": false,
  "parallel_runner": false,
  "fake_data": false,
  "final_ready": false,
  "db_write": false,
  "migration": false,
  "production_deploy": false
}
```

Bu dosya launcher/panel tarafından doğrudan üretilmiş gibi gösterilmemelidir; `generated_by_real_runner=true` ancak gerçek runner process'i dosyayı yazdıysa kullanılmalıdır.

### E. Push ve remote readback kanıtı

Smoke artifact için:

1. Runner dosyayı oluşturmalı.
2. Runner dosyayı commit etmeli.
3. Runner hedef branch'e push etmeli.
4. Push sonrası remote branch fetch edilmeli.
5. `git show origin/codex/aays-single-runner-v5-20260706:docs/chatgpt_status/_shared/smoke_tests/one_click_runner_smoke_latest.json` ile remote readback yapılmalı.
6. Readback içindeki `run_id` ve payload, local üretilen değerle birebir eşleşmeli.

Push kanıtı için ayrıca şu dosya üretilebilir:

`docs/chatgpt_status/_shared/smoke_tests/one_click_runner_smoke_push_proof_latest.json`

Bu proof dosyasında ilk artifact commit SHA, push sonucu ve remote readback sonucu bulunmalıdır.

## Panelde Gösterilecek Sonuç

Panel aşağıdaki alanları göstermelidir:

- Runner recovery: PASS/FAIL
- Single runner check: PASS/FAIL
- PID alignment: PASS/FAIL
- Fresh heartbeat: PASS/FAIL
- Git pull/sync: PASS/FAIL
- Smoke artifact write: PASS/FAIL
- Git commit: PASS/FAIL
- Git push: PASS/FAIL
- Remote readback: PASS/FAIL
- Artifact repo path
- Commit SHA
- Son blocker

Panelde sadece tüm acceptance koşulları sağlanırsa yeşil `ONE_CLICK_RUNNER_SMOKE_PASS` gösterilmelidir.

## Başarısızlık Davranışı

Herhangi bir adım başarısızsa:

- Sahte PASS/completed/%100 yazma.
- İkinci runner açma.
- Hata adımı, exit code, stderr özeti ve önerilen recovery adımı panelde göster.
- Mümkünse blocker dosyasını şu konuma yaz ve push et:
  `docs/chatgpt_status/_shared/blockers/one_click_runner_blocker_latest.json`
- `final_ready=false` bırak.

## Kabul Kriterleri

- Tek düğmeye bir kez basılması bütün akışı başlatır.
- Aynı düğmeye tekrar basılması ikinci runner oluşturmaz.
- Panel PID, lock PID ve heartbeat PID eşleşir.
- Heartbeat tazedir.
- Smoke dosyası gerçek runner tarafından üretilmiştir.
- Smoke dosyası GitHub hedef branch'inde bulunur.
- Remote readback başarılıdır.
- ChatGPT GitHub connector ile sabit artifact yolunu okuyabilir.
- İşlem hiçbir DB write, migration veya production deploy yapmaz.
- `fake_data=false` ve `final_ready=false` korunur.
