# height_difference_1 ArcGIS candidate query links

Evidence-only helper links. These queries target the public `Land_Registry_INSPIRE` ArcGIS FeatureServer layer whose data last edit is 5 July 2026. They do not replace current HMLR raw GML terminal validation.

- parcel_2759: https://services2.arcgis.com/LrUbY6lLLgV3tEa5/ArcGIS/rest/services/Land_Registry_INSPIRE/FeatureServer/0/query?geometry=528658.656%2C192535.809&geometryType=esriGeometryPoint&inSR=27700&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=pjson
- parcel_2758: https://services2.arcgis.com/LrUbY6lLLgV3tEa5/ArcGIS/rest/services/Land_Registry_INSPIRE/FeatureServer/0/query?geometry=528747.982%2C192527.698&geometryType=esriGeometryPoint&inSR=27700&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=pjson
- parcel_2757: https://services2.arcgis.com/LrUbY6lLLgV3tEa5/ArcGIS/rest/services/Land_Registry_INSPIRE/FeatureServer/0/query?geometry=528723.664%2C192513.392&geometryType=esriGeometryPoint&inSR=27700&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=pjson

Fail-closed rule: only explicit `inspireid` returned by point intersection may be used as secondary identity evidence; numeric promotion remains blocked until current HMLR Barnet+Enfield raw GML/SHA and revision-14 integrity checks pass.
