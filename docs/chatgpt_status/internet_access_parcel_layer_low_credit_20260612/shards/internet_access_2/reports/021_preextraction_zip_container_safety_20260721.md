# internet_access_2 — pre-extraction ZIP container safety

- Scope: parcel rows 30,762–61,522 only.
- The official outer archive name and rounded display size remain metadata, not revision or integrity proof.
- `Invoke-WebRequest` retains `-OutFile` without `-PassThru`; Microsoft documents an empty-file risk for the combined form.
- The downloaded archive is audited before `Expand-Archive`.
- Fail-closed ZIP gates reject absolute paths, parent traversal, normalized duplicate paths, encrypted entries, symlinks, unsupported compression and CRC failure.
- The container must contain zero internal postcode `r1` files and exactly 121 unique corrected `r2` postcode-area files directly under `postcode_files`.
- ZIP container audit SHA-256 is inserted into the same twelve-artifact provenance chain as the downloaded ZIP, V2 report, bounded slices, candidate outputs and web readbacks.
- Deterministic results: ZIP safety 18/18; inner runner 39/39; provenance 24/24; wrapper 36/36; web 20/20; consistency 14/14; combined 292/292.
- Real source rows remain 0/30,761 until the existing shared runner passes all readiness gates.
- Business rows, scores, DB writes, migrations and deployments remain zero/false. `final_ready=false`.
