# AAYS 051 Open Items Completion Plan

Generated: 2026-05-14

## Goal
Close the remaining technical gaps that were not proven by the final summary signal.

## Constraints
- No database writes.
- No SQL mutation statements.
- No secret printing.
- No UI patch.
- No Docker build or destructive container recreation.

## Work packages

1. Runner automation hardening
   - Verify the CLEAN2 runner autostart installer exists.
   - Run the scheduled-task installer if possible.
   - Report whether scheduled tasks are present.

2. Docker and PostGIS recovery
   - Verify Docker Desktop/daemon availability.
   - Inventory containers and ports.
   - Start known stopped PostGIS containers only with `docker start`.
   - Do not recreate or rebuild containers.

3. Read-only database probe
   - Prefer container-local `docker exec` into known PostGIS containers.
   - Run only read-only SQL: `SELECT version(), current_database(), current_user` and table-regclass probes.
   - Do not use host password strings and do not print secrets.

4. Runner task-format standardization
   - Restore a runnable `current-task.json` format with `script_path`.
   - Produce a report with pass/fail signals for every open item.

5. Final decision
   - If runner autostart is installed and at least one read-only DB probe succeeds, mark plan progress 95.
   - If only automation hardening succeeds but DB auth/probe fails, mark plan progress 88.
   - If neither succeeds, keep plan progress 80 and report next manual action.

## Expected output
- `ai-results/aays-051-open-items-completion.report.md`
- Updated heartbeat from the runner.
