# New ChatGPT Page Continuation Template

Use this when a new ChatGPT/Codex page continues AAYS work.

```text
REPO_FULL_NAME=cagdascagdas100/chat_gpt_clone_1
BRANCH=main
PAGE_KEY=<PAGE_KEY>
LOCAL_REPO=<LOCAL_REPO>
ACTIVE_RUNNER_MODE=single_shared_runner
CANONICAL_QUEUE=docs/chatgpt_status/<PAGE_KEY>/queue/<TASK_ID>.json
STATUS_DIR=docs/chatgpt_status/<PAGE_KEY>/status
REPORT_DIR=docs/chatgpt_status/<PAGE_KEY>/reports
HEARTBEAT_DIR=docs/chatgpt_status/<PAGE_KEY>/heartbeat
COMPLETED_DIR=docs/chatgpt_status/<PAGE_KEY>/completed
ALLOWED_PATHS=docs/chatgpt_status/<PAGE_KEY>/
```

Prompt:

```text
Devam et: Bu sayfadaki gorevi mevcut repo/branch/page-key baglamini esas alarak tek shared/canonical runner ve GitHub kanitli queue/status/report/heartbeat/completed akisi ile surdur. Yeni paralel runner baslatma. Sahte completed, final_ready veya yuzde 100 uretme. allowed_paths disina cikma. Gercek runner outputlarini GitHub'dan dogrula. Eksik kanit varsa blocker olarak yaz ve kaldigin yerden ilerlet.
```

Short response format:

```text
Bekleme: <dakika>
Tamamlanan islem: <%>
Kalan islem: <%>
Runner durumu: <status>
Final: <true/false>
Blocker: <blocker>
```
