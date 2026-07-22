# future_growth_2 — Wave 47 Sevenoaks

Only `future_growth_2` source-candidate preparation was changed. Thirty official Sevenoaks District Council brownfield records were reviewed from MHCLG Planning Data.

## Result

- 14 current records retained for high-confidence point-only review.
- 6 current records held fail-closed: official unsuitable/not-carried-forward notes, two sub-10-dwelling sites, one structured/narrative capacity mismatch and one expired permission note.
- 10 explicit-end historical records excluded, including one employment-only record without structured residential maximum.
- Provider `1970-01-01` values on not-permissioned records were treated as sentinel values and normalized to null, not interpreted as real permission dates.
- Five grouped exact-reference repository searches returned no indexed overlap; this is duplicate screening only.
- Structural checks 138/138 and official remote field checks 120/120 passed.

Point locations are not site boundaries or parcel identity. No canonical row, HMLR intersection, Future Growth score or business row was produced. `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.