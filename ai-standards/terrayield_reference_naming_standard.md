# TerraYield Reference Naming Standard

Project slug: `terrayield_land_intelligence`

## Rule
Every generated task, result, heartbeat, slot reference, evidence file, score file and report must start with the project slug or include it as the first structured segment.

## Preferred patterns

```text
terrayield_land_intelligence__task_<number>__<purpose>.json
terrayield_land_intelligence__slot_backend__latest.md
terrayield_land_intelligence__slot_frontend__latest.md
terrayield_land_intelligence__slot_ops__latest.md
terrayield_land_intelligence__slot_data_cache__latest.md
terrayield_land_intelligence__slot_tests__latest.md
terrayield_land_intelligence__scorecard__<run_id>.csv
terrayield_land_intelligence__status__<run_id>.json
terrayield_land_intelligence__evidence__<source>__<run_id>.md
terrayield_land_intelligence__parcel_match__<run_id>.md
terrayield_land_intelligence__sales_evidence__<run_id>.md
```

## Compatibility rule
Legacy names such as `slot-backend.md` can remain for the existing panel, but each legacy file should have a project-prefixed alias. New logic should prefer the project-prefixed alias.

## Slot naming

```text
backend      -> terrayield_land_intelligence__slot_backend__latest.md
frontend     -> terrayield_land_intelligence__slot_frontend__latest.md
ops          -> terrayield_land_intelligence__slot_ops__latest.md
data-cache   -> terrayield_land_intelligence__slot_data_cache__latest.md
tests        -> terrayield_land_intelligence__slot_tests__latest.md
```

## Reason
This avoids mixing TerraYield outputs with other project pages, other ChatGPT runner pages, or future AAYS subprojects.
