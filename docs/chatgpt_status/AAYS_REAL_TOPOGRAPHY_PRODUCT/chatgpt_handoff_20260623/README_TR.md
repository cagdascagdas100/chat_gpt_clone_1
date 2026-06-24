# AAYS Real Topography Product - ChatGPT Handoff - 2026-06-23

Bu paket, Topography katmani icin Codex tarafinda dogrulanan mevcut yerel durumu ve ChatGPT'ye devredilebilecek kalan isleri icerir.

Amac:

- Codex kredisini az harcayarak kalan isleri ChatGPT tarafinda planlatmak
- D/F diskleri uzerindeki gercek local durumdan sapmamak
- Fake final uretmemek
- Topography icin local 100 durumunu bozmayacak sekilde ilerlemek

Bu pakette once okunacak dosya:

- `00_CHATGPT_MASTER_PROMPT_TR.md`

Destek dosyalari:

- `01_TOPOGRAPHY_DURUM_VE_EKSIKLER_TR.md`
- `02_PATH_MANIFEST_TR.csv`
- `03_CHATGPT_TASK_SPLIT_TR.md`
- `scripts/10_verify_topography_local_runtime.ps1`
- `scripts/20_audit_topography_data_coverage.ps1`
- `scripts/30_remote_sync_diagnostic.ps1`

Mevcut dogrulanmis yerel durum:

- `http://127.0.0.1:8010/england_map_web/` aciliyor
- `http://127.0.0.1:8010/topography/lookup?parcel_id=29759443` 200 donuyor
- canonical final report localde 100 tokenlariyla var

Ama hala ayri takip edilmesi gereken eksikler vardir:

- remote branch sync tamam degil
- England-wide veri kapsami kanitlanmadi
- ornek parcel icin `status=no_data` donusu devam edebilir
- manuel UI parcel-click smoke tam kanitlanmadi
