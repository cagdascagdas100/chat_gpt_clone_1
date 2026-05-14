# AAYS/TerraYield Contractor Pipeline Final Local Status

Plan completed: 90%
Plan remaining: 10%

Completed:
- Contractor normalized rows: 317
- Procurement event rows: 421
- Contractor score rows: 317
- Parcel match rows: 29
- App export rows: 317
- Critical provenance missing count: 0
- Fake data: not used
- Missing evidence: remained null until provenance mapping
- DO_NOT_CONTACT gate: preserved in app export
- SQL + CSV transfer files: present under E:\AAYS_DATA\legal\db_transfer

Blocked:
- PostgreSQL/PostGIS load is blocked because DB credentials are not visible.
- Required: DATABASE_URL or PGHOST/PGDATABASE/PGUSER/PGPASSWORD

Final status: fail-closed, ready for DB credential handoff.
