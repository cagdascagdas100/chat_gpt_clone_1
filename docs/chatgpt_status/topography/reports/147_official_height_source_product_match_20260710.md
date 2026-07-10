# Topography 147 - Official Height Source Product Match

Page key: topography
Layer: Topography / Height Difference
Branch: codex/aays-single-runner-v5-20260706
Final: false

## Purpose
Match the three BNG-ready starter parcels to official height source product routes before numeric elevation sampling.

## Candidate parcels
- parcel_2757 / parcel_ref 52213412 / WGS84 51.6167362, -0.1421556 / BNG 528723.664E 192513.392N / tile TQ2892
- parcel_2758 / parcel_ref 52213916 / WGS84 51.6168592, -0.1417993 / BNG 528747.982E 192527.698N / tile TQ2892
- parcel_2759 / parcel_ref 52040420 / WGS84 51.6169525, -0.1430858 / BNG 528658.656E 192535.809N / tile TQ2892

## Official product routes
1. Defra / Environment Agency Data Services Platform Survey Data Download
   - Role: preferred England LiDAR DTM/DSM source where coverage exists.
   - Required next operation: query/download raster tile covering BNG tile TQ2892 and sample numeric elevation from official raster.
   - Current status: product route matched, sampling pending.

2. Copernicus DEM GLO-30 fallback
   - Role: official 30 m global DSM fallback if England LiDAR tile cannot be sampled.
   - Required next operation: download/access the GLO-30 geocell containing WGS84 51.6169, -0.142 and sample numeric elevation from the source grid.
   - Current status: product route matched, sampling pending.

## Numeric value rule
No elevation value, regional average, or height difference is written in this step.
Numeric values may only be written after source-backed raster/tile sampling proof exists.

## Regional average rule
Regional average uses same local authority group Barnet and requires at least 5 verified height samples before computing:
elevation_difference_regional_average_m = elevation_sea_level_m - regional_average_elevation_m

## Output status
- official_height_source_product_match_ready: true
- candidate_count: 3
- verified_height_rows: 0
- height_difference_values_written: false
- final_ready: false
- fake_data: false
