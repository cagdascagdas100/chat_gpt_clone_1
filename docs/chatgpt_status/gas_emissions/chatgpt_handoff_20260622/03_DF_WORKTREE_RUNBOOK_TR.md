D/F Worktree Runbook - Gas Emissions

Tercih edilen kok

1. `F:\chatgpt\AAYS_WORK\gas_emissions_088_clean_20260616_160836`
2. Fallback:
   `D:\chatgpt\gas_emissions_runtime_finish_20260622`

Onemli

1. C repo kokunde calismayi tercih etme.
2. F koku varsa onu kullan.
3. Yoksa `D:\chatgpt\...` altina kopya/worktree ac.

Adimlar

1. F koku varsa:

```powershell
Set-Location 'F:\chatgpt\AAYS_WORK\gas_emissions_088_clean_20260616_160836'
git branch --show-current
```

2. D fallback gerekiyorsa:

```powershell
New-Item -ItemType Directory -Force 'D:\chatgpt\gas_emissions_runtime_finish_20260622' | Out-Null
```

3. Temel truth check:

```powershell
node --check england_map_web\app.js
```

4. App open:

```powershell
Set-Location terrayield_land_intelligence
.\start_uvicorn_8010_bg.ps1
```

5. Saglik probe:

```powershell
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/health').StatusCode
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/england_map_web/').StatusCode
```

6. Gas static probe:

```powershell
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/england_map_web/data/parcel_emissions_scores.geojson?v=20260622-gas-emissions-v2').StatusCode
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/england_map_web/assets/icons/terrayield_icons/air.png').StatusCode
```

7. Browser smoke hedefi

Ac:

```text
http://127.0.0.1:8010/england_map_web/?r=gas-final-check
```

Kontrol et:

1. `Deger menusu` aciliyor mu?
2. `Hava Kirliligi` butonu aktif/inactive toggle yapiyor mu?
3. Sadece legend degil, thematic parcel output var mi?
4. Tiklanan parcel popup veya sag panel icinde gas alanlari dolu mu?

ChatGPT'ye geri verilecek minimum veri

1. `node --check` sonucu
2. 4 adet HTTP status sonucu
3. Browser smoke gozlemi:
   - `geometryMode`
   - popup'ta dolu alan var/yok
   - parcel polygon thematic render var/yok
