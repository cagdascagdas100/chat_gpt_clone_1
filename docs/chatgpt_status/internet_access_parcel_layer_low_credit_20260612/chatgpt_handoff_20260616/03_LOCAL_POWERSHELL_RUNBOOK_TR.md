# Local PowerShell Runbook

## 1. Agir Root Hazirla

Repo disi agir root icin:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\chatgpt_handoff_20260616\scripts\10_prepare_heavy_root.ps1
```

## 2. Mevcut Paketi Hizli Dogrula

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\chatgpt_handoff_20260616\scripts\20_validate_current_package.ps1
```

## 3. Uygulamayi Fail-soft Modda Ac

```powershell
$env:TYLI_DB_PORT='55460'
$env:TYLI_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:55460/terrayield_land?connect_timeout=1'
Set-Location 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
C:\Python312\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Tarayici:

```text
http://127.0.0.1:8010/england_map_web/
```

## 4. Docker Varsa Opsiyonel Kontroller

Docker servis durumunu kontrol et:

```powershell
Get-Service com.docker.service
```

Yonetici yetkisi varsa servis baslat:

```powershell
net start com.docker.service
```

DB tablo kontrolu:

```powershell
docker exec terrayield_land_postgis psql -U postgres -d terrayield_land -c "select count(*) from parcel_internet_access_scores;"
```

## 5. ChatGPT Cevabi Geldikten Sonra

ChatGPT sana patch/diff ve yeni output path'leri verdiginde:

1. agir root altinda dosyalar var mi kontrol et
2. `06_AFTER_CHATGPT_RETURN_CHECKLIST_TR.md` ile karsilastir
3. ancak bundan sonra Codex'e geri don

