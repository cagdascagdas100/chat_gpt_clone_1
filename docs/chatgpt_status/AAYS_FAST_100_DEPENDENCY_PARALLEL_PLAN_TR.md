# AAYS Fast 100 Plan

Bu plan kalan isleri tek ana runner icinde hizlandirmak icindir.

## Calisma modeli
- Tek ana runner korunur.
- Bagimsiz denetimler child job olarak paralel calisir.
- Bagimli isler sirali calisir.
- Database yazimi kapali kalir.
- Production deploy kapali kalir.
- Fake veri uretilmez.

## Bagimli zincir
1. current-task, last-task ve heartbeat senkronu kontrol edilir.
2. Gerekli script dosyalari var mi kontrol edilir.
3. Onceki gap audit ciktilari okunur.
4. Final kanit raporu uretilir.
5. Status/dashboard icin yalnizca ilgili sayfa satiri onerilir.

## Paralel calisacak bagimsiz isler
- Dosya envanteri.
- Guvenlik bayraklari denetimi.
- Estate coverage, scoring, export ve join sozlesmeleri.
- Internet score lineage ve dashboard stale kontrolu.
- Codex handoff paket kontrolu.

## Basari kriteri
- Final raporu ai-results altinda yazilir.
- Heartbeat final gorevi gosterir.
- Dis veri eksigi varsa blocker olarak acikca yazilir.
- Tek runner kurali bozulmaz.

## Uygulama
Yeni hizlandirici gorev: aays-fast-100-dependency-parallel-20260523-r1
