# AAYS ChatGPT Sayfalari Devam Promptu

Asagidaki promptu yeni veya mevcut ChatGPT/Codex sayfasina ilk mesaj olarak yapistir. Sonraki mesajlarda sadece `devam et` yazabilirsin.

```text
Yerel AAYS/TerraYield projesinde bu sayfanin isine kaldigi yerden devam et.

Repo:
C:\Users\cagda\Documents\GitHub\AAYS

Branch hedefi:
main

Once su raporlari ve sozlesmeleri oku:
- docs/chatgpt_status/_shared/reports/AAYS_SINGLE_RUNNER_PANEL_ACCEPTANCE_LATEST.md
- docs/chatgpt_status/_shared/reports/single_runner_all_pages_contract_final_report_20260706.md
- docs/chatgpt_status/_shared/contracts/AAYS_SINGLE_RUNNER_PAGE_CONTRACT_20260706.md
- docs/chatgpt_status/_shared/contracts/PAGE_KEY_REGISTRY.json
- docs/chatgpt_status/_shared/panel/page_status_index_latest.json

Kurallar:
- Yeni paralel runner baslatma.
- Tek shared/canonical runner sistemini kullan.
- Queue/status/report/heartbeat/completed veya blocked kaniti olmadan completed yazma.
- Sahte final_ready=true yazma.
- Sahte %100 yazma.
- Sahte veri, source_url, source_date, browser proof veya production evidence uretme.
- allowed_paths disina cikma.
- DB write, migration, DDL veya production deploy yapma.
- GitHub/main push kaniti yoksa bunu blocker olarak yaz.
- Eksik kanit varsa basari yazma; blocker yaz ve final_ready=false birak.

Bu sayfa icin:
PAGE_KEY=<BURAYA_SAYFA_PAGE_KEY_YAZ>

Yapilacak:
1. PAGE_KEY icin docs/chatgpt_status/<PAGE_KEY>/ altindaki queue/status/reports/heartbeat/completed/blocked/runner_outputs dosyalarini oku.
2. Shared panel indexinden bu page_key durumunu oku.
3. Pending/queued task varsa sadece mevcut shared runner pickup kanitini bekle veya eksikse blocker yaz.
4. Yeni task gerekiyorsa docs/chatgpt_status/_shared/templates/NEW_CHATGPT_PAGE_QUEUE_TEMPLATE_20260706.json formatinda queue task olustur.
5. Sadece allowed_paths altinda calis.
6. Cevabinda kisa format kullan:

Bekleme: <dakika>
Tamamlanan islem: <%>
Kalan islem: <%>
Runner durumu: <status>
Final: <true/false>
Blocker: <blocker veya none>

Bundan sonraki mesajlarda "devam et" denirse ayni rapor/sozlesme/page_key baglamindan surdur.
```
