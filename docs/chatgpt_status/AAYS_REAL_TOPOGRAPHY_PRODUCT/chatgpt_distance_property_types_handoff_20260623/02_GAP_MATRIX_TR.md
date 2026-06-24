# Gap Matrix - Distance to Nearby Property Types

| Bilesen | Simdiki durum | Kanit | Eksik | Kim yapar |
|---|---|---|---|---|
| Frontend toggle / fetch baglantisi | Tamam | `england_map_web/app.js` ve integration raporu | Yok | - |
| Backend route `/map/distance-property-types` | Tamam | `terrayield_land_intelligence/app/api/routes/map_layers.py` | Yok | - |
| Popup / sag panel alanlari | Tamam | integration raporu | Canli veri ile yeniden smoke gerekli | local user |
| API syntax / static check | Tamam | `py_compile` / `node --check` PASS | Yok | - |
| Endpoint HTTP availability | Tamam | endpoint `200` | Bos feature collection sorunu devam | local user |
| Parcel polygon live visibility | Bloklu | endpoint `features=[]` | DB ve parcel tablolarina erisim gerekli | local user |
| DB runtime | Bloklu | `/health -> database=degraded` | PostGIS dinler hale gelmeli | local user |
| Docker runtime | Bloklu | local environment bulgulari | Docker daemon / compose DB ayaga kalkmali | local user |
| Parcel geometry source | Kismi | route `parcels_inspire` okuyor | Gercek DB-backed polygon verisi canli olmali | local user |
| Six-color use classification | Tamam | `parcel_use6_lookup.json` | Yok | - |
| DB'siz polygon fallback | Yok | lookup dosyasi geometry icermiyor | Ancak ayri gercek geometri kaynagi varsa eklenebilir | ChatGPT planlar, Codex/local uygular |
| Shared runner chain | Bloklu | runtime wrapper probe raporu | dogru page-key task + fresh heartbeat + output gerekli | local user / Codex |
| Final marker report | Yok | final wrapper yok | Gercek runtime probe sonrasi uretilmeli | local user / Codex |

## Duz sonuc

Bugun itibariyla su ayrim gecerli:

- **Kod entegrasyonu:** var
- **Gercek runtime kabul:** yok
- **Dogrulanmis ilerleme:** `%75`

## ChatGPT icin pratik ayrim

### ChatGPT'nin rahatlikla yapabilecekleri

- Gap matrisi yorumlamak
- Patch oneri paketi uretmek
- Runbook sadeleştirmek
- Kullanici icin local komut sirasini optimize etmek
- Sonraki Codex prompt'unu yazmak

### ChatGPT'nin tek basina yapamayacaklari

- Local Docker Desktop / daemon acmak
- PostGIS container'ini calistirmak
- Local 127.0.0.1 endpoint sonucu dogrulamak
- Gercek harita ustunde parcel polygon gorunurlugunu gormek
