# parcel_label_3 — Lambeth LLPG exact query requests

Continuation key: `26d2706c9fe7886330bc70256fd7d0eebdfb344cb320c087fdde79fa8e1e0342`

These links query the official London Borough of Lambeth LLPG postal-address feature layer within 30 metres of each canonical parcel point. Results remain candidates until nearest-distance, postcode and BLPUCLASS checks pass.

- [parcel_61523 official LLPG query](https://gis.lambeth.gov.uk/arcgis/rest/services/LambethLLPGAllPostalAddresses/MapServer/0/query?where=1%3D1&geometry=-0.1387938%2C51.4196454&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&distance=30&units=esriSRUnit_Meter&outFields=OBJECTID%2CUPRN%2CFULLADDRESS%2CSTREET%2CPOSTCODE%2CBLPUCLASS&returnGeometry=true&outSR=4326&f=geojson)
- [parcel_61524 official LLPG query](https://gis.lambeth.gov.uk/arcgis/rest/services/LambethLLPGAllPostalAddresses/MapServer/0/query?where=1%3D1&geometry=-0.1407703%2C51.4170637&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&distance=30&units=esriSRUnit_Meter&outFields=OBJECTID%2CUPRN%2CFULLADDRESS%2CSTREET%2CPOSTCODE%2CBLPUCLASS&returnGeometry=true&outSR=4326&f=geojson)
- [parcel_61525 official LLPG query](https://gis.lambeth.gov.uk/arcgis/rest/services/LambethLLPGAllPostalAddresses/MapServer/0/query?where=1%3D1&geometry=-0.1398845%2C51.4167453&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&distance=30&units=esriSRUnit_Meter&outFields=OBJECTID%2CUPRN%2CFULLADDRESS%2CSTREET%2CPOSTCODE%2CBLPUCLASS&returnGeometry=true&outSR=4326&f=geojson)

Correction applied 2026-07-29T14:28:00Z: query parameter separators are literal `&`; the prior request incorrectly encoded separators as `%26` inside the `where` value.

No second task or runner is created by this request artifact.
