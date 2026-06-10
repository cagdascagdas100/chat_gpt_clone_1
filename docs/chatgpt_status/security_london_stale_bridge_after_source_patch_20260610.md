# Security London stale bridge after source patch

Date: 2026-06-10
Page scope: security/asayis London-only pilot
Repo/branch: cagdascagdas100/chat_gpt_clone_1 / main

## Finding

The latest runner capture report proves the local bridge ran before pulling the source-restore parser fix. The runner report says:

- `HEAD is now at 099fb6c97 Fix security London runner capture UTF8 logging`
- The source-restore fallback still failed on the Unicode separator/parser error at line 89.

The GitHub source script on `main` is already patched to ASCII separator:

- `foreach($p in $ProbeResults){ $md += "- $($p.id): $($p.status) $($p.http_status) - $($p.url)" }`

Therefore the immediate blocker is not the source script anymore; it is that the local bridge must sync to the newer commit containing the source script fix and rerun the capture helper.

## Current blocker

The local bridge has not yet rerun after the source-restore parser fix commit. Expected outputs are still missing:

- `ai-results/security_london_source_restore_latest.json`
- `ai-results/security_london_source_restore_latest.md`
- `docs/chatgpt_status/security_london_source_restore_status_20260609.md`

## Required next local action

Run the existing single helper after syncing main:

```powershell
cd C:\AAYS_GITHUB_BRIDGE_CLEAN2; git fetch origin main; git reset --hard origin/main; powershell -ExecutionPolicy Bypass -File .\ai-task-scripts\security_london_runner_capture_once_20260610.ps1
```

Do not paste PowerShell stdout into chat. The helper must push GitHub evidence.

## Expected next GitHub evidence

- `ai-results/security_london_source_restore_runner_latest.txt`
- `ai-results/security_london_source_restore_latest.json`

## Safety

- DB write: false
- DDL/migration: false
- Production deploy: false
- Fake data: false
