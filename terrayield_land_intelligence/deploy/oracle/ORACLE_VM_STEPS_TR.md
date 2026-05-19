# Oracle VM Setup Steps - TerraYield / AAYS

## Scope

This file lists the VM-side setup sequence after the Oracle Always Free VM exists. It contains no real secret values.

## Sequence

1. Install base packages: Docker, Git, Curl, firewall tooling.
2. Enable Docker for the VM user.
3. Allow public ports 80 and 443.
4. Keep database port 5432 closed to the public internet.
5. Clone the repository on the VM.
6. Check out branch `security-accuracy-expansion-20260508`.
7. Copy `deploy/oracle/vm_env_template.example` to a VM-local private env file.
8. Fill secret values only on the VM.
9. Run `deploy/oracle/bootstrap_readonly_checks.sh`.
10. Start `docker-compose.cloud.yml` only after DNS points to the VM and private env values are filled.
11. Confirm containers are healthy.
12. Confirm `https://api-terrayield.edalmo.com` and `https://terrayield.edalmo.com` resolve through Caddy.

## Notes

- Do not paste real secrets into ChatGPT, Codex, GitHub issues, or reports.
- Do not open Postgres directly to the public internet.
- Keep classification as `CLOUD_READY_PENDING_PROVIDER` until hosted smoke and performance evidence pass.

## Safety

- secret_values_printed=false
- db_write=none during preparation
- ddl=none during preparation
- migration_apply=none during preparation
- prod_deploy=none during preparation
