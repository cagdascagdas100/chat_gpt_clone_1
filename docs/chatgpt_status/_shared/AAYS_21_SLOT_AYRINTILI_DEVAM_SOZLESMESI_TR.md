# AAYS 21 Slot Ayrıntılı Devam Sözleşmesi

Bu dosya, eski veya yeni herhangi bir ChatGPT/Codex sayfasından yalnız bir kısa paragraf ve bir `SLOT_ID` ile güvenli devam edilebilmesi için kanonik çalışma sözleşmesidir.

## 1. Kanonik hedef

- Depo: `https://github.com/cagdascagdas100/chat_gpt_clone_1`
- Kanonik çalışma branch’i: `codex/aays-single-runner-v5-20260706`
- Sözleşme/yayın branch’i: `agent/aays-21-slot-recovery-prompt-20260722`
- Workstream: `AAYS_21_SLOT_SAFE_PARALLEL_V1`
- Mantıksal slot: 21
- Donanım üst sınırı: 15 gerçek eşzamanlı görev; güvenli ve yürütülebilir görev sayısı daha azsa sayı uydurulmaz.

Bu sözleşmeye erişilemiyorsa iş yapılmış gibi davranma. `DETAILED_CONTRACT_UNAVAILABLE` bildir ve GitHub erişimini düzeltmeden business dosyası yazma.

## 2. Geçerli slot kimlikleri

`ready_to_sell_1`, `ready_to_sell_2`, `ready_to_sell_3`, `gas_emissions_1`, `gas_emissions_2`, `gas_emissions_3`, `height_difference_1`, `height_difference_2`, `height_difference_3`, `security_public_safety_1`, `security_public_safety_2`, `security_public_safety_3`, `parcel_label_1`, `parcel_label_2`, `parcel_label_3`, `internet_access_1`, `internet_access_2`, `internet_access_3`, `future_growth_1`, `future_growth_2`, `future_growth_3`.

Mesajın sonundaki değer bu listede birebir yoksa hiçbir slotu tahmin etme ve `INVALID_SLOT_ID` bildir.

## 3. İlk mesajda zorunlu okuma sırası

1. Bu sözleşmenin GitHub’daki en güncel sürümünü oku.
2. Kanonik branch’in uzak HEAD değerini al.
3. Yalnız seçili slota ait `slots_21/<slot_id>` durum, checkpoint, heartbeat, ownership ve current-task kayıtlarını oku.
4. Seçili slotun queue kayıtlarını ve varsa recovery/manual-action kaydını oku.
5. Önceki sayfanın konuşmasına güvenmek yerine GitHub kanıtlarını otorite kabul et.
6. Yerel dosya varsa yalnız yardımcı kopya olarak kullan; GitHub HEAD ve kanıtlarla uyuşmayan yerel kayıtla devam etme.

## 4. Eski ve yeni sayfaların çakışmadan birleşmesi

Her devam denemesi şu kanonik anahtarı üretir:

`continuation_key = SHA256(workstream_id | slot_id | canonical_branch | first_unverified_step | source_head)`

- Queue veya current-task içinde aynı `continuation_key` varsa yeni görev üretme; mevcut göreve bağlan.
- Canlı heartbeat ve geçerli owner lease varsa owner’ı ele geçirme, aynı business yollarına yazma ve ikinci commit üretme.
- Owner yalnız heartbeat sözleşmedeki `stale_after_seconds` değerini aşmışsa ve recovery kaydı devralmayı güvenli bulmuşsa değiştirilebilir.
- Yeni sayfa, eski sayfanın doğrulanmış checkpoint’inden devam eder; eski konuşma geçmişinin taşınması gerekmez.
- Eski sayfa tekrar `devam` derse aynı anahtarı bulur ve ikinci görev açmadan mevcut durumu izler veya ilk doğrulanmamış adımdan sürdürür.
- Her görev yalnız kendi slot köklerine ve sözleşmede açıkça verilen `exact_write_paths` yollarına yazabilir.
- Paylaşılan publisher’a çocuk sayfa doğrudan push yapmaz; çıktı child commit/publish queue üzerinden tek seri yayıncıya verilir.

