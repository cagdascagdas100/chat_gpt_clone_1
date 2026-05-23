# 13 Internet / Estate Final 100 Dependency Execution Plan

Durum: Teknik paralel kapanis tamamlandi. Gercek uretim 100 icin dis veri ve acik onay gerektiren blokajlar kaldi.

## Mevcut kanit
- current-task ve last-task: estate-parallel-close-20260523-r1
- heartbeat: finished, exit=0
- rapor: ai-results/estate_remaining_parallel_close_20260523.report.md
- teknik task completion: 100/100
- plan progress: 92

## Bagimli isler
Bu isler sirali ilerlemelidir:
1. Dogrulanmis estate-agent source rows alinacak.
2. Gercek TerraYield parcel master/export alinacak.
3. Estate agent coverage ile parcel_group_id eslestirme dogrulanacak.
4. Kullanici DB write icin acik onay verirse migration/import planlanacak.
5. Kullanici production deploy icin acik onay verirse deploy gate acilacak.

## Ayni anda calisabilecek bagimsiz isler
Bu isler tek ana runner icinde child job olarak paralel calisabilir:
- Kaynak veri dosya formati kontrolu.
- Parcel master kolon kontrolu.
- Estate agent kolon kontrolu.
- Duplicate ve bos alan kontrolu.
- Coverage/scoring/join raporlari kontrolu.
- Dashboard/status sync kontrolu.

## En hizli ve en guvenilir yol
1. Simdilik DB write=false, production_deploy=false, fake_data=false korunur.
2. Dis veri gelene kadar otomatik 100 yapilmaz; 92 gercek guvenli seviyedir.
3. Kullanici iki dosyayi verdiginde tek runner icinde paralel validator calistirilir:
   - verified estate-agent rows
   - TerraYield parcel master/export
4. Validator temiz cikarsa import/migration icin ayri onay istenir.

## Kapanis kriteri
Gercek 100 icin sunlar gerekir:
- verified estate-agent rows var ve valid
- parcel master/export var ve valid
- join coverage raporu valid
- DB write onayi varsa migration dry-run pass
- production deploy onayi varsa smoke test pass

## Kullanici kesin mudahalesi gereken nokta
Dosyalar kullanicida ise sisteme yerlestirilmeli veya yolu belirtilmeli. Dosyalar yoksa fake veriyle 100'e tamamlanmayacak.
