# AAYS Source and Storage Policy V1

## Required source lineage

Every published or candidate data artifact must identify:

- official source page URL and direct artifact URL when available;
- source snapshot date and retrieval timestamp;
- SHA-256 of every downloaded source artifact;
- archive member, table, row, field, or geographic unit actually used;
- transformation and parcel-binding method;
- measurement level and whether the value is measured, a proxy, or a candidate;
- final gate state and the factual reason for every blocked row.

Missing data remains `NO_DATA_NOT_INFERRED`. Area-level or national evidence must not
be presented as a parcel measurement.

## Storage boundaries

- Large raw archives stay under the portable runtime cache and are not committed.
- Git stores only the minimum derived rows needed by the application and a compact
  evidence manifest containing source URL, date, SHA-256, relevant member/field
  references, transformation, and gate result.
- Browser profiles, duplicate downloads, full-page captures, temporary files, and
  unchanged retry outputs are not retained.
- Temporary files used for atomic writes are deleted immediately after replacement.
- A source is fetched again only when its official version, ETag, Last-Modified value,
  or expected SHA-256 changes.

## Runtime behavior

- Hash and inventory checks run before expensive parsing.
- A confirmed unchanged negative inventory skips repeated full scans.
- Network failures use bounded backoff and do not block unrelated slots.
- Publishing remains serialized, while source discovery, parsing, and validation may
  run concurrently within the RAM-safe worker limit.
