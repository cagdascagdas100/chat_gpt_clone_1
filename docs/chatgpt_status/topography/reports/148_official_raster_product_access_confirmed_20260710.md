# Topography 148 - Official Raster Product Access Confirmed

Page key: topography
Layer: Topography / Height Difference
Final: false

## Scope
Continue Height Difference work for the three starter parcels without inventing numeric height values.

Starter candidates:
- parcel_2757 / 52213412 / 51.6167362, -0.1421556 / BNG tile TQ2892
- parcel_2758 / 52213916 / 51.6168592, -0.1417993 / BNG tile TQ2892
- parcel_2759 / 52040420 / 51.6169525, -0.1430858 / BNG tile TQ2892

## Official source access confirmation

### Preferred source
Defra / Environment Agency Data Services Platform Survey Data Download.

Evidence:
- The official page is the Defra Data Services Platform.
- It exposes Defra Survey Data Download.
- It includes Layers Download.
- It is available under Open Government Licence v3.0 except where otherwise stated.

Use this route first for Environment Agency / Defra LiDAR DTM or DSM tile coverage for the TQ2892 area.

### Fallback source
Copernicus DEM - Global and European Digital Elevation Model.

Evidence:
- Copernicus DEM is a Digital Surface Model.
- It provides GLO-30 and GLO-90 global coverage.
- GLO-30 is global at 30 m resolution.
- It is accessible via Copernicus Browser or API.
- GLO-30 and GLO-90 datasets have worldwide free-license access conditions for download by eligible registered users/general public as described by Copernicus Data Space.

Use Copernicus DEM GLO-30 only if LiDAR DTM/DSM tile sampling is unavailable or blocked.

## Sampling status
No numeric elevation is written in this step.

Required next operation:
1. Query/download official raster tile covering BNG tile TQ2892.
2. Sample raster values at the three BNG/WGS84 centroids.
3. Record source product, resolution, acquisition/release metadata, file path or source URL.
4. Write elevation_sea_level_m only after sampling proof exists.
5. Compute regional average only after minimum verified same-authority sample count is satisfied.

## Data integrity
- final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false
- elevation values remain null
- height difference remains null
