# Batch 168 — Parcel Label / Distance Property Types

- Status: `QUEUED_PENDING_SINGLE_RUNNER_VALIDATION_NOT_COMPLETED`
- Candidate rows: `18`
- Category balance: `3` rows in each of the six property-type categories
- Initial average accuracy: `3.594/4`
- Web pending rows published: `18`
- Runner completed rows: `0`
- Browser-proven rows: `0`
- Target tracked rows after queue: `170`
- Target program-layer count only if all currently pending batches are accepted: `86`

## Research batch

Retail: The Oracle Reading, Silverburn Shopping Centre, Lakeside Shopping Centre.

Mixed: Greenwich Peninsula, Royal Arsenal Riverside, Elephant Park.

Detached: Blickling Estate, Attingham Park, Castle Drogo.

Apartment: Wardian London, DAMAC Tower Nine Elms, One Nine Elms.

Office: Bloomberg London, 25 Churchill Place, 5 Broadgate.

Industrial: SEGRO Park Rainham, Prologis Park Coventry, SEGRO Park Kettering.

The research payload intentionally asserts no coordinates. The canonical F portable shared runner must remote-validate each source, bind or reject exact building/parcel geometry, append accepted rows individually to the program layer and browser matrix, and generate output plus browser proof before any row becomes completed.

Safety: `single_runner_only=true`, `new_runner=false`, `parallel_runner=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
