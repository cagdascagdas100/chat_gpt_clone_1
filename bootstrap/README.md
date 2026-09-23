# AAYS ChatGPT producer transport

Install this once on every Windows PC whose Downloads folder receives AAYS ZIP packages from ChatGPT.

1. Download `AAYS_CHATGPT_PRODUCER_KIT.zip` and verify its SHA-256 against `AAYS_CHATGPT_PRODUCER_KIT.zip.sha256`.
2. Extract the ZIP.
3. Run `INSTALL_ON_THIS_PC.ps1` with PowerShell.
4. Run `START_NOW.cmd` once.

The kit also includes the current Plan 0 and Layer24 start/continue prompts under
`PROMPTS/`. Use those files instead of older saved continuations. Their mandatory
gate keeps area joins, direct parcel measurements, building classification and
distinct planned-building counts separate, and requires GitHub transport proof.

The uploader validates producer ZIP contents and SHA-256 sidecars, retains the original download, and commits valid packages to one of these paths:

- `incoming/plan0/<COMPUTERNAME>/`
- `incoming/layer24/<COMPUTERNAME>/`

A successful upload writes a local receipt containing `github_path` and `remote_commit_sha`. A ZIP existing only in a producer PC's Downloads folder has not been delivered to the receiving AAYS computer.
