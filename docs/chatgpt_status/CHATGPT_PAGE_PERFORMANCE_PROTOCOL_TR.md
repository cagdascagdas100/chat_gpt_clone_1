# ChatGPT Sayfa Performans Protokolü

Amaç: Uzun konuşma sayfalarında ChatGPT yanıtının kesilmesi, sayfanın kasması ve gereksiz tekrarların birikmesini azaltmak.

## Kısa kullanım kuralı

Kullanıcı bu sayfada mümkünse yalnızca `devam et` yazar.

Asistan her turda yalnızca şunları yapar:

1. `ai-tasks/current-task.json` dosyasını oku.
2. `ai-tasks/.last-task-id` dosyasını oku.
3. `ai-heartbeat/portable-runner.md` dosyasını oku.
4. Kendi sayfa anahtarını ortak pano JSON içinde güncelle.
5. Gerekiyorsa tek küçük `current-task` güncellemesi yap.
6. Son cevapta yalnızca genel ilerleme ve bekleme süresini ver.

## Yasaklanan ağır davranışlar

- Aynı uzun kullanıcı promptunu cevaplarda tekrar etme.
- Tüm geçmiş planı her mesajda yeniden özetleme.
- Aynı turda çok sayıda büyük dosya yazma.
- Başka sayfaların JSON satırlarını elle yeniden üretme.
- Gereksiz status.md, index.html, standalone HTML rewrite yapma.
- PowerShell komutu isteme; yalnızca runner tamamen kilitliyse iste.
- DB write açma.
- Production deploy açma.
- Fake veri üretme.

## Pano güncelleme kuralı

Öncelik `ai-task-scripts/update_chatgpt_status.ps1` helper scriptidir. Mümkünse ortak JSON doğrudan komple yeniden yazılmaz; sadece ilgili sayfa helper üzerinden güncellenir.

Kendi sayfası dışında başka satırlar silinmez, ezilmez.

## Yanıt formatı

Her `devam et` sonunda yalnızca şu iki satır bulunur:

- Genel proje ilerlemesi: %X
- Bekleme süresi: X-Y dakika

Ek teknik yüzde, alt görev yüzdesi, runner yüzdesi verilmez.

## Düşünme durdu durumunda

Bu ChatGPT arayüzünün cevap üretiminin kesildiğini gösterir; yerel PowerShell runner'ın kesin durduğu anlamına gelmez. İlk kontrol GitHub dosyalarından yapılır. Heartbeat eskiyse status `polling` veya `stale_finished` olarak güncellenir; aynı büyük prompt tekrar ettirilmez.
