# FG444 London F-drive workspace rule

Scope: London-only FG444 pilot.

Rule:
- New FG444 London work must use F drive.
- Do not move existing C drive work in this phase.
- Do not create heavy new outputs under C drive.

Preferred local workspace:
- Workspace root: `F:\chatgpt\AAYS_WORK\FG444_LONDON`
- Repo copy: `F:\chatgpt\AAYS_WORK\FG444_LONDON\repo`
- Logs: `F:\chatgpt\AAYS_WORK\FG444_LONDON\logs`
- Artifacts: `F:\chatgpt\AAYS_WORK\FG444_LONDON\artifacts`

GitHub-readable outputs:
- Result branch: `fg444-london-readonly-audit-latest`
- Status root in repo: `docs/chatgpt_status/FG444_LONDON_READONLY_AUDIT/`

Safety:
- Read-only audit first.
- No DB write.
- No DDL.
- No migration.
- No production publish.
- No fake rows.

Operational note:
The F-drive repo copy should push only lightweight final reports to GitHub. Large intermediate files should stay under the F-drive workspace.
