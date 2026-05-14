# AAYS 086 Final Verify Runner
Generated: 2026-05-15T01:24:56
SLEEPWAIT_PATCHED=true
patched: C:\Users\cagda\AppData\Local\Temp\aays086_20260515_012456.ps1
CHILD_EXIT_CODE=
## child stdout tail
01 initdb trust locale C
Bu veritabanı sistemine ait olan dosyaların sahibi "cagda" kullanıcısı olacaktır.
Bu kullanıcı aynı zamanda sunucu sürecinin de sahibi olmalıdır.

Veritabanı kümesi "C" yerel ayarları ile oluşturulacak.
Öntanımlı metin arama yapılandırması "english" olarak ayarlanacak.

Veri sayfası (data page) doğrulama etkinleştirilmiştir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260515_012500 dizininin izinleri düzeltiliyor ... tamam
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

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260515^_012500^" -l logfile start


Bu veritabanı sistemine ait olan dosyaların sahibi "cagda" kullanıcısı olacaktır.
Bu kullanıcı aynı zamanda sunucu sürecinin de sahibi olmalıdır.

Veritabanı kümesi "C" yerel ayarları ile oluşturulacak.
Öntanımlı metin arama yapılandırması "english" olarak ayarlanacak.

Veri sayfası (data page) doğrulama etkinleştirilmiştir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260515_012500 dizininin izinleri düzeltiliyor ... tamam
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

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260515^_012500^" -l logfile start


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
06 apply schema
CREATE SCHEMA
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE SCHEMA
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
07 truncate staging
TRUNCATE TABLE
TRUNCATE TABLE
08 import csv
COPY 120
COPY 120
09 count staging rows
 staging_rows 
--------------
          120
(1 satır)

 staging_rows 
--------------
          120
(1 satır)

10 count verified polygon non-empty
 verified_polygon_non_empty 
----------------------------
                          0
(1 satır)

 verified_polygon_non_empty 
----------------------------
                          0
(1 satır)

11 geometry verdict distribution
   geometry_verdict   | count 
----------------------+-------
 derived_ai_visual    |    99
 derived_signal       |    19
 derived_multi_signal |     2
(3 satır)

   geometry_verdict   | count 
----------------------+-------
 derived_ai_visual    |    99
 derived_signal       |    19
 derived_multi_signal |     2
(3 satır)

TERRAYIELD_TASK_DONE report=C:\Users\cagda\AppData\Local\ai-results\aays-056-db-dryrun-no-pgctl-20260515_012500.md port=5443
## child stderr tail
AAYS_086_FINAL_VERIFY_DONE=false
