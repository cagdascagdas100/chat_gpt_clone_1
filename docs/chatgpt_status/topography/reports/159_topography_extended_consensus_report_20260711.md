# Topography 159 â€” Extended Multi-DEM Consensus Batch

- Candidate parcel rows: 3
- Regional control samples inherited: 8
- EU-DEM 25 m source-backed rows: 3
- SRTM 90 m cross-check rows: 3
- SRTM 30 m QC rows: 3
- ASTER 30 m QC rows: 3
- Consensus rows: 3
- High consistency rows: 0
- Moderate consistency rows: 2
- Manual review rows: 1
- Browser rendered rows: 3
- Total serial stages represented: 15
- Completion percent after real runner proof: 60
- Accuracy: 2.5/4 fallback multi-DEM consensus
- final_ready: false
- fake_data: false

All work ran serially inside the existing F-portable canonical shared runner. No second or parallel runner was opened. Extra DEMs are quality-control sources only and do not promote the rows to primary or final status. Real parcel boundaries, primary CopDEM GLO-30 raster sampling and official Environment Agency LiDAR or Ordnance Survey Terrain numeric validation remain mandatory.