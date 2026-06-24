# Internet Access ChatGPT Gap Package

Amac:
- Internet katmani icin eksik kalan parcel-level isi ChatGPT tarafina tasimak
- Codex kredi harcamadan D/F drive odakli local runbook vermek
- "report final" ile "urun gercekten calisiyor" ayrimini korumak

Sabit kapsam:
- repo: `cagdascagdas100/chat_gpt_clone_1`
- branch: `feature/terrayield-aays-integration`
- page key: `internet_access_parcel_layer_low_credit_20260612`
- local repo root: `C:\Users\cagda\Documents\GitHub\AAYS`
- agir calisma root hedefi: `F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623`
- agir calisma fallback root: `D:\AAYS_WORK\internet_access_parcel_final_20260623`

Ilk okunacak dosyalar:
1. `00_CHATGPT_MASTER_PROMPT_TR.md`
2. `01_GAP_STATUS_TR.md`
3. `03_PATHS_AND_OUTPUTS_TR.md`
4. `references\INTERNET_F_ARTIFACT_HEADERS_20260623.md`
5. `references\CURRENT_RUNTIME_AUDIT_20260623.md`

Bu paket neyi cozer:
- ChatGPT hangi eksiklerin gercek oldugunu bilir
- ChatGPT kod/pipeline/runbook metinlerini uretir
- Sen localde PowerShell ile D/F uzerinde calistirirsin

Bu paket neyi tek basina cozmuyor:
- renderable parcel geometry uretimi
- buyuk GeoJSON/CSV olusturma
- DB import
- 8010 endpoint smoke

Gercek durumun kisasi:
- uygulama aciliyor
- `/map/internet-access` 200 donuyor
- ama bos `FeatureCollection` donuyor
- mevcut F paketi postcode-level ve `geometry: null`
- yani Internet parcel thematic layer henuz tamam degil
