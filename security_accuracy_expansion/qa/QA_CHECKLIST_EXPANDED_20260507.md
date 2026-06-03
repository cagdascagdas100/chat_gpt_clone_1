# Expanded QA Checklist

- Scope guard passes: only `security_accuracy_expansion/` files are produced.
- Live hash verifier is run before and after generation.
- Existing live blockers are reported, not repaired silently.
- Download manifests identify source, URL, timestamp, hash, and status.
- Run manifests state `live_outputs_written=false`.
- Parcel evidence examples state `live_merge_allowed=false`.
- No active `safety_score` or `confidence_score` production is changed.