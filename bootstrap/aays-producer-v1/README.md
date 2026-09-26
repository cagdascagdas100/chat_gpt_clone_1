# AAYS Producer V1

This bootstrap replaces the normal Downloads handoff for AAYS ChatGPT slots.

## One-time setup on each producer PC

1. Install Python 3 and GitHub CLI.
2. Authenticate once with `gh auth login` to `cagdascagdas100/chat_gpt_clone_1`.
3. Run PowerShell as the normal user:

   `powershell -ExecutionPolicy Bypass -File .\install_aays_producer.ps1`

4. Configure the browser/profile used for AAYS so generated files download to:

   `C:\AAYS_Producer\outbox`

The installer registers a hidden at-logon task named `AAYS Producer Uploader`.
It validates every package, uploads the ZIP and external SHA-256 sidecar in one
commit, then moves the local source to `sent`. Invalid packages go to `rejected`.

The uploader never reads the normal Downloads directory and never places a
GitHub token in a prompt, package, script or state file.
