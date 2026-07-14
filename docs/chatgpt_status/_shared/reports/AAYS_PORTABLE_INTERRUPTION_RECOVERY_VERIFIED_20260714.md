# AAYS Portable Kesinti Recovery - Doğrulandı 20260714

Durum: **PASS**

## Canlı kurulum

- Scheduled Task: `AAYS Portable Runner Guardian`, state `Running`.
- Trigger sayısı: 3 (logon, resume event, periyodik self-heal).
- Guardian sayısı: 1, PID `17156`.
- Runner sayısı: 1, PID `3424`.
- Runner lock geçerli: true.
- Eski `AAYS_TerraYield_SingleRunner` task kaldırıldı.
- Rollback XML mevcut.
- Kurulum sırasında gerçek kontrollü restart: PID `18316` -> `3424`.
- Restart duplicate execution: 0.
- İkinci installer çalıştırması duplicate oluşturmadı.
- Tek-tık launcher tekrar çalıştırıldığında `already_running` döndü; yeni süreç açılmadı.

## Dosya bütünlüğü

- ProgramData guardian SHA256: `37099A8D36FDB1FFAD753D4B2ADAD0F590BFBFCDFE26E8E3830483E9FA116258`
- F repo guardian SHA256: aynı.
- Installer SHA256: `CA155DBE75A9327A047AD8826E01DB7418DED16B1422B026940C322F1CABE104`
- Portable launcher SHA256: `3E3AB14280AAD16C0D638BC8C6227B0ABA5826AA232A25389219A916AB6312EC`
- Volume GUID: `\\?\Volume{9526ec62-0000-0000-0000-000008000000}\`
- Volume serial: `C232B744`
- Marker ID: `a607fa27ba174eb9ab86ec96d60956c8`

## Testler

- A Normal: PASS; runner healthy, tek guardian/runner.
- B Ağ kaybı simülasyonu: PASS; `waiting_for_network`, runner kapanmadı.
- Ağ dönüşü: PASS; `runner_healthy`, aynı PID/checkpoint.
- C Disk yok simülasyonu: PASS; `waiting_for_portable_disk`, F'ye test yazması yapılmadı.
- Disk dönüşü: PASS; marker/volume çözümü ve mevcut runner sahipliği doğrulandı.
- D Uyku/uyanma simülasyonu: PASS; owner grace doğrulandı, duplicate 0.
- E Yeniden kurulum: PASS; task/guardian/runner sayısı 1.
- F Checkpoint: PASS; `current.task.json` SHA256 önce/sonra aynı: `4A1C4D34A1C126CA472125464DBC8FB9E70379125A1B3C6D59FEADFB9B90FCF3`.
- Beş sayfa registry: PASS.
- İlk installer hata denemesinde rollback: PASS; eski task/runner geri geldi, ardından düzeltme ile kurulum tamamlandı.
- Gerçek process-kill testi aktif görev `running` olduğu için güvenli biçimde yapılmadı. Kurulumdaki kontrollü PID değişimi restart zincirini kanıtladı.

Fiziksel disk çıkarma, ağ adaptörü kapatma ve gerçek uyku testi otomatik yapılmadı; güvenli üç-adımlı manuel rehber plan raporundadır.

## Güvenlik

- 5x5 planı uygulanmadı.
- Yeni/paralel runner yok.
- Veri yeniden üretilmedi.
- Aktif ChatGPT görevi kesilmedi.
- `final_ready=false`, `product_final_ready=false`.
