Gas Emissions Final Acceptance Checklist

Bu maddeler kapanmadan `FINAL_READY` deme:

1. Layer `air.png` ile aciliyor.
2. Layer tekrar tiklaninca kapaniyor.
3. Buton aktif/inactive state veriyor.
4. Legend gorunuyor.
5. Legend scale dogru:
   - 0-20 Very Low
   - 21-40 Low
   - 41-60 Medium
   - 61-80 High
   - 81-100 Very High
   - No Data
6. Runtime point-source degil parcel thematic output veriyor.
7. Veri olmayan parcel'lar thematic davranisi bozmuyor.
8. Parcel tiklaninca popup veya sag panelde su alanlar dolu:
   - emission_percent
   - emission_level
   - emission_color_hex
   - confidence label/value
   - source_type
   - source/evidence
   - source_date
   - matching_method
   - calculation_explanation
9. Browser smoke ile en az bir parcel icin non-empty proof var.
10. Performans bozucu yeni broad polling veya tam sayfa refetch eklenmemis.

Bitmis saymak icin minimum kanit

1. Browser screenshot veya popup text
2. Runtime state
3. Legend text
4. Tiklanan parcelde dolu gas alanlari
