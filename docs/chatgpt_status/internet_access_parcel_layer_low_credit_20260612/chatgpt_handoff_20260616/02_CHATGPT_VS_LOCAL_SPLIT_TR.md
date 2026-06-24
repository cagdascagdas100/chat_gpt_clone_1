# Gorev Bolusumu

## ChatGPT'ye Verilecek Isler

1. Eksiklerin teknik kapanis planini cikarmak
2. `F:` veya `D:` icin final artifact klasor yapisini tarif etmek
3. Postcode-level / null-geometry paketin neden final olmadigini belgelemek
4. Parcel-ready output contract'i tamamlamak
5. Faktor breakdown schema ve popup/right-panel data contract'ini tamamlamak
6. Repo patch metni uretmek:
   - `england_map_web/app.js`
   - `england_map_web/internet_access_overlay.js`
   - `terrayield_land_intelligence/app/api/routes/map_layers.py`
   - gerekirse ek detail endpoint dosyasi
7. Final reports / diagnostics / markdown aciklamalari uretmek
8. Excel workbook schema ve gerekiyorsa workbook build instructions vermek

## Yerel PowerShell / Docker ile Yapilacak Isler

1. Agir root klasorunu `F:` veya `D:` altinda olusturmak
2. Mevcut paketin varligini dogrulamak
3. Docker/PostGIS varsa tablo import / row count kontrolu yapmak
4. Uygulamayi foreground `uvicorn` komutuyla acmak
5. ChatGPT'nin urettigi artifact'lari ilgili agir root altina koymak

## Codex'e Birakilacak Dar Isler

1. ChatGPT patch metnini repo'ya uygulamak
2. `node --check` / `py_compile` dogrulamak
3. `http://127.0.0.1:8010` smoke test yapmak
4. Son kucuk UI/backend baglama hatalarini kapatmak

## ChatGPT'ye Verilmemesi Gereken Isler

1. "tamamlandi" demek ama geometry hala null ise
2. proxy source'u final internet katmani diye sunmak
3. agir artifact'i `C:` altina yazmak
4. fake parcel polygon uretmek

