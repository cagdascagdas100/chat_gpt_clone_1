# AAYS Portable 15 Slot Host Hardening Result - 2026-07-18

## Status
PASS_WITH_EXTERNAL_FIRST_USE_STEPS

## Kullanım modeli
- Gerçek 15 ChatGPT akışı için 15 ayrı sayfa kullanılır.
- Mevcut beş sayfa ilgili projenin `_1` slotudur; on yeni sayfa `_2` ve `_3` slotlarıdır.
- Her sayfa ilk mesajda tek SLOT_ID alır; sonraki mesajlarda yalnız `devam et` yeterlidir.
- Her sayfa 20-30 dakikada bir yeniden kontrol edildiğinde aynı canlı task duplicate edilmez.

## Düzeltilen riskler
1. Sürücü harfi hardcode edilmedi; root her zaman launcher konumundan çözülür.
2. Eski architecture=2 / 5-worker identity, architecture=3 / 15-slot identity ile düzeltildi.
3. Başka PC'deki Git dubious ownership sorunu için portable safe.directory dosyası her açılışta yeniden üretilir.
4. Sistem Python/Git fallback kaldırıldı; yalnız disk üzerindeki doğrulanmış portable runtime kullanılır.
5. On beş slot repo self-contained `.git` dizinidir; mutlak gitdir/alternates yoktur.
6. 8012 portundaki başka servis TerraYield olarak kabul edilmez.
7. Panel Türkçe encoding ve eski 5-slot açıklaması düzeltildi.
8. Tek coordinator lock, machine/boot/PID identity ile stale lock ve ikinci açılışı engeller.
9. 20-30 dakikalık işler için timeout ve slot lease 3600 saniyeye çıkarıldı; aktif heartbeat yenilenir.
10. `*.v3.task.json` desteği eklendi; eski v2 görevleri okunmaya devam eder.
11. Child çıktıları exact_write_paths dışına çıkarsa yayın reddedilir.
12. Tek serial publisher, kalıcı publish queue, push retry/rebase ve remote SHA readback yolu eklendi.
13. Tek-tık app helper zaman aşımı düzeltildi; app sağlıklı olunca runner aşamasına geçer.
14. `START_AAYS_APP_AND_15_SLOT_FROM_THIS_DISK.cmd` uygulama + runner + paneli tek yerden açar.

## Testler
- Python syntax: PASS
- PowerShell parser: PASS
- Portable preflight: PASS
- Slot count: 15
- Parcel count: 92283; her proje 30761 x 3
- 16 GB fixture max simultaneous light workers: 15
- Wrong slot blocked: PASS
- Duplicate task blocked: PASS
- Path overlap blocked: PASS
- Long task timeout: 3600 seconds
- Long task heartbeat refresh: PASS
- Alternate drive root: PASS
- One-click app health: PASS
- One-click duplicate runner prevention: PASS
- Current machine: 7.31 GB usable RAM, adaptive max 5
- Physical second 16 GB PC test: NOT_RUN (PC bagli degil)
- Serial publisher real business-task E2E: PENDING_FIRST_REAL_SLOT_TASK

## İlk yeni-PC adımları
1. Diski tak ve `START_AAYS_APP_AND_15_SLOT_FROM_THIS_DISK.cmd` çalıştır.
2. Git push gerekiyorsa bu PC'de GitHub hesabına bir kez güvenli giriş yap.
3. Uzaktan kontrol isteniyorsa Chrome Remote Desktop/Tailscale hesabına bir kez giriş yap.
4. On beş ChatGPT sayfasına kendi SLOT_ID değerini bir kez ver; sonra yalnız `devam et` yaz.

## Kalan gerçek blockerlar
- Fiziksel ikinci PC bağlı olmadığı için gerçek 16 GB yük/reboot/USB sürücü harfi testi yapılamadı.
- GitHub push kimliği ve uzaktan masaüstü hesabı güvenlik nedeniyle diske gömülemez; her yeni PC'de bir defalık kullanıcı girişi gerekir.
- İlk gerçek slot task'i gelmeden serial publisher business-output E2E kanıtı üretilemez.

final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false
