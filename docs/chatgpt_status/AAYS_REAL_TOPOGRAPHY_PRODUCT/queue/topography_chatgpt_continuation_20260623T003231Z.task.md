---
page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
task_id: topography_chatgpt_continuation_20260623T003231Z
repo: cagdascagdas100/chat_gpt_clone_1
requested_branch: aays-runner-v17-icon-work-20260603-232706
script: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/automation/topography_chatgpt_continuation_20260623T003231Z.ps1
expected_report: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_chatgpt_continuation_20260623T003231Z_work_summary.txt
expected_status: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/topography_chatgpt_continuation_20260623T003231Z_queued.status.txt
mode: read_only_diagnostic_continuation
no_second_runner: true
fake_final_allowed: false
---

# topography_chatgpt_continuation_20260623T003231Z

## Amaç
Topography local 100 durumunu düşürmeden kalan gerçek eksikleri teşhis etmek:

- remote branch sync / non-fast-forward
- England-wide veri kapsamı
- parcel lookup no_data oranı
- manuel UI smoke eksikliği
- pb naming debt notu

## Kabul kriterleri

1. Runtime verify raporu üretilir.
2. Remote sync diagnostic raporu üretilir.
3. Data coverage audit raporu üretilir.
4. UI smoke checklist operatöre verilir.
5. Bu görev yeni final marker üretmez.

## Yasaklar

- İkinci runner başlatma.
- DB write, migration, seed, production deploy yapma.
- Local canonical final tokenlarını bu görevde yeniden yazma.
- Başka page-key altında dosya üretme.
