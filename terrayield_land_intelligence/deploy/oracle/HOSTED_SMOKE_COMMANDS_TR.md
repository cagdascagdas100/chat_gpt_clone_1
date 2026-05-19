# Hosted Smoke Commands - TerraYield Oracle edalmo

## Scope

Run only after:

- `https://api-terrayield.edalmo.com` resolves.
- `https://terrayield.edalmo.com` resolves.
- Backend container is running.
- Postgres/PostGIS runtime connectivity is verified without printing secrets.

## Environment values

Set only public-safe values in the shell running the smoke check:

```text
TERRAYIELD_PUBLIC_API_URL=https://api-terrayield.edalmo.com
TERRAYIELD_FRONTEND_PUBLIC_URL=https://terrayield.edalmo.com
TERRAYIELD_CLOUD_DB_VERIFIED=true
```

## Smoke command

From `terrayield_land_intelligence`:

```text
python scripts/cloud_smoke_check.py
```

## Expected success fields

```text
public_url_verified=true
cloud_db_verified=true
frontend_public_url_verified=true
hosted_smoke_status=passed
ok_count=6
total=6
classification=CLOUD_RUNTIME_READY
```

## Failure rule

HTTP 4xx and 5xx responses must fail the smoke. Only HTTP 2xx/3xx count as success.

## Safety

Do not print or paste DATABASE_URL, passwords, tokens, or private keys.
