# height_difference_1 — Official point-query manifest

SLOT_ID: `height_difference_1`  
Parcel partition: `1-30761`  
Remote HEAD read before manifest: `d1d4d70b4215d52179a5634bb4b0bd52b62f0c13`  
Generated: `2026-07-20T16:48:00Z`

This manifest contains read-only official-source queries for the three existing candidates. It does not assert a polygon match or numeric elevation until the response is read and recorded.

## Environment Agency coverage metadata

- [EA 1 m DTM extent query for the candidate envelope](https://environment.data.gov.uk/geoservices/datasets/9f0fa3fc-a860-4729-adc9-47fe53f658d0/ogc/features/v1/collections/LIDAR_Composite_1m_DTM_2022_extents/items?bbox=-0.1445%2C51.6160%2C-0.1405%2C51.6180&limit=20&f=text%2Fhtml)
- [EA 2 m DTM extent query for the candidate envelope](https://environment.data.gov.uk/geoservices/datasets/9f0fa3fc-a860-4729-adc9-47fe53f658d0/ogc/features/v1/collections/LIDAR_Composite_2m_DTM_2022_extents/items?bbox=-0.1445%2C51.6160%2C-0.1405%2C51.6180&limit=20&f=text%2Fhtml)
- [EA 1 m DTM WCS capabilities](https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs?request=GetCapabilities&service=WCS&version=2.0.1)
- [EA survey-index OGC API](https://environment.data.gov.uk/spatialdata/survey-index-files/ogc/features/v1)

## HM Land Registry point queries

Layer: `inspire:CP.CadastralParcel`  
CRS: `EPSG:27700`  
Shared query image envelope: `528600,192480,528820,192600`.

- [parcel_2759 / parcel_ref 52040420](https://inspire.landregistry.gov.uk/inspire/ows?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS=inspire%3ACP.CadastralParcel&QUERY_LAYERS=inspire%3ACP.CadastralParcel&STYLES=&SRS=EPSG%3A27700&BBOX=528600%2C192480%2C528820%2C192600&WIDTH=220&HEIGHT=120&FORMAT=image%2Fpng&INFO_FORMAT=application%2Fvnd.ogc.gml&FEATURE_COUNT=10&X=59&Y=64)
- [parcel_2758 / parcel_ref 52213916](https://inspire.landregistry.gov.uk/inspire/ows?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS=inspire%3ACP.CadastralParcel&QUERY_LAYERS=inspire%3ACP.CadastralParcel&STYLES=&SRS=EPSG%3A27700&BBOX=528600%2C192480%2C528820%2C192600&WIDTH=220&HEIGHT=120&FORMAT=image%2Fpng&INFO_FORMAT=application%2Fvnd.ogc.gml&FEATURE_COUNT=10&X=148&Y=72)
- [parcel_2757 / parcel_ref 52213412](https://inspire.landregistry.gov.uk/inspire/ows?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS=inspire%3ACP.CadastralParcel&QUERY_LAYERS=inspire%3ACP.CadastralParcel&STYLES=&SRS=EPSG%3A27700&BBOX=528600%2C192480%2C528820%2C192600&WIDTH=220&HEIGHT=120&FORMAT=image%2Fpng&INFO_FORMAT=application%2Fvnd.ogc.gml&FEATURE_COUNT=10&X=124&Y=87)
- [Current HMLR local-authority GML download page](https://use-land-property-data.service.gov.uk/datasets/inspire/download)

## Independent official elevation source

- [OS Terrain 50, July 2026](https://osdatahub.os.uk/downloads/open/Terrain50)

## Guard

No measured parcel value may be written unless a candidate has a real polygon response and official numeric elevation evidence. Until then use `NO_DATA_NOT_INFERRED`.
