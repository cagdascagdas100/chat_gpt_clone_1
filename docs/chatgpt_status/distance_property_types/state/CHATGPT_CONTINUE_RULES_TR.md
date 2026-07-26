# ChatGPT Devam Modu - Distance Property Types

Kullanici bu sayfada sadece `devam et` dediginde asagidaki is akisi uygulanacak.

## Sabitler

- Repo: cagdascagdas100/chat_gpt_clone_1
- Branch: main
- Page key: distance_property_types
- Layer: Distance to Nearby Property Types
- Aktif F repo: F:\chatgpt\chat_gpt_clone_1_main
- Bridge root: C:\AAYS_GITHUB_BRIDGE_CLEAN2
- Tek runner: korunacak, yeni runner acilmayacak

## Her devam et komutunda

1. GitHub main uzerinden son progress raporu okunur.
2. Issue #19 okunur.
3. Queue, reports, data ve runner_outputs altinda yeni kanit veya runner sonucu var mi kontrol edilir.
4. Yeni gercek kanit varsa verified/manual-review ciktilari guncellenir.
5. Yeni kanit yoksa final_ready=false korunur ve blocker rapora yazilir.
6. Sahte parcel, sahte property type, sahte kaynak, sahte fotograf AI kaniti uretilmez.
7. Local runner calisti denmez; sadece repo icinde gercek runner output varsa rapora islenir.

## Guvenlik sinirlari

fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false

## Final ready kosulu

final_ready=true ancak su kosullarda yazilabilir:

- GeoJSON parse ediliyor.
- Her feature parcel_id tasiyor.
- selected_property_type sozlesmeye uyuyor.
- accuracy_score_4 0-4 araliginda.
- 3/4 ustu satirlarda kanit var.
- sorunlu satirlar manual review dosyasinda.
- site layer aciliyor.
- Guncel degisiklikler filtresi calisiyor.
- popup veya sag panel kanitlari gosteriyor.