## 5. Devam algoritması

1. `SLOT_ID`, workstream ve branch doğrula.
2. Uzak HEAD’i ve slot kanıtlarını oku.
3. `DONE/PUBLISHED` ve doğrulanmış kabul kanıtı varsa aynı işi tekrar çalıştırma; sıradaki ilk doğrulanmamış adıma geç.
4. `CLAIMED/RUNNING` ve heartbeat güncelse çakışan iş başlatma; gerçek ilerlemeyi raporla.
5. Yürütülebilir görev yoksa yalnız idempotent `.v3.task.json` devam kaydı oluştur; business çıktısını continuation mesajında uydurma.
6. Görevin `read_paths`, `exact_write_paths`, `resource_class`, timeout, kanıt ve kabul koşulları açık değilse görevi çalıştırma.
7. Çalışma bitince gerçek dosya/hash/satır/HTTP/DOM kanıtlarını kontrol et; yalnız test edilen sonucu yaz.
8. Commit/push yapılmadıysa yapılmış gibi söyleme. Commit SHA ve uzak readback yoksa durum `PUBLISH_PENDING` kalır.

## 6. BLOCKED ve uzun PENDING kurtarma kapısı

Normal işten önce aşağıdaki kapı uygulanır:

- `BLOCKED`, `STALE` veya heartbeat süresi aşmış aktif görev: hemen teşhis planı oluştur.
- `PENDING/QUEUED/PUBLISH_PENDING`: 15 dakika boyunca ilerleme yoksa veya üç yayın denemesi aynı hatayla biterse takılı kabul et.
- Önce süreç/owner/heartbeat, Git lock yaşı, worktree temizliği, uzak HEAD, kaynak erişimi ve disk/bellek durumunu kaydet.
- Aktif Git işlemi yoksa yalnız boş ve yaşlanmış `index.lock`, `sparse-checkout.lock` veya `shallow.lock` kaldırılabilir.
- Temiz yerel HEAD doğrulanırsa timeout için yalnız bir güvenli tekrar yapılabilir.
- Kirli worktree korunur; gerekirse izole recovery worktree kullanılır. Kullanıcı verisi silinmez, `reset --hard` yapılmaz.
- Gerçek kaynak/çıktı yoksa veri uydurma ve kullanıcıdan kaynak isteme; Bölüm 6.1'deki otomatik kaynak keşfi/kanıtlı `NO_DATA_CONTINUE` yolunu uygula.
- Aynı onarım bir kez başarısız olursa sonsuz döngü yapma; `RECOVERY_PARKED` ve gerçek nedeni yaz.
- Problem çözülmeden normal business adımına dönme. Çözülünce aynı `continuation_key` ile checkpoint’ten devam et.

### 6.1. Gerçek veri ve ücretsiz kaynak politikası

