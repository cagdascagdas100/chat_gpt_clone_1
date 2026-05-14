# AAYS Direct Autopilot Result

TaskId: aays-056-db-dryrun-no-pgctl-20260514-1715
Script: aays_056_db_dryrun_no_pgctl_20260514.ps1
ExitCode: 
Time: 2026-05-14T18:01:37

## STDOUT
```text
01 initdb trust locale C
Bu veritaban� sistemine ait olan dosyalar�n sahibi "cagda" kullan�c�s� olacakt�r.
Bu kullan�c� ayn� zamanda sunucu s�recinin de sahibi olmal�d�r.

Veritaban� k�mesi "C" yerel ayarlar� ile olu�turulacak.
�ntan�ml� metin arama yap�land�rmas� "english" olarak ayarlanacak.

Veri sayfas� (data page) do�rulama etkinle�tirilmi�tir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260514_175928 dizininin izinleri d�zeltiliyor ... tamam
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

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260514^_175928^" -l logfile start


Bu veritaban� sistemine ait olan dosyalar�n sahibi "cagda" kullan�c�s� olacakt�r.
Bu kullan�c� ayn� zamanda sunucu s�recinin de sahibi olmal�d�r.

Veritaban� k�mesi "C" yerel ayarlar� ile olu�turulacak.
�ntan�ml� metin arama yap�land�rmas� "english" olarak ayarlanacak.

Veri sayfas� (data page) do�rulama etkinle�tirilmi�tir.

mevcut E:/AAYS_DATA/postgresql18_aays_auto_cluster_20260514_175928 dizininin izinleri d�zeltiliyor ... tamam
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

   ^"C^:^\Program^ Files^\PostgreSQL^\18^\bin^\pg^_ctl^" -D ^"E^:^\AAYS^_DATA^\postgresql18^_aays^_auto^_cluster^_20260514^_175928^" -l logfile start



```

## STDERR
```text
Start-Process : This command cannot be run because "RedirectStandardOutput" and "RedirectStandardError" are same. Give 
different inputs and Run your command again.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_056_db_dryrun_no_pgctl_20260514.ps1:56 char:9
+ $proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -Redi ...
+         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (:) [Start-Process], InvalidOperationException
    + FullyQualifiedErrorId : InvalidOperationException,Microsoft.PowerShell.Commands.StartProcessCommand
 

```
