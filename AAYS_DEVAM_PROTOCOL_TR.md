# AAYS Devam Protokolu

Bu dosya ChatGPT, GitHub ve PowerShell runner arasindaki devam akisini tanimlar.

Kullanici ChatGPT icinde sadece `devam et` yazdiginda:

1. ChatGPT son `ai-results` ciktisini okur.
2. Siradaki kucuk ve dogrulanabilir gorevi belirler.
3. Yeni gorev scriptini `ai-task-scripts` altina yazar.
4. `ai-tasks/current-task.json` dosyasini yeni benzersiz gorev id ile gunceller.
5. Acik PowerShell runner bu gorevi GitHub polling ile alir.
6. Runner sadece `ai-task-scripts` altindaki PowerShell scriptini calistirir.
7. Runner sonucu `ai-results` ve `ai-heartbeat` altina yazar.
8. Sonuc GitHub'a push edilince bir sonraki `devam et` komutu bu sonucu temel alir.

Varsayilan yollar:

- BridgeRoot: C:\Users\cagda\Documents\chat_gpt_clone_1
- ProjectRoot: C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
- Project: TerraYield / aays1

Kural: gorevler kucuk, geri alinabilir ve loglanabilir olmalidir. Sonuc dosyalari her zaman `NEXT_COMMAND=devam et` satiri icermelidir.
