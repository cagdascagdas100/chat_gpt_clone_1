# Site Filtre Gereksinimleri

Katman: Distance to Nearby Property Types

Veri kaynagi:
england_map_web/data/distance_property_types/distance_property_types_verified.geojson

Zorunlu UI:

- Katman acildiginda sadece verified veya manual-review featurelar gorunmeli.
- Legend alti kategoriye gore ayrilmali.
- Popup ve sag panel property type, color category, distances, evidence, photo AI evidence, source date, matching method, accuracy score/label, conflict status, manual review state ve explanation gostermeli.
- Guncel degisiklikler filtresi properties.changed_in_latest_run === true olan featurelari gostermeli.
- change_reason alani popup veya panelde gosterilmeli.

Kaniti zayif kayit icin uyarı:
Bu parcel icin yapi turu kaniti 3/4 dogruluk esigine ulasmadi. Manuel inceleme onerilir.
