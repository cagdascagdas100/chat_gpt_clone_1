# Estate Final Dependency DAG 009

## Completed or scaffolded
1. Parcel group scaffold -> agent schema -> source discovery -> local candidate extraction -> dry-run export -> parallel contracts.

## Parallel groups used
- Coverage mapping contract
- Trust/truth scoring contract
- Verified export template
- Parcel join contract

## Sequential blockers
1. Verified estate-agent source rows must exist before final directory import.
2. Real TerraYield parcel master/export must exist before parcel_id join.
3. DB write requires explicit user approval.
4. Production deploy requires explicit user approval.

## Safe current state
Read-only integration readiness is complete; production data completion needs external verified data.
