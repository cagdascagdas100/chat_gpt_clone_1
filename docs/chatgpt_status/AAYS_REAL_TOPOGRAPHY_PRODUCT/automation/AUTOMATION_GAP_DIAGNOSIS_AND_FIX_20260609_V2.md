# AAYS real topography automation gap diagnosis and fix

## Current target
Keep the work on a single existing Kalife runner. The user should only write `devam et`. ChatGPT should read GitHub reports, decide the next action, write new task or prompt files, and continue the loop.

## What is working
- ChatGPT can read and write repository files through GitHub.
- Product code has already advanced to the current real-product estimate of 84%.
- The UI/cache/backend route side is not the current blocker.
- Heavy future work must stay on F drive.
- Existing C drive runner/queue infrastructure should not be moved for now.

## What is not working
The missing automation link is not the runner count. The missing link is task delivery.

ChatGPT writes task files under the repository status area, but the local Kalife runner only executes jobs that appear in its local queue. There is no confirmed active poller that watches the GitHub task folder and copies new tasks into the local runner queue.

Therefore this chain is broken:

```text
GitHub task file -> local runner queue -> Kalife runner execution -> GitHub report file -> ChatGPT reads report
```

The break is between `GitHub task file` and `local runner queue`.

## Why percentage is not increasing
Percentage stays at 84% because the expected execution reports are not appearing in GitHub:

```text
bridge_poller_status_*.txt
real_topography_source_inventory_*.txt
```

No report means ChatGPT has no machine-readable output to analyze and no proof that the runner executed the next job.

## Required fix
Create or start a persistent bridge/poller on F drive. Its only job is:

1. Pull the current branch into the F-drive worktree.
2. Inspect the project runner task folder in GitHub/worktree.
3. Copy new PowerShell task files into the existing local runner queue.
4. Start the existing single Kalife runner if it is not running.
5. Write a status report back to the GitHub reports folder.
6. Repeat on a short interval.

## Disk policy
- New heavy work: F drive.
- New temp/artifact/source inventory/browser evidence/API smoke outputs: F drive.
- Existing C runner/queue: keep as-is and use only as the existing runner handoff point.
- Do not migrate existing C infrastructure unless explicitly requested later.

## Next expected progress
- 84 -> 85: bridge/poller status report appears in GitHub.
- 85 -> 88: real elevation/source artifact found or source inventory proves next acquisition step.
- 88 -> 92: lookup/API smoke passes.
- 92 -> 100: browser popup proof passes.

## Manual-output rule
The user should not paste PowerShell output into chat. PowerShell output must be captured into GitHub report files.
