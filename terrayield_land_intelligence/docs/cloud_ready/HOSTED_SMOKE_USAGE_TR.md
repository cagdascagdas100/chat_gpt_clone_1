# Hosted Smoke Usage

Public cloud URL olustuktan sonra su komut kullanilir:

```powershell
$env:TERRAYIELD_PUBLIC_API_URL="https://YOUR_PUBLIC_API_HOST"
python terrayield_land_intelligence/scripts/cloud_smoke_check.py
```

Beklenen basarili siniflandirma:

```text
CLOUD_RUNTIME_READY
```

Eger sonuc `CLOUD_RUNTIME_BLOCKED` ise:

1. Backend container loglarini kontrol et.
2. Database connection ayarlarini provider panelinde kontrol et.
3. CORS/API base URL ayarlarini kontrol et.
4. `/` endpointinin public URL'den acildigini kontrol et.

Bu smoke local `127.0.0.1` testi degildir. Sadece public HTTPS URL ile cloud runtime kaniti sayilir.
