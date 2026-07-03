# Topography Devam Output Format

Kullanici `devam` veya `devam et` dediginde yanit sadece bu metrik formatinda olmalidir:

```text
Topography devam durumu:
Tamamlanan: %<overall_completion_percent>
Kalan: %<remaining_percent>
Bekleme: <wait_minutes> dakika
Doldurulan parsel: <filled_parcel_count>
Dogruluk: <accuracy_score_4>
Program entegrasyonu: %<program_integration_percent>
Web sitesi guncellemesi: %<website_update_percent>
final_ready: <true|false>
blocker: <blockers veya yok>
next_action: <tek satir>
```

`final_ready=true` sadece resmi kaynak + parsel eslesmesi + UI popup/panel + 8020 gorunum + browser smoke + runner raporu tamamlandiginda yazilabilir.
