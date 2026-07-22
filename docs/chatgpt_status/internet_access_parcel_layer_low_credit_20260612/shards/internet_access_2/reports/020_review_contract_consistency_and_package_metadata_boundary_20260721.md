# Review-contract consistency and official package metadata boundary

- The official Spring 2026 publication page currently lists the fixed broadband package as 32.3 MB; a prior readback recorded 32.2 MB. Rounded display size is metadata only.
- The outer archive retains an r1 filename. Internal V2 correctness is established only by zero internal postcode r1 files, exactly 121 internal r2 files, 1,741,096 unique postcode rows and corrected CW/CV and MK/ME SHA-256 pairs.
- No public checksum was found on the publication page. The canonical runner must compute the downloaded ZIP SHA-256.
- Added a 14-check fail-closed consistency audit across tasks, progress, readiness, scope and operation rows before any network request.
- Deterministic totals: consistency 14/14, wrapper 36/36, web contract 18/18, combined 260/260.
- Real rows remain 0/30,761; business writes remain 0; final_ready=false.
