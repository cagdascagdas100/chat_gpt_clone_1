# AAYS / TerraYield Tek Runner Queue-Lock Plani

Amaç: Birden fazla ChatGPT sayfasinin ayni `ai-tasks/current-task.json` dosyasini ezmesini engellemek ve tek PowerShell runner ile isleri karismadan hizlandirmak.

## Ana karar

Birden fazla PowerShell runner acilmayacak. Tek ana runner calisacak. ChatGPT sayfalari dogrudan `current-task.json` ezmek yerine kendi isteklerini queue dosyalarina yazacak.

## Dosya yapisi

```text
ai-queue/pending/*.json
ai-queue/running/*.json
ai-queue/done/*.json
ai-queue/failed/*.json
ai-locks/runner.lock.json
ai-heartbeat/portable-runner.md
docs/chatgpt_status/multi_page_status.json
```

## Sayfa kurali

Her sayfa yalniz kendi `page_key` alanini gunceller. Baska sayfanin satiri silinmez veya ezilmez.

Her sayfa yeni is istediginde:

1. `ai-tasks/current-task.json` okumali.
2. `ai-tasks/.last-task-id` okumali.
3. `ai-heartbeat/portable-runner.md` okumali.
4. Eger aktif is varsa kendi taskini `ai-queue/pending/<page_key>_<task_id>.json` olarak eklemeli.
5. `current-task.json` yalniz runner bos ise veya lock izin verirse guncellenmeli.
6. DB write kapali kalmali.
7. Production deploy kapali kalmali.
8. Fake veri uretilmemeli.

## Runner kurali

Tek runner su sekilde davranmali:

1. `ai-locks/runner.lock.json` yoksa lock al.
2. `ai-tasks/current-task.json` icinde is varsa once onu calistir.
3. Is bitince `ai-queue/pending` icinden en eski isi al.
4. Isi `running` klasorune tasi.
5. Calistir.
6. Sonucu `done` veya `failed` klasorune tasi.
7. Heartbeat yaz.
8. Lock'u yenile.

## Hizlandirma kurali

Paralel is sadece dosya okuma, rapor hazirlama, manifest uretme gibi read-only alt islemlerde yapilabilir. Ayni anda Git push, ortak JSON update, DB write, migration, production deploy yapilmaz.

## Diger ChatGPT sayfalarina verilecek kisa talimat

Bu sayfada bundan sonra `current-task.json` dosyasini dogrudan ezme. Tek runner queue-lock protokolunu kullan. Aktif is varsa kendi taskini `ai-queue/pending` altina ekle. Sadece kendi sayfa status satirini guncelle. DB write false, production_deploy false kalsin. Kullanici sadece `devam et` yazabilsin.

## Beklenen sonuc

- Runner karismasi azalir.
- ChatGPT sayfalari birbirinin taskini ezmez.
- Tek runner sirali ama kontrollu calisir.
- Uzun isler 30-45 dakika surecek sekilde queue'ya alinir.
- Site status verisi eski kalmaz.
