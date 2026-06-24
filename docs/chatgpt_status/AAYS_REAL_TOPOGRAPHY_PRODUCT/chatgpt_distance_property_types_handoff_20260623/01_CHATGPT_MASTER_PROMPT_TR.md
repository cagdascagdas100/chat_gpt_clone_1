# CHATGPT MASTER PROMPT - Distance to Nearby Property Types

Bu gorevi sadece asagidaki kapsamda ele al:

- Layer name: `Distance to Nearby Property Types`
- Repo root: `C:\Users\cagda\Documents\GitHub\AAYS`
- Status page key: `AAYS_REAL_TOPOGRAPHY_PRODUCT`
- Agir local work root: `F:\chatgpt\AAYS_WORK\distance_property_types_page34_20260623`
- Agir local data/report root: `D:\AAYS_DATA\distance_property_types_page34_20260623`

## Ana hedef

Bu katmanin gercekten `%100` olup olmadigini yalan soylemeden degerlendir. Mevcut durum `%75` civarinda. Kod entegrasyonu ile gercek runtime kabulunu birbirine karistirma.

## Kesin kurallar

1. `FINAL_READY`, `100%`, `production complete` deme; ancak gercek runtime kaniti gelirse de.
2. Kod var diye veri var varsayma.
3. DB runtime, Docker, PostGIS, listener portu ve endpoint sonucu dogrulanmadan parcel polygon gorunurlugu tamamlandi deme.
4. Elindeki bu paketi ve eklenen local probe raporlarini source of truth kabul et.
5. Performans dusurucu buyuk tarama isteme. Ilk probe'lari dar tut:
   - `/health`
   - `/map/distance-property-types?bbox=-0.55,51.28,0.35,51.75&limit=10`
6. C diskte buyuk is isteme. D/F koklerini kullan.

## Senden istenen cikti

Su 6 basligi tek cevapta ver:

1. **Gercek durum ozeti**
   - Simdiye kadar tamam olanlar
   - Tamam olmayanlar
   - Neden `%100` denemeyecegi

2. **Eksik parca matrisi**
   - Bilesen
   - Simdiki durum
   - Kanit
   - Eksik aksiyon
   - Kim yapar: `ChatGPT`, `local user`, `Codex`

3. **ChatGPT'nin yapabilecegi isler**
   - Repo/audit yorumlama
   - Patch/planning/runbook uretimi
   - Minimal PowerShell iyilestirme onerileri
   - Final acceptance checklist

4. **ChatGPT'nin tek basina yapamayacagi isler**
   - Docker daemon baslatma
   - PostGIS portunu canli dinler hale getirme
   - 127.0.0.1 endpointlerini bizzat acip dogrulama
   - Shared runner stale bridge durumunu local makinede duzeltme

5. **Local kullanici icin kisa komut paketi**
   - D/F klasor hazirlama
   - DB probe
   - Docker / PostGIS probe
   - API probe
   - Rapor toplama

6. **Bir sonraki Codex veya local asama icin karar**
   - Hangi durumda tekrar Codex'e donulmeli
   - Hangi durumda sadece local PowerShell ile devam edilmeli

## Elindeki temel kanitlar

Simdilik kabul et:

- `http://127.0.0.1:8010/health` -> `200`
- health icinde `database=degraded`
- `http://127.0.0.1:8010/map/distance-property-types?...` -> `200`
- ama `features=[]`

Kod kaniti:

- `england_map_web/app.js` icinde frontend entegrasyonu var
- `terrayield_land_intelligence/app/api/routes/map_layers.py` icinde `GET /map/distance-property-types` var
- `terrayield_land_intelligence/data/exports/parcel_use6/parcel_use6_lookup.json` siniflama verisini tasiyor

Ama runtime eksik:

- Local DB listener yok
- Docker daemon / PostGIS runtime bu makinede ayakta degil
- Shared runner bridge bu page-key icin stale veya baska goreve bakiyor

## Beklenen uslup

- Kisa
- Teknik
- Yalan olmayan
- Tamamlanan ve tamamlanmayan kisimlari ayiran
- "Kod hazir ama runtime bloklu" cizgisini koruyan
