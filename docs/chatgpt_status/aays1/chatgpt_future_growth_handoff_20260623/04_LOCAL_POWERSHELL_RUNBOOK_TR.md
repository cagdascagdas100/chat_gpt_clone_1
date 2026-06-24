# Local PowerShell Runbook

Amac:

- C yerine `F:\chatgpt\AAYS_FG100\` veya `D:\chatgpt\AAYS_FG100\` altina rapor uretmek
- Docker / 8010 / Future Growth layer / final wrapper durumunu tek raporda toplamak

## 1. Tani scripti calistir

```powershell
powershell -ExecutionPolicy Bypass -File .\05_FG_LOCAL_RUNTIME_DIAGNOSTIC.ps1
```

Istersen hedef kok verebilirsin:

```powershell
powershell -ExecutionPolicy Bypass -File .\05_FG_LOCAL_RUNTIME_DIAGNOSTIC.ps1 -OutputRoot "F:\chatgpt\AAYS_FG100"
```

## 2. ChatGPT'ye geri gonderecegin cikti

Yalniz su iki seyi geri ver:

1. Uretilen rapor dosyasinin tam yolu
2. Raporun tam metni

## 3. Kritik local checks

Rapor icinde su satirlarin sonucu olacak:

- `git_branch`
- `git_remote`
- `git_status_short`
- `api_root_status`
- `england_map_web_status`
- `future_growth_methodology_status`
- `future_growth_layer_status`
- `future_growth_layer_note`
- `docker_status`
- `final_wrapper_exists`

## 4. Fail-closed kural

Asagidaki durumda final kabul verme:

- Docker yoksa
- layer endpoint timeout / 5xx ise
- final wrapper yoksa
- runtime koku Future Growth yerine farkli shell'e gidiyorsa
