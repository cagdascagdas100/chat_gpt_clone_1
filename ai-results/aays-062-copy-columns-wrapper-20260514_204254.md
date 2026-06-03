# AAYS 062 Wrapper for AAYS 056 Copy Columns Fix
Generated: 2026-05-14T20:42:54
REDIRECT_PATCHED=true
COPY_COLUMNS_PATCHED=true
patched: C:\Users\cagda\AppData\Local\Temp\aays_056_copy_columns_20260514_204254.ps1
CHILD_EXIT_CODE=
## child stdout tail
01 initdb trust locale C
Bu veritabanı sistemine ait olan dosyaların sahibi "cagda" kullanıcısı olacaktır.
Bu kullanıcı aynı zamanda sunucu sürecinin de sahibi olmalıdır.

Veritabanı kümesi "C" yerel ayarları ile oluşturulacak.
Öntanımlı metin arama yapılandırması "english" olarak ayarlanacak.

Veri sayfası (data page) doğrulama etkinleştirilmiştir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260514_204257 dizininin izinleri düzeltiliyor ... tamam
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

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260514^_204257^" -l logfile start


Bu veritabanı sistemine ait olan dosyaların sahibi "cagda" kullanıcısı olacaktır.
Bu kullanıcı aynı zamanda sunucu sürecinin de sahibi olmalıdır.

Veritabanı kümesi "C" yerel ayarları ile oluşturulacak.
Öntanımlı metin arama yapılandırması "english" olarak ayarlanacak.

Veri sayfası (data page) doğrulama etkinleştirilmiştir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260514_204257 dizininin izinleri düzeltiliyor ... tamam
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

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260514^_204257^" -l logfile start


## child stderr tail
psql.exe : psql: hata (error): connection to server at "127.0.0.1", port 5435 failed: FATAL:  the database system is st
arting up
At C:\Users\cagda\AppData\Local\Temp\aays_056_copy_columns_20260514_204254.ps1:64 char:14
+ ...    $probe = & $Psql -h 127.0.0.1 -p "$Port" -U postgres -d postgres - ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (psql: hata (err... is starting up:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
AAYS_062_WRAPPER_DONE=false
