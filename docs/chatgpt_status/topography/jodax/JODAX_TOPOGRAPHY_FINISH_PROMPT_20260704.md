# JodaX Topography Finish Prompt

Sen yerel Windows bilgisayara erisebilen JodaX/Codex ajanisin. Bu isi kullanicinin bilgisayarinda bitir. Hedef: TerraYield AAYS Topography katmaninda tek runner akisini kesin calisir hale getir, program ve 8020 site ciktilarini guncelle, sahte veri uretmeden final_ready kuralina gore sonucu yaz.

## Sabitler

- Repo: cagdascagdas100/chat_gpt_clone_1
- Branch: main
- Local repo root: F:\chatgpt\chat_gpt_clone_1_main
- Page key: topography
- Layer: Topography
- Tek runner ilkesi: once mevcut runner/PowerShell sureci ve heartbeat kontrol et. Aktif ve saglikli runner varsa yeni runner baslatma. Runner yoksa veya stale ise sadece bir tane runner/bridge baslat.

## Ilk calistirilacak tek komut

PowerShell'de su bootstrap'i calistir:

```powershell
$u="https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/main/docs/chatgpt_status/topography/automation/START_TOPOGRAPHY_AUTOFIX_FROM_ANYWHERE_20260704.ps1"; $p="$env:TEMP\START_TOPOGRAPHY_AUTOFIX_FROM_ANYWHERE_20260704.ps1"; Invoke-WebRequest -UseBasicParsing $u -OutFile $p; powershell -NoProfile -ExecutionPolicy Bypass -File $p
```

Bu komut repo yoksa clone eder, varsa main'i ceker, F disk disindaki repo rootlarini reddeder, Topography bridge'i calistirir, smoke check'i dener ve status dosyasini yazar.

## Zorunlu okunacak dosyalar

1. docs/chatgpt_status/topography/current_task/topography_current_task_20260703.json
2. docs/chatgpt_status/topography/schemas/topography_site_update_schema_20260703.json
3. england_map_web/data/program_layer_matrix/topography.geojson
4. docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT
5. docs/chatgpt_status/topography/fixtures/topography_verified_rows_template_20260703.csv
6. docs/chatgpt_status/topography/automation/topography_single_runner_bridge_20260703.ps1
7. outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json
8. docs/chatgpt_status/topography/status/topography_current_status_20260703.txt
9. docs/chatgpt_status/topography/reports/topography_progress_latest_20260703.md

## Zorunlu isler

1. F:\chatgpt\chat_gpt_clone_1_main altinda calis. C veya baska disk kullanma.
2. Git sync yap: stash gerekirse stashle, fetch, checkout main, pull --ff-only.
3. Aktif runner durumunu kontrol et. Kopya runner baslatma. Yoksa sadece Topography icin tek bridge/runner calistir.
4. CSV sablonunda su alanlar eksiksiz olsun: parcel_id, parcel_ref, elevation_sea_level_m, regional_average_elevation_m, elevation_difference_regional_average_m, elevation_class, color_category, confidence_rating, confidence_percent, source, source_url, source_date, matching_method, calculation_explanation, accuracy_score_4, needs_manual_review, changed_in_latest_run.
5. Sahte parsel veya sahte evidence uretme. Gercek verified satir yoksa 0 parsel ve final_ready=false kalacak.
6. Resmi kaynakli satir varsa bridge'i calistir ve topography.geojson ile latest_changes.json dosyalarini guncelle.
7. 8010 ana app ve 8020 kontrol sitesi aciksa browser smoke calistir. Acik degilse blocker yaz.
8. Son durumda su dosyalari mutlaka yaz/kontrol et:
   - outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json
   - docs/chatgpt_status/topography/reports/topography_progress_latest_20260703.md
   - docs/chatgpt_status/topography/status/topography_current_status_20260703.txt
   - docs/chatgpt_status/topography/logs/topography_autofix_latest_20260704.log

## Final kabul kurali

final_ready=true sadece su kosullarda yazilabilir:

- En az bir gercek kaynakli Topography parsel satiri var.
- elevation_sea_level_m ve elevation_difference_regional_average_m dolu.
- source, source_url, source_date, confidence, matching_method, calculation_explanation dolu.
- topography.geojson ilgili parcel properties alanlarini tasiyor.
- 8020 Topography - Guncel Degisiklikler panelinde latest_changes.json gorunuyor.
- 8010 ana uygulamada parcel secilince Topography/elevation paneli veya popup gorunuyor.
- Browser smoke ve runner raporu var.

Eksik varsa final_ready=false, blockers ve next_action net yaz.

## Kullaniciya donulecek tek format

```text
Topography devam durumu:
Tamamlanan: %<completion>
Kalan: %<remaining>
Bekleme: <minutes> dakika
Doldurulan parsel: <count>
Dogruluk: <score>/4
Program entegrasyonu: %<program>
Web sitesi guncellemesi: %<site>
final_ready: <true|false>
blocker: <blocker listesi veya yok>
next_action: <tek satir>
```

## Hedef

Oncelik hiz: tek bootstrap ile runner/bridge calissin. Sonra veri/smoke eksikse sadece eksigi yaz. Kesinlikle sahte %100, sahte FINAL_READY, sahte parsel verisi veya sahte smoke uretme.
