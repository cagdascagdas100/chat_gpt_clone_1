# Internet Access Parcel Layer Handoff

Amaç: TerraYield AAYS icindeki Internet katmanini dusuk Codex kredisiyle ChatGPT ve yerel PowerShell/Docker uzerinden tamamlatmak.

Bu paket uygulama kodunu degistirmez. Mevcut repo okunarak hazirlanmis denetim, kaynak URL listesi, E-drive veri klasoru sozlesmesi, API/UI cikti sozlesmesi, kabul testleri, Excel raporu semasi ve yerel read-only audit betigini icerir.

## En Kisa Kullanim

1. ChatGPT'ye `01_CHATGPT_MASTER_PROMPT_TR.txt` dosyasindaki metni verin.
2. ChatGPT'ye bu klasoru veya olusturulan ZIP dosyasini ek olarak verin.
3. Yerelde once `07_LOCAL_READONLY_AUDIT.ps1` betigini calistirin.
4. E-drive veri klasorlerini olusturmak icin `08_CREATE_E_DRIVE_STRUCTURE.ps1` betigini calistirin.
5. ChatGPT'den gelen patch onerilerini uygulamadan once `06_ACCEPTANCE_TESTS_TR.md` ile karsilastirin.

## Kritik Guncel Tespit

Bu checkout'ta Internet katmani icin onemli frontend/backend kancalari zaten mevcut:

- Ana map kontrolunde internet ikonu `./assets/icons/terrayield_icons/internet.png` ile bagli.
- `england_map_web/index.html` `internet_access_overlay.js` dosyasini yukluyor.
- `window.AAYS_INTERNET` bridge'i var.
- Backend `GET /map/internet-access` endpoint'i var.
- Endpoint `parcel_internet_access_scores` tablosunu `parcels_inspire` ile join etmeyi hedefliyor.

Ancak final kabul kuralina gore ozellik tamam sayilmamali:

- `england_map_web/data/parcel_internet_access_scores.geojson` fallback dosyasi mevcut degil.
- Narrow taramada `parcel_internet_access_scores` icin acik migration/model bulunamadi.
- Overlay gercek internet verisi yoksa sales-history proxy'den skor uretmeye calisiyor; bu sadece diagnostic fallback olabilir, final Internet Access katmani olarak kabul edilmemeli.
- Popup temel alanlari gosteriyor ama faktor katkilarini tablo halinde, matching method, source recency, geometry precision ve Excel export contract'ini tam olarak garanti etmiyor.

## Final Hedef

Kullanici internet ikonuna bastiginda:

- Internet Access layer acilmali.
- Parcel'lar 5 seviyeli renk skalasiyla gorunmeli.
- Parcel'a tiklaninca Internet Access Quality yuzdesi, seviye, renk kategorisi, confidence, kaynaklar, source date ve hesaplama aciklamasi gorunmeli.
- Faktor tablosu gorunmeli: faktor, olculen deger, normalize skor, agirlik, katkisi, kaynak, confidence.
- Excel raporu uretilmeli: tum parcel'lar, skor, seviye, renk, faktor breakdown, kaynaklar, source dates, matching method, confidence ve explanation.
- Tum raw/processed/reports dosyalari `E:\AAYS_DATA\internet_access\` altinda duzenli saklanmali.

