# New ChatGPT Page Continue Prompt

Use the active repo, branch, and page key. Write exactly one queue task under:

```text
docs/chatgpt_status/<PAGE_KEY>/queue/<TASK_ID>.json
```

Rules:

- Use the existing single shared runner.
- Do not start a new parallel runner.
- Keep `new_runner_allowed=false`.
- Keep `single_shared_runner_required=true`.
- Keep `final_ready=false` until real GitHub-visible runner output and gate evidence exist.
- Do not fabricate completed output, percent 100, rows, sources, browser proof, or production evidence.
- Do not write outside `allowed_paths`.
- Do not perform DB writes, migrations, DDL, or production deploys.
- Read progress only from GitHub-visible queue/status/report/heartbeat/completed or blocked evidence.
- If evidence is missing, report the blocker instead of claiming success.

Short output:

```text
Bekleme: <dakika>
Tamamlanan islem: <%>
Kalan islem: <%>
Runner durumu: <status>
Final: <true/false>
Blocker: <blocker>
```
