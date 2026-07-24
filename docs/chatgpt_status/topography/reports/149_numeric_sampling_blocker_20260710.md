# Topography 149 — Numeric sampling blocker

Status: sampling blocked, no source-backed numeric elevation yet.

Scope:
- parcel_2757 / 52213412 / TQ2892
- parcel_2758 / 52213916 / TQ2892
- parcel_2759 / 52040420 / TQ2892

Official source routes already confirmed:
- Defra / Environment Agency Data Services Platform Survey Data Download
- Copernicus DEM GLO-30 fallback

Reason for blocker:
- Official source portals and products are identified.
- Numeric elevation, regional average elevation, and elevation difference cannot be written until an actual official raster/tile is downloaded or accessed and sampled at the parcel centroid.
- The current branch has no 149 numeric sampling result file.

Rules held:
- final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false
- elevation values remain null

Next required operation:
1. Download/access official raster covering BNG tile TQ2892 or Copernicus DEM geocell around 51.6169,-0.142.
2. Sample centroid values.
3. Write numeric values only with source path/URL, source date, and sampling proof.
4. Compute regional average only after minimum verified sample count is satisfied.
