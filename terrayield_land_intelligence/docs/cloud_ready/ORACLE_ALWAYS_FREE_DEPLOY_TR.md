# Oracle Always Free Deploy Runbook - TerraYield / AAYS

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Target architecture

- Frontend: `https://terrayield.edalmo.com`
- Backend API: `https://api-terrayield.edalmo.com`
- Runtime: Oracle Always Free VM
- Backend: FastAPI Docker container
- Database: PostgreSQL/PostGIS Docker container
- Reverse proxy: Caddy

## User manual prerequisites

1. Oracle Cloud account/login.
2. Always Free VM with Ubuntu.
3. SSH key access.
4. Domain DNS access for `edalmo.com`.
5. Oracle VM public IP.

## Recommended VM

- Ampere A1 if available.
- Start with 2 OCPU / 12 GB RAM.
- Disk: at least 50 GB, preferably 100 GB.

## Network policy

Open publicly:

- 80/tcp
- 443/tcp

Restrict:

- 22/tcp to trusted admin IP when possible.

Keep closed publicly:

- 5432/tcp
- 8010/tcp

## VM bootstrap outline

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git ufw
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
```

Log out/in after Docker group change.

## Repo setup outline

```bash
git clone <REPO_URL> AAYS
cd AAYS/terrayield_land_intelligence
git checkout security-accuracy-expansion-20260508
```

## Runtime secret setup

Create a VM-local env file only on the VM. Do not commit it.

Required names:

```text
TY_POSTGRES_PASSWORD=<set_on_vm_only>
TY_DATABASE_URL=<set_on_vm_only>
```

No real secret value should be pasted into ChatGPT/Codex/GitHub reports.

## Start outline

```bash
docker compose -f docker-compose.cloud.yml --env-file /path/to/vm-only.env up -d --build
```

## Read-only verification

```bash
bash deploy/oracle/bootstrap_readonly_checks.sh
docker compose -f docker-compose.cloud.yml ps
```

## Classification rule

Keep `CLOUD_READY_PENDING_PROVIDER` until:

- public backend HTTPS URL works,
- cloud DB/PostGIS runtime is verified,
- public frontend URL works,
- hosted smoke passes 6/6,
- hosted p95/performance is recorded.

## Safety

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