- Kullanıcı AAYS görevleri için dosya, e-posta, hesap, ücretli abonelik, FOI/bilgi edinme başvurusu veya manuel kaynak sağlamayacaktır; bunları isteme ve kullanıcı eylemi olarak kaydetme.
- Kaynak sırası zorunludur: önce repo/taşınabilir disk/önceki kanıt ve indirilen dosyalar, sonra kimlik doğrulama istemeyen ücretsiz ve herkese açık internet kaynakları. Mümkün olduğunda resmî kamu/veri sağlayıcı kaynağını tercih et; URL, erişim zamanı, lisans/atıf ve hash kanıtını yaz.
- Üyelik, ödeme, e-posta doğrulaması, CAPTCHA veya kişisel bilgi isteyen kaynak atlanır; bu durum slotu bloklamaz.
- Kaynak keşfi sınırlı ve idempotent yapılır. Aynı URL/hata sonsuza kadar denenmez; erişim ve sonuç kanıtı checkpoint'e yazılır.
- Uygun gerçek veri bulunursa normal doğrulama ve üretim adımına devam et. Bulunamazsa değer uydurma veya çıkarım yapma; ilgili kapsamı kanıtlı `NO_DATA` olarak kaydet, görev durumunu `NO_DATA_CONTINUE` yap ve aynı slotun sonraki ilk doğrulanmamış işine geç.
- `SOURCE_NOT_FOUND`, `SOURCE_READ_FAILED`, `EXPORT_NOT_STARTED`, `FEATURE_COUNT_ZERO`, `NO_NATIONAL_ENGLAND_CANONICAL_PARCEL_INVENTORY` ve benzeri veri-yokluğu durumları tek başına `RECOVERY_PARKED` veya manuel kullanıcı eylemi değildir.
- Teknik bir problem (Git yetkisi, bozuk dosya, disk hatası, çalışmayan resmi URL istemcisi) kaynak keşfinin kendisini engelliyorsa yalnız teknik problem kurtarma kapısına alınır; kullanıcıdan veri istenmez.

### 6.2. `parcel_building_type_classification_v1` devam fazı

`parcel_label_1`, `parcel_label_2` ve `parcel_label_3` slotları için yeni bina türü sınıflandırma fazı yalnız ayrı queue task üzerinden başlatılır:

- Faz kimliği: `parcel_building_type_classification_v1`.
- İlk doğrulanmamış adım: `START_PARCEL_BUILDING_TYPE_CLASSIFICATION_V1_FROM_CANONICAL_PARCEL_LABEL_OUTPUTS`.
- Bu faz, eski `distance_property_types` çalışmalarını yalnız tarihsel/pilot kanıt olarak okuyabilir; `distance_property_types` çıktısı tek başına kanonik `selected_property_type` ya da bina türü kararı değildir.
- `selected_property_type`, `building_type_classification`, `property_type_source`, `confidence` veya benzeri alanlar yalnız gerçek kaynak, mevcut kanıt dosyası, hash ve kabul koşullarıyla yazılır. Tahmin, placeholder, varsayılan değer veya görsel benzerlikten sınıflandırma yapılmaz.
- Her slot kendi partition sınırı içinde kalır: `parcel_label_1` 1-30761, `parcel_label_2` 30762-61522, `parcel_label_3` 61523-92283.
- Yeni faz task'ları `docs/chatgpt_status/aays1/queue/0000_030_parcel_label_<n>_parcel_building_type_classification_v1_20260808.task.json` dosyalarından başlatılır.
- Kabul için en azından slot current-task/status/checkpoint, canonical parcel label çıktıları, varsa `england_map_web/data/distance_property_types/parcel_label_<n>_*` pilot çıktıları ve yeni faz runner output hash readback'i doğrulanır.
- Büyük ham veri, DB write, migration, production deploy, legal boundary claim, address/UPRN inference ve fake data yasaktır.
- DeepSeek/opencode kullanılıyorsa geniş repo taraması veya paralel ajan başlatılmaz; yalnız prompt-önce `--file` ekli dar komut ya da `F:\OpenCode_Manager_Factory\Run_DeepSeek_AAYS_Parcel_Building_Type_Verify.cmd` kullanılır. Süreç takılırsa yeni ajan açılmaz, ilgili opencode süreci kapatılır ve timeout blocker yazılır.

## 7. Manuel eylem kayıt sözleşmesi

Otomatik çözüm mümkün değilse şu dosyayı oluştur veya güncelle:

`docs/chatgpt_status/_shared/manual_actions/<slot_id>.json`

Zorunlu alanlar:

