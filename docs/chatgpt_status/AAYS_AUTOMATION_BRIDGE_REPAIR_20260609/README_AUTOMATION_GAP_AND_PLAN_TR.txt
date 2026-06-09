AAYS AUTOMATION BRIDGE REPAIR - 2026-06-09

KISA TEShis
Sorun tek runner sayisi degil. Sorun GitHub tarafinda ChatGPT'nin yazdigi talimat dosyasinin local runner queue dizinine otomatik tasinmamasi ve local runner sonucunun tekrar GitHub'a guvenilir sekilde push edilmemesi.

Mevcut kanitlar
1. Local komutlar current-task.txt ve tasks/*.txt yazabiliyor.
2. Runner bazen started/already_running gorunuyor.
3. Fakat GitHub'da beklenen latest output uzun sure status=queued seviyesinde kaliyor.
4. Daha once branch divergence goruldu: feature/terrayield-aays-integration ile origin/feature/terrayield-aays-integration ayrismis; bu push/sync zincirini bozdu.
5. Son acceptance durumunda ilerleme 65% seviyesinde kaldi; endpoint perf ve runtime proof kapanmadan yuzde artirilmayacak.

Eksik parca
GitHub <-> local bridge loop eksik veya calismiyor:
- ChatGPT GitHub'a docs/chatgpt_status/runner_inputs/*.txt yaziyor.
- Local runner bunu otomatik alip C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue\current-task.txt dosyasina aktarmiyor.
- Runner bitince docs/chatgpt_status/runner_outputs/*.txt dosyasini GitHub'a garanti push etmiyor.

Duzeltme stratejisi
1. Tek canonical runner korunacak.
2. GitHub input dosyalari local queue'ya aktarilacak.
3. Runner output dosyalari repo icine kopyalanacak.
4. Push icin mevcut ayrismis branch zorlanmayacak; output icin benzersiz chatgpt/aays-runner-output-* branch kullanilacak.
5. DB write, migration, DDL, deploy, fake data, destructive git, force push yok.

Bu klasordeki AAYS_BRIDGE_REPAIR_BOOTSTRAP.ps1 dosyasi bu eksik bridge loop'u kurmak icin hazirlandi. Bu dosya bir kez calistirilirse sonraki 'devam' mesajlarinda ChatGPT GitHub'daki outputlari okuyarak donguyu surdurebilir.

Yuzde neden artmiyor?
Yuzde kanitla artar. Son karar 65% seviyesinde kaldi, cunku listings endpoint timeout, sales-history agir, lazy/nonblocking kaniti eksik ve full England runtime coverage PARTIAL. Once output zinciri duzelmeli; sonra endpoint/lazy proof uretilmeli.
