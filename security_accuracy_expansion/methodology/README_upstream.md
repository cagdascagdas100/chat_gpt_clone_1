# Terrayield / AAYS Güvenlik Doğruluğu Genişletme Paketi

Bu ZIP, Codex'e verilecek güvenlik veri güvenilirliği genişletme çalışması için hazırlanmıştır.

Amaç: Terrayield/AAYS uygulamasında topografik veya harita sayfası açıldığında, İngiltere kapsamındaki kayıtlı parseller için polis/asayiş açısından güvenlik bilgisini daha kanıtlı ve izlenebilir şekilde göstermek.

Önemli sınır: Bu plan “mutlak kesin güvenlik” iddiası kurmaz. Resmî suç verileri, LSOA/posta kodu/UPRN/parsel eşlemesi ve veri tazeliği kontrolleriyle kanıta dayalı güvenilirlik üretir. Kanıt yetersizse kayıt review/manual inceleme durumunda kalır.

Klasörler:
- `prompts/`: Codex'e atılacak ana prompt ve kısa prompt.
- `source_catalog/`: önerilen resmî/kamu kaynak kataloğu.
- `codex_tasks/`: 047/048/049 görev taslakları.
- `evidence_templates/`: ChatGPT'ye doldurtulacak kanıt dosyası şablonları.
- `schemas/`: çıktı şemaları.
- `frontend/`: uygulama entegrasyon taslağı.
- `qa/`: test/kanıt/kalite kontrol şablonları.

Mevcut güvenlik modülü durumu:
- Security features: 92.283
- Review features: 242
- Accuracy: Cok Yuksek 91.730, Yuksek 139, Orta 172, Dusuk 242
- Bad score range: 0
- Missing core fields: 0
- Plan progress: 100%

Codex'e önerilen işlem: Veri üretimini hemen değiştirme. Önce kaynak katalogları ve kanıt şablonlarını üret, sonra preflight/audit, sonra kaynak bazlı genişletme planını uygula.