```json
{
  "schema_version": 1,
  "slot_id": "<slot_id>",
  "state": "OPEN",
  "requires_user_action": true,
  "reason": "Gerçek ve güncel problem nedeni",
  "detected_at": "UTC ISO-8601",
  "updated_at": "UTC ISO-8601",
  "solution": "Kullanıcının yapacağı somut ve kısa işlem",
  "evidence_paths": [],
  "continuation_key": "...",
  "final_ready": false
}
```

- Otomatik kurtarma sürüyorsa bu kayıt oluşturulmaz.
- Yalnız kaynak/veri eksikliği için manuel kayıt oluşturulmaz; Bölüm 6.1 uygulanır.
- Kullanıcı işlemi gerçekten gerekliyse kayıt görünür ve Python panelindeki `Çözülmemiş Kullanıcı İşlemleri` tablosuna yansır.
- Sorun doğrulanarak çözülünce `state` değeri `RESOLVED`, `requires_user_action` değeri `false` yapılır. Panel sonraki yenilemede satırı otomatik kaldırır.
- Sadece güncel çözülmemiş işlem tutulur; eski veya çözülmüş hata tekrar gösterilmez.

## 8. GitHub ve yayın güvenliği

- Başlamadan `gh auth status` veya eşdeğer uzak erişim doğrulaması yap.
- Her çalışma ve her push denemesinden önce uzak branch'i `fetch` et; yalnız güncel uzak HEAD üzerine ilerle.
- Başka slotların değişikliklerini stage/commit etme.
- Karışık worktree’de `git add -A` kullanma; yalnız bu slotun doğrulanmış yollarını stage et.
- Non-fast-forward durumunda en fazla 5 sınırlı `fetch -> merge -> test -> push` denemesi yap; `force push`, `reset --hard` ve geçmiş silme kullanma.
- Bir çatışmayı otomatik çözebilmek için çatışan bütün yollar bu görevin `exact_write_paths`/slot kanıt yolları içinde olmalıdır. Başka slota ait tek bir yol varsa merge'i iptal et, ilgili owner'ın yayınını bekle ve yeniden dene; başka slotun çıktısını silme.
- Aynı üretilmiş JSON/TXT/MD kaydı yalnız zaman damgasında ayrılıyorsa içerikleri zaman damgaları çıkarılmış halde eşitlik kontrolünden geçir ve en yeni geçerli kaydı seç. İçerik de farklıysa körlemesine `ours/theirs` seçme.
- Kod, şema veya farklı iş kanıtları aynı satırlarda değişmişse seçili slot owner'ı iki tarafın işlevini birleştirir; conflict marker taraması, sözdizimi ve ilgili testler geçmeden commit/push yapmaz.
- Ortak koordinatör/publisher dosyalarını yalnız seri publisher çözer. Child sayfa ortak branch'e doğrudan merge/push yapmaz.
- Aynı çatışma yeniden görülürse slot, yol ve üç Git nesnesinden kararlı bir çatışma anahtarı üret; aynı çözümü/testi idempotent uygula ve ikinci bir görev/commit üretme.
- Push sonrası uzak branch SHA readback ile yerel SHA eşleşmeden `PUBLISHED` yazma.
- Ayrıntılı sözleşme değişikliği ayrı branch ve taslak PR ile yayımlanır.

## 9. İlk cevap ve bitiş raporu

İlk cevapta kısa olarak şunları yaz:

- Okunan sözleşme sürümü/branch’i.
- Seçili slot ve bulunan `continuation_key`.
- Gerçek durum: aktif, bekliyor, blocked, recovery veya devam edilecek ilk adım.
- Çakışan canlı owner olup olmadığı.

Bitişte şunları ayır:

- Gerçekten yapılanlar.
- Yapılmayanlar.
- Oluşturulan/değiştirilen yollar.
- Test/kanıt sonucu.
- Commit/push/uzak readback durumu.
- Kalan blocker veya manuel eylem.

`final_ready` yalnız iş, test, commit/push ve uzak readback gerçekten tamamlandıysa `true` olabilir.
