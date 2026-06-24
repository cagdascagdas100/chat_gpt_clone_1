# CHATGPT MASTER PROMPT - AAYS REAL TOPOGRAPHY PRODUCT - 2026-06-23

Bu promptu ChatGPT'ye aynen ver.

## Sabit kapsam

Repo:
`cagdascagdas100/chat_gpt_clone_1`

Branch:
`aays-runner-v17-icon-work-20260603-232706`

Page key:
`AAYS_REAL_TOPOGRAPHY_PRODUCT`

Calisma kokleri:

- local worktree: `F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706`
- page root: `F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706\docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT`
- D/F veri kokleri:
  - `D:\topografik_map\london\terrarium_tiles`
  - `F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz`
  - beklenen ama su an kanitlanmamis England-wide kok: `D:\AAYS_DATA\topography\england\`

## Mutlak kurallar

1. Fake final uretme.
2. Ayrica ikinci runner uretme.
3. Baska page key, branch veya repo varsayma.
4. Topography local 100 durumunu dusurme.
5. D/F diski disinda agir veri akisi onermemeye calis.
6. C drive'da sadece kucuk metin/script uretimi onerebilirsin; veri tasima ve runtime D/F odakli olmali.
7. `PRODUCTION_COMPLETE=true` ifadesini ancak mevcut local kanitla uyumlu sekilde kullan.

## Codex tarafinda artik kanitli olanlar

Asagidaki local durumlar Codex tarafinda dogrulandi:

- `http://127.0.0.1:8010/england_map_web/` aciliyor
- `http://127.0.0.1:8010/topography/lookup?parcel_id=29759443` 200 donuyor
- canonical final report var:
  - `F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706\docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\reports\pb_runtime_finalization_single_runner_20260617T000000Z.txt`
- canonical final status var:
  - `F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706\docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\status\pb_runtime_finalization_single_runner_20260617T000000Z.status.txt`
- bu report icinde su tokenlar localde mevcut:
  - `FINAL_STATUS=FINAL_READY_CONFIRMED`
  - `PRODUCT_PROGRESS_ESTIMATE=100`
  - `PRODUCTION_COMPLETE=true`

## ChatGPT'nin simdi yapmasi gerekenler

Senden kod yazmaktan cok, operatorun localde calistirabilecegi dusuk riskli devam paketi uretmen isteniyor.

Asagidaki ciktilari ver:

1. **Eksik kalan islerin net listesi**
   - hangisi tamam
   - hangisi eksik
   - hangisi sadece local operator calistirabilir
   - hangisi ChatGPT tarafinda metin/script/runbook olarak hazirlanabilir

2. **Topography icin gercek kalan blocker analizi**
   Su basliklari ayir:
   - remote branch sync / non-fast-forward
   - England-wide veri kapsami eksigi
   - parcel bazli `no_data` donen lookup kapsami
   - manuel UI smoke eksigi
   - page-key altindaki `pb_*` isim kirligi / naming debt

3. **Operator icin PowerShell runbook**
   Ayni anda sadece guvenli su isleri uretsin:
   - remote sync diagnostic
   - topography lookup coverage audit
   - final token verify
   - manuel UI smoke checklist

4. **Asagidaki scriptler icin gelistirilmis icerik ver**
   - `10_verify_topography_local_runtime.ps1`
   - `20_audit_topography_data_coverage.ps1`
   - `30_remote_sync_diagnostic.ps1`

5. **Iki ayri durum ver**
   - local technical completion
   - product completeness

## Onemli gercek eksikler

Bunlari eksik olarak ele al:

- local final 100 olsa da remote branch push reddedildi (`non-fast-forward`)
- England-wide topography source kokleri su anda kanitli degil
- `parcel_id=29759443` lookup endpoint 200 donse bile veri `status=no_data` donebilir; bu veri dolulugu eksigidir
- Topography icin gercek parcel click / right panel UI smoke tam kanitli degil

## Yasaklar

- Yeni helper zip dongusu onermeyin
- fake completion onermeyin
- baska page key kullanmayin
- localde var olmayan source dosyalarini varmis gibi kabul etmeyin

## Beklenen cevap formati

ChatGPT su formatta donsun:

1. `LOCAL_100_STATUS`
2. `REMAINING_GAPS`
3. `CHATGPT_CAN_DO`
4. `OPERATOR_MUST_RUN`
5. `SAFE_POWERSHELL_SEQUENCE`
6. `FINAL_DECISION`

Ve her maddede yalnizca bu Topography page-key kapsaminda kal.
