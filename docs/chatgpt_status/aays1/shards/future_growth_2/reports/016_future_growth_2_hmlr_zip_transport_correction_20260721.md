# future_growth_2 HMLR ZIP transport correction

- Scope remains `future_growth_2` only.
- The official HMLR INSPIRE page is current for July 2026 and lists Royal Borough of Greenwich among authority downloads.
- The authority download route is ZIP transport even though the user-facing link is labelled as a GML download.
- The previous downloader accepted only `.gml` paths and attempted to validate the archive response as raw XML/GML; a real live download would therefore fail before intersection.
- `003_acquire_hmlr_inspire_authority_gml.py` now reuses a cookie-aware opener, accepts ZIP/GML/XML authority routes, extracts exactly one GML/XML member in memory, blocks zip-slip paths, caps archive/member size and compression ratio, and hashes both archive and extracted GML.
- Executed downloader regression: `14/14 PASS`.
- This is a real code-path correction, not a real HMLR download. Actual downloads, exact intersections, canonical parcel matches and product scores remain `0`.
- Direct Planning Data `period=current` responses and the real 30,761-row product matrix remain pending.
- `final_ready=false`.
