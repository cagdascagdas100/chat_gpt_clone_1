Gas Emissions Eksik Listesi - 2026-06-22

Durum ozeti

1. Aktif rapor zinciri gecmiste `FINAL_READY / 100` demis.
2. Gercek runtime audit sonucu:
   `PARTIAL_RUNTIME_FIXED_NOT_ACCEPTANCE_COMPLETE`
3. App acilis, icon, static dataset ve legend calisiyor.
4. Ama orijinal kabul kuralina gore layer tam bitmis degil.

Tek tek eksikler

1. Parcel polygon thematic output eksik
   - Kodda polygon path var:
     - `buildVisiblePolygonFeatures()`
     - `getLookupMatch()`
   - Fakat aktif runtime `point_source` modunda kaliyor.
   - Sonuc: kullanici gercek parcel polygon boyamasini gormuyor.

2. `directSourceMode=true` uretim kabulunu gizliyor
   - Bu mod layer'i aciyor ama parcel thematic behavior yerine GeoJSON point source gosteriyor.
   - Bu sadece fail-soft runtime acilisi icin uygun; final acceptance icin tek basina yeterli degil.

3. Popup kapanisi tam degil
   - `buildGasEmissionsPopupMetaHtml()` mevcut.
   - `buildParcelPopupContent()` icine inject edilmis.
   - Ama runtime click proof ile dolu gas alanlari kesin olarak kapanmadi.
   - Non-empty gas popup kaniti eksik.

4. Sag panel entegrasyonu net degil
   - Mevcut kanit popup agirlikli.
   - Orijinal istekte popup veya sag panel deniyor.
   - Sag panelde acik bir Gas Emissions detay bloku runtime proof ile dogrulanmadi.

5. Parcel filter behavior kapanmamis
   - Kullanici beklentisi: veri olan parcel thematic ciksin.
   - Mevcut direct point source davranisi bu kontrati zayiflatıyor.

6. Parcel-ID / parcel-ref eslesme mantigi daha tutarli hale getirilmeli
   - Lookup genisletildi ama tek source-of-truth mantigi tam kapanmadi.
   - Bir tiklamada aktif feature props, baska tiklamada source lookup props kullaniliyor.
   - Bu akisin tek modele indirilmesi lazim.

7. Browser acceptance smoke eksik
   - Legend ve toggle smoke var.
   - Ama “parcel tikla -> gerekli alanlari gor” davranisi tam kanitlanmis degil.

Ana nedenler

1. Uretim kabul yerine app-open-safe davranis onceleme mantigi kodda kalmis.
2. Direct source fallback kolayca calisiyor, bu yuzden polygon join path'i kapanmadan sistem “var gibi” gozukuyor.
3. Popup ve thematic parcel flow ayni veri modelinden beslenmiyor.

Bu is tamamlandi denebilmesi icin gerekli son durum

1. Runtime `geometryMode=polygon_join` veya esdeger parcel polygon mode gostermeli.
2. Parcel tiklaninca en az su alanlar dolu olmali:
   - `emission_percent`
   - `emission_level`
   - `emission_color_hex`
   - `confidence`
   - `source_type`
   - `source/evidence`
   - `source_date`
   - `matching_method`
   - `calculation_explanation`
3. Browser smoke ile bu alanlar goruntu veya metin olarak kanitlanmali.
