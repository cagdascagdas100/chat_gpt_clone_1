PowerShell Komutlari - Low Credit Gas Emissions

1. Branch ve kok dogrula

```powershell
Set-Location 'F:\chatgpt\AAYS_WORK\gas_emissions_088_clean_20260616_160836'
git branch --show-current
Get-Location
```

2. Kritik marker grep

```powershell
rg -n "EMISSIONS_CONTROL_MODE|air\.png|Hava Kirliligi|GAS_EMISSIONS_DATA_URL|GAS_EMISSIONS_SOURCE_FEATURE_COUNT" england_map_web\app.js
rg -n "buildVisiblePolygonFeatures|getLookupMatch|point_source|polygon_join|point_fallback|buildGasEmissionsPopupMetaHtml|ensureGasEmissionsPopupLookupLoaded" england_map_web\app.js
rg -n "static-3110-sale-ready-20260622-v43|app\.js\?v=" england_map_web\index.html
```

3. App.js syntax

```powershell
node --check england_map_web\app.js
```

4. Runtime health

```powershell
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/health').StatusCode
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/england_map_web/').StatusCode
```

5. Gas asset + data health

```powershell
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/england_map_web/assets/icons/terrayield_icons/air.png').StatusCode
(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8010/england_map_web/data/parcel_emissions_scores.geojson?v=20260622-gas-emissions-v2').StatusCode
```

6. Sample record check

```powershell
@'
import json
from pathlib import Path
p = Path("england_map_web/data/parcel_emissions_scores.geojson")
with p.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)
print("feature_count", len(data["features"]))
first = data["features"][0]["properties"]
print("first_keys", sorted(first.keys()))
print("first_sample", {k: first.get(k) for k in ["parcel_id","parcel_ref","emission_percent","confidencePercent","source_type"]})
'@ | python -
```

7. Popup mismatch sample

```powershell
@'
import json
from pathlib import Path
p = Path("england_map_web/data/parcel_emissions_scores.geojson")
with p.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)
for feat in data["features"]:
    props = feat.get("properties", {})
    if str(props.get("parcel_ref", "")).strip() == "33507540":
        print(props)
        break
'@ | python -
```

ChatGPT'ye sadece bunlari geri yapistir

1. Branch adi
2. `node --check` sonucu
3. HTTP status satirlari
4. `feature_count`
5. `first_sample`
6. `parcel_ref=33507540` sample record
