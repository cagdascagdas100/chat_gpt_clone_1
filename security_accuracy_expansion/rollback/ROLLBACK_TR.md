# Rollback

Bu genisletme asamasinda canli `Guvenlik` ve `Dusuk Review` modullerine dokunulmadigi icin rollback yalindir.

## PASS Sonrasi

- `england_map_web` altinda hash degisikligi yoksa rollback gerekmez.
- `security_accuracy_expansion` yalnizca plan/kanit klasoru oldugu icin istenirse tamamen silinebilir.

## FAIL Sonrasi

1. Once canli dosyalarin hash'ini kontrol et:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1"
```

2. Eger `OVERALL=FAIL` donerse, `england_map_web` altinda istenmeyen degisiklik yapildi demektir. Bu plan asamasinda beklenen durum degildir. Bu durumda ChatGPT veya lokal script ciktisini durdur.

3. Sadece bu altyapiyi kaldirmak icin:

```powershell
Remove-Item "C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion" -Recurse -Force
```

## Not

Bu rollback yalnizca `security_accuracy_expansion` klasorunu kaldirir. Canli overlay dosyalari bu klasorun disindadir ve bu plan asamasinda degistirilmemelidir.
