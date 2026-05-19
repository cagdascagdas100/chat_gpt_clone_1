# Oracle VM Start Checklist - TerraYield

## Preconditions

- Oracle VM exists.
- DNS records are prepared or ready to be added.
- Branch `security-accuracy-expansion-20260508` is available.
- No real secret is copied into this file.

## Required public DNS names

- `terrayield.edalmo.com`
- `api-terrayield.edalmo.com`

## Required public ports

- `80/tcp`
- `443/tcp`

## Must stay closed publicly

- `5432/tcp` PostgreSQL
- `8010/tcp` backend direct port

## VM-local files

Create a VM-local env file from:

```text
terrayield_land_intelligence/deploy/oracle/vm_env_template.example
```

The filled copy must stay only on the VM.

## Start command pattern

Run on the VM from `terrayield_land_intelligence` only after env values are filled:

```text
docker compose -f docker-compose.cloud.yml --env-file <VM_PRIVATE_ENV_FILE> up -d --build
```

## Safety

- secret_values_printed=false
- db_write=none during preparation
- ddl=none during preparation
- migration_apply=none during preparation
- prod_deploy=none during preparation
