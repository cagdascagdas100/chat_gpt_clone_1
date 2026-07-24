# AAYS 15 Slot Remote Continuation Contract

WORKSTREAM_ID=AAYS_15_SLOT_SAFE_PARALLEL_V1
ARCHITECTURE_VERSION=3
CANONICAL_PARCEL_COUNT=92283

- Her proje uc sabit shard kullanir: 1=1..30761, 2=30762..61522, 3=61523..92283.
- Her ChatGPT sayfasi tam bir slot_id sahibidir; baska slotun queue/status/output yoluna yazamaz.
- Mevcut eski sayfa ilgili projenin _1 slotuna gecis yapar. _2 ve _3 yeni sayfalara ayrilir.
- ZIP ve sohbet metni tarihsel baglamdir. GitHub branch HEAD ve matching slot checkpoint authoritative kaynaktir.
- Yeni sayfa once manifest, ownership, checkpoint, heartbeat, current_task ve status dosyalarini okur.
- Terminal/no-replay task yeniden calistirilmaz. Ilk eksik veya dogrulanmamis adimdan devam edilir.
- Child worker direct push yapmaz. Shared/final yollarini yalniz tek git_publish/shared_publish gate yayinlar.
- exact_write_paths icindeki her yol kendi slot_id degerini icermelidir.
- Queue task base_slot_id, shard_index ve parcel_partition alanlariyla slot kimligini kanitlamalidir.
- Stale heartbeat aktif is sayilmaz; lease takeover yalniz remote HEAD readback sonrasinda yapilir.
- final_ready=false; gercek commit, push, remote readback ve kabul kaniti olmadan completed veya yuzde 100 yazilmaz.