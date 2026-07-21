# future_growth_3 — Official source wave 9

- Slot: `future_growth_3`
- Parcel shard: `61523–92283` (`30,761`)
- New records: `16`
- Eligible source candidates: `16`
- High source confidence: `16`
- Wave average source confidence: `97.6/100`
- Combined researched: `97`
- Combined eligible: `92`
- Combined excluded: `5`
- Combined high source confidence: `85`
- Combined average source confidence: `96.4/100`
- Official source families: `24`
- Canonical parcel matches: `0`
- Future Growth scores: `0`

## Added source families

- London Borough of Sutton
- Redbridge Council
- London Borough of Bromley
- London Borough of Bexley

## Quality controls

- Four Redbridge records have a structured `maximum-net-dwellings=0`; they remain source candidates but are explicitly routed to zero-capacity review.
- Nine records expose dwelling counts only in official notes. Those counts are kept in `described_dwellings` and are not promoted into `maximum_net_dwellings`.
- Blank end dates are preserved; no parcel row or score is inferred from point proximity.
- Canonical shard export is still absent, so geometry crosswalk and the 30,761-row matrix remain blocked.

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
