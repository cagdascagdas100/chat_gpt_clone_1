# Distance Property Types - Site Integration Checklist

Layer: `Distance to Nearby Property Types`

Required data file:

```text
england_map_web/data/distance_property_types/distance_property_types_verified.geojson
```

Required UI behavior:

- Show only verified or manual-review parcel features from the GeoJSON.
- Render legend colors for Industrial Unit, Detached Home, Retail Property, Apartment Building, Office Building, Mixed Building, and Unknown/Manual Review.
- Popup/right panel must show evidence fields, photo AI observation, source date, matching method, accuracy label/score, conflict status, manual-review state, and explanation.
- Add `Guncel degisiklikler` filter that selects only features where `properties.changed_in_latest_run === true`.
- When evidence is below 3/4, show: `Bu parcel icin yapi turu kaniti 3/4 dogruluk esigine ulasmadi. Manuel inceleme onerilir.`

No production deploy, DB write, DDL, or migration is authorized by this task.
