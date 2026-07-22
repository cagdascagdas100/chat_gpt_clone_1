# Problem Solver 1

Bu, 21 veri slotuna eklenen 22. mantıksal bakım slotudur. Ayrı runner açmaz ve 15 veri
işçisi kapasitesinden worker tüketmez.

Öncelik sırası:

1. `Çözülmemiş Kullanıcı İşlemleri` listesindeki güncel problemler.
2. `RECOVERY_PARKED`, stale, timeout, Git kilidi veya kirli worktree nedeniyle takılan slotlar.
3. Bekleyen yayın/kuyruk sorunları ve güvenli worker kapasitesi.
4. Problem kalmadığında sürekli izleme ve bir defalık telefon `all clear` bildirimi.

ChatGPT sayfasında ortak devam promptuna yalnız `SLOT_ID=problem_solver_1` yazılır. Her
`devam et` mesajı `continuation_requested_latest.json` dosyasına yeni `request_id` ve
`requested_at` yazar. Business task, ikinci coordinator, force push veya veri silme üretmez.

Telefon bildirimi için kontrol panelindeki `Telefon Bildirim Ayarı` düğmesine Android
bildirim servisi/ntfy tam HTTPS konu URL'si yazılır. Kimlik bilgisi GitHub'a konmaz.
