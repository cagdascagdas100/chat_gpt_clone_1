# AAYS 086 Final Verify Runner
Generated: 2026-05-15T01:17:37
SLEEPWAIT_PATCHED=true
patched: C:\Users\cagda\AppData\Local\Temp\aays086_20260515_011737.ps1
CHILD_EXIT_CODE=
## child stdout tail
01 initdb trust locale C
Bu veritabanı sistemine ait olan dosyaların sahibi "cagda" kullanıcısı olacaktır.
Bu kullanıcı aynı zamanda sunucu sürecinin de sahibi olmalıdır.

Veritabanı kümesi "C" yerel ayarları ile oluşturulacak.
Öntanımlı metin arama yapılandırması "english" olarak ayarlanacak.

Veri sayfası (data page) doğrulama etkinleştirilmiştir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260515_011742 dizininin izinleri düzeltiliyor ... tamam
alt dizinler oluşturuluyor ... tamam
dinamik paylaşılan bellek (shared memory) uygulaması seçimi ... windows
selecting default "max_connections" ... 100
selecting default "shared_buffers" ... 128MB
selecting default time zone ... Europe/Istanbul
yapılandırma dosyaları yaratılıyor ... tamam
önyükleme komut dosyası çalıştırılıyor ...tamam
önyükleme sonrası başlatmayı gerçekleştirme ...tamam
veriyi diske senkronize etme ...tamam

İşlem başarılı. Veritabanı sunucusunu aşağıdaki gibi başlatabilirsiniz:

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260515^_011742^" -l logfile start


Bu veritabanı sistemine ait olan dosyaların sahibi "cagda" kullanıcısı olacaktır.
Bu kullanıcı aynı zamanda sunucu sürecinin de sahibi olmalıdır.

Veritabanı kümesi "C" yerel ayarları ile oluşturulacak.
Öntanımlı metin arama yapılandırması "english" olarak ayarlanacak.

Veri sayfası (data page) doğrulama etkinleştirilmiştir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260515_011742 dizininin izinleri düzeltiliyor ... tamam
alt dizinler oluşturuluyor ... tamam
dinamik paylaşılan bellek (shared memory) uygulaması seçimi ... windows
selecting default "max_connections" ... 100
selecting default "shared_buffers" ... 128MB
selecting default time zone ... Europe/Istanbul
yapılandırma dosyaları yaratılıyor ... tamam
önyükleme komut dosyası çalıştırılıyor ...tamam
önyükleme sonrası başlatmayı gerçekleştirme ...tamam
veriyi diske senkronize etme ...tamam

İşlem başarılı. Veritabanı sunucusunu aşağıdaki gibi başlatabilirsiniz:

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260515^_011742^" -l logfile start


03 psql version
psql (PostgreSQL) 18.3
psql (PostgreSQL) 18.3
04 connection test
 current_database | current_user |                                 version                                 
------------------+--------------+-------------------------------------------------------------------------
 postgres         | postgres     | PostgreSQL 18.3 on x86_64-windows, compiled by msvc-19.44.35225, 64-bit
(1 satır)

 current_database | current_user |                                 version                                 
------------------+--------------+-------------------------------------------------------------------------
 postgres         | postgres     | PostgreSQL 18.3 on x86_64-windows, compiled by msvc-19.44.35225, 64-bit
(1 satır)

05 create database aays
## child stderr tail
createdb.exe : createdb: hata: veritabanı yaratma başarısız oldu: ERROR:  duplicate key value violates unique constrain
t "pg_database_datname_index"
At C:\Users\cagda\AppData\Local\Temp\aays086_20260515_011737.ps1:14 char:10
+   $out = & $exe @ArgList 2>&1
+          ~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (createdb: hata:..._datname_index":String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
AAYS_086_FINAL_VERIFY_DONE=false
