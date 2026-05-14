# AAYS Autopilot Supervisor Result

TaskId: aays-053-auto-clean-cluster-db-dryrun-20260514-pgctl-guard-1450
ExitCode: 124
Time: 2026-05-14T15:19:53

## STDOUT
```text
01 initdb trust locale C
Bu veritaban� sistemine ait olan dosyalar�n sahibi "cagda" kullan�c�s� olacakt�r.
Bu kullan�c� ayn� zamanda sunucu s�recinin de sahibi olmal�d�r.

Veritaban� k�mesi "C" yerel ayarlar� ile olu�turulacak.
�ntan�ml� metin arama yap�land�rmas� "english" olarak ayarlanacak.

Veri sayfas� (data page) do�rulama etkinle�tirilmi�tir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260514_150455 dizininin izinleri d�zeltiliyor ... tamam
alt dizinler olu�turuluyor ... tamam
dinamik payla��lan bellek (shared memory) uygulamas� se�imi ... windows
selecting default "max_connections" ... 100
selecting default "shared_buffers" ... 128MB
selecting default time zone ... Europe/Istanbul
yap�land�rma dosyalar� yarat�l�yor ... tamam
�ny�kleme komut dosyas� �al��t�r�l�yor ...tamam
�ny�kleme sonras� ba�latmay� ger�ekle�tirme ...tamam
veriyi diske senkronize etme ...tamam

��lem ba�ar�l�. Veritaban� sunucusunu a�a��daki gibi ba�latabilirsiniz:

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260514^_150455^" -l logfile start


Bu veritaban� sistemine ait olan dosyalar�n sahibi "cagda" kullan�c�s� olacakt�r.
Bu kullan�c� ayn� zamanda sunucu s�recinin de sahibi olmal�d�r.

Veritaban� k�mesi "C" yerel ayarlar� ile olu�turulacak.
�ntan�ml� metin arama yap�land�rmas� "english" olarak ayarlanacak.

Veri sayfas� (data page) do�rulama etkinle�tirilmi�tir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260514_150455 dizininin izinleri d�zeltiliyor ... tamam
alt dizinler olu�turuluyor ... tamam
dinamik payla��lan bellek (shared memory) uygulamas� se�imi ... windows
selecting default "max_connections" ... 100
selecting default "shared_buffers" ... 128MB
selecting default time zone ... Europe/Istanbul
yap�land�rma dosyalar� yarat�l�yor ... tamam
�ny�kleme komut dosyas� �al��t�r�l�yor ...tamam
�ny�kleme sonras� ba�latmay� ger�ekle�tirme ...tamam
veriyi diske senkronize etme ...tamam

��lem ba�ar�l�. Veritaban� sunucusunu a�a��daki gibi ba�latabilirsiniz:

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260514^_150455^" -l logfile start


02 start cluster local only wait max 20s

```

## STDERR
```text
```
