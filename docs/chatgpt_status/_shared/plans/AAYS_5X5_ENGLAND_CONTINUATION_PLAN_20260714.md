# AAYS 5x5 İngiltere Devam Planı - TASLAK

Tarih: 2026-07-14
Durum: plan_hazır_uygulama_onayı_bekliyor
Branch: `codex/aays-single-runner-v5-20260706`

## Doğrulanmış başlangıç durumu

- Tek canonical runner: sağlıklı.
- Portable kök: `F:\TerraYield_AAYS_Portable`.
- Supervisor PID: `18316` (2026-07-14 doğrulaması).
- Queue sahiplik testleri A-F: PASS.
- GitHub remote heartbeat: `runner_active=true`, `pid_alive=true`, `lock_valid=true`.
- İkinci/paralel runner: yok.
- `final_ready=false`, `product_final_ready=false`.

## Amaç

Beş alanı beş çakışmayan coğrafi parçaya ayırarak ChatGPT sayfalarının hazırlık ve araştırma işini paralel yürütebilmesini sağlamak. Yerel yürütme yine TEK canonical runner üzerinden, claim/lease/CAS sözleşmesiyle sırayla yapılır. Bu nedenle gerçek çalışma süresinin tam 5 kat kısalacağı garanti edilmez; hız kazancı sayfa hazırlığı ve bağımsız veri toplama aşamasındadır.

## Zorunlu mimari

- 25 ayrı runner oluşturulmaz.
- 25 kayıt, tek runner için 25 mantıksal queue görevidir.
- GitHub queue/status/report/checkpoint dosyaları tek doğruluk kaynağıdır.
- Yeni ChatGPT sayfası eski sohbet raporuna ihtiyaç duymadan görev anahtarını ve global handoff paketini kullanır.
- Aynı `task_key` yeniden açıldığında en son checkpoint okunur; tamamlanmış satırlar tekrar işlenmez.
- C: canonical değildir; çalışma ve büyük çıktı F: üzerindedir.
- Sahte veri, sahte completed, sahte yüzde 100 ve kanıtsız final yasaktır.

## Beş coğrafi parça

Her alan aynı sabit parçaları kullanır:

1. `01_london_closure`: Önceden Londra kapsamlı işlerin gerçek kabul kriterleriyle kapatılması.
2. `02_south_southeast`: London hariç South East + South West.
3. `03_east_midlands`: East of England + East Midlands + West Midlands.
4. `04_north`: North West + Yorkshire and the Humber + North East.
5. `05_england_reconciliation`: İngiltere geneli eksik/çift kayıt, sınır, HTTP, browser ve remote-readback uzlaştırması.

Uygulamada resmi bölge kodları kullanılacak; değişken satır aralıklarıyla bölme yapılmayacak. Londra kapanmadan 02-04 görevleri veri hazırlayabilir, ancak yayın/kabul sırası Londra kabulünden sonra ilerler. 05, 01-04 kanıtları tamamlanmadan başlayamaz.

## 25 taslak görev anahtarı

| Alan | Görevler |
|---|---|
| Parcel Label | `parcel_label_1` ... `parcel_label_5` |
| Height Difference / Topography | `topography_1` ... `topography_5` |
| Gas Emissions | `gas_emissions_1` ... `gas_emissions_5` |
| Security / Public Safety | `security_1` ... `security_5` |
| Ready to Sell | `ready_to_sell_1` ... `ready_to_sell_5` |

## Her görev için checkpoint sözleşmesi

- `task_key`, `page_key`, `region_key`, `source_snapshot_sha`
- toplam/hedef/işlenen/doğrulanan/blocked kayıt sayıları
- son tamamlanan değişmez parsel kimliği
- çıktı hash'leri ve remote commit SHA
- HTTP/browser görünürlük kanıtı
- exact blocker listesi
- güvenlik bayrakları ve `final_ready=false`
- claim_id, lease, heartbeat ve terminal durum

## Yeni ChatGPT sayfası akışı

1. Tek global handoff ZIP'i yükle.
2. Yalnız görev adını yaz: örnek `topography_2 kaldığı yerden devam et`.
3. Sayfa GitHub registry/checkpoint/queue/status dosyalarını okur.
4. Aynı görevin tamamlanan kayıtlarını tekrar üretmez.
5. Yeni runner açmaz; mevcut tek runner kuyruğuna yalnız kendi page_key görevi için sözleşmeli dosya yazar.
6. Gerçek runner output + remote readback gelmeden completed veya yüzde 100 yazmaz.

## Olası problemler ve önlemler

- Çift çalışma: claim_id + CAS + tek lock ile engellenir.
- Sayfa kota/limit bitmesi: checkpoint GitHub'da olduğu için yeni sayfa aynı task_key ile devam eder.
- Coğrafi çakışma: resmi region registry ve değişmez parsel kimliğiyle dedupe yapılır.
- Dengesiz parça büyüklüğü: parça içinde batch checkpoint kullanılır; coğrafi sınır değiştirilmez.
- F diski harfi değişmesi: launcher kendi klasöründen portable root çözer.
- Git push kesintisi: local çıktı korunur, `git_push_status=failed` ve exact blocker yazılır; sonraki döngü retry eder.
- Browser/site kapalı: görev blocked/recoverable kalır; kanıtsız tamamlanmaz.
- Londra/İngiltere kapsam karışması: her kanıtta `region_key` zorunludur.
- Eski sohbetin yanlış yüzdesi: yalnız GitHub doğrulanan sayıları geçerlidir.

## Uygulama sırası - kullanıcı onayından sonra

1. Mevcut parcel/koordinat registry'sini okuyup resmi bölge eşlemesini doğrula.
2. 25 kayıtlık registry'yi `draft` durumundan `approved` durumuna geçir.
3. Global prompt + tek ZIP handoff manifestini üret.
4. Önce beş adet `*_1` Londra kapanış görevini sıraya al.
5. Londra kabulünden sonra 02-04 görevlerini aç.
6. Son olarak beş adet 05 uzlaştırma görevini çalıştır.
7. Beş alanın İngiltere geneli remote-readback kanıtı bitmeden ürün finali verme.

## Onay sınırı

Bu belge yalnız plandır. 25 queue görevi oluşturulmadı ve mevcut runner düzeni değiştirilmedi.

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
