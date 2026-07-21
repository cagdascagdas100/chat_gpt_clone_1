# Height Difference 1 — noninteractive publisher authentication recovery

The prior local automation recorded exit code 0, but its publisher could not push because HTTPS GitHub credentials were unavailable in a noninteractive process. No remote revision 13 output or integrity readback exists, so no measurement is accepted.

A guarded, dry-run-first preflight now checks the existing canonical F repository:

- Existing noninteractive `git ls-remote` access is accepted without requiring GitHub CLI.
- If Git access fails, an already-authenticated GitHub CLI session is required.
- `gh auth setup-git --hostname github.com` runs only with explicit `-Apply`.
- A second noninteractive `git ls-remote` must pass after setup.
- Tokens and credential-bearing URLs are never printed.
- The script starts, stops and creates no runner, and performs no result push by itself.
- The next action reuses the existing single runner for exact revision 14.

Validation: `24/24` source-level checks passed. F-host application remains pending. `final_ready=false`.
