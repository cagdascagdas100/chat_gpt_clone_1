# Estate 011 Dependency + Parallel Plan

Bağımlı zincir:
1. Verified agent source rows
2. Evidence rows
3. Truth score /4
4. Trust score /10
5. Coverage parcel_group_ids
6. Real TerraYield parcel_id join
7. Final Excel/API/DB import

Paralel işler:
- candidate review queue
- parcel master scan
- acceptance gate
- dependency report

DB write ve production deploy kapalı.
