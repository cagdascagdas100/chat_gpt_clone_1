# Future Growth Scope Lock

## Feature Identity
- backend_internal_name: future_growth_layer
- ui_label_tr: Gelecek Gelişim
- ui_label_en: Future Growth
- layer_name: Future Urban Growth & Value Shift Layer
- calculation_version: future_growth_v1

## Scope Principle
Bu katman, parsel bazında gelecekteki kentsel büyüme ve değer kayması sinyallerini gösteren kanıt-temelli bir karar destek katmanıdır.

Bu katman kesin fiyat tahmini, yatırım tavsiyesi veya deterministik getiri projeksiyonu üretmez.

## Non-Negotiables
- [x] "Kesin fiyat tahmini değildir" metni zorunlu
- [x] calculation_version = future_growth_v1 korunacak
- [x] Kaynaksız high confidence yasak
- [x] source_url olmayan kayıt high confidence olamaz
- [x] Evidence sadece ilgili parsel için gösterilecek
- [x] Parsel popup içinde başka parsellerin evidence verisi gösterilmeyecek
- [x] Eksik veri sistemi bozmayacak, confidence düşecek
- [x] Canlı dış kaynak erişimi yoksa fixture/stub kullanılacak
- [x] Fixture/stub çıktıları production-compatible connector interface ile aynı typed shape’i koruyacak

## Delivery Boundary

### In Scope
- Source ingestion contract
- Fixture/stub data path
- Production-compatible connector interface
- Spatial matching rules
- Parcel-specific evidence selection
- Growth/value-shift scoring inputs
- Confidence downgrade rules
- API response contract
- Frontend layer visibility rules
- Popup disclaimer and evidence rendering rules
- Unit, contract, and fixture regression tests

### Out of Scope
- Kesin fiyat tahmini
- Yatırım tavsiyesi
- Al/sat/tut yönlendirmesi
- Garantili değer artışı iddiası
- Kaynaksız yüksek güven üretimi
- Parsel dışı veya komşu parsel evidence’ının ilgili parsel evidence’ı gibi gösterilmesi
- calculation_version değerinin değiştirilmesi
- Production runtime’da typed olmayan geçici veri şekilleri

## Evidence Rules
- Her evidence kaydı parsel ilişkisi kurulmadan popup’ta gösterilemez.
- Evidence kaydı mümkün olduğunda source_url taşımalıdır.
- source_url eksikse confidence high olamaz.
- Evidence spatial olarak ilgili parsel ile eşleşmiyorsa sadece genel bağlam sinyali olarak değerlendirilebilir; parsel popup evidence listesine giremez.
- Aynı evidence birden fazla parselde kullanılacaksa her parsel için ayrı spatial ilişki sonucu bulunmalıdır.

## Confidence Rules
- High confidence yalnızca kaynaklı, parsel ile ilişkili ve doğrulanabilir evidence için kullanılabilir.
- Eksik kaynak, zayıf spatial ilişki veya fixture/stub modu confidence değerini düşürür.
- Confidence skoru kesin değer tahmini gibi sunulmaz.
- Kullanıcıya gösterilen metin karar destek niteliğini korur.

## Fallback Policy If No Network
- mode: fixture/stub
- behavior: live connector yerine typed fixture/stub veri kullanılır
- requirement: API ve frontend kontratı değişmez
- requirement: source_url eksik fixture kayıtları high confidence üretemez
- requirement: testler fixture/stub path üzerinde deterministik çalışır

## Acceptance Criteria
- calculation_version response ve test fixture içinde future_growth_v1 olarak kalır.
- UI üzerinde "Kesin fiyat tahmini değildir" metni görünür.
- source_url olmayan kayıt high confidence olarak işaretlenmez.
- Popup yalnızca ilgili parsel evidence listesini gösterir.
- Dış kaynak erişimi olmadan fixture/stub path ile testler çalışır.
