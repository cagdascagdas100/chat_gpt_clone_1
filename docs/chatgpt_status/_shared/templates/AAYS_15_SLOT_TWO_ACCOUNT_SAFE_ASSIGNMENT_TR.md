# AAYS 15 Slot - İki Hesap İçin Güvenli Örnek Dağılım

Bu dağılım zorunlu değildir; amaç aynı SLOT_ID'nin iki sayfada açılmasını önlemektir. Her hesap repo/branch erişimine sahip olmalı ve her sayfa yalnız kendi SLOT_ID yollarına yazmalıdır.

## Hesap A - 8 sayfa
- ready_to_sell_1
- ready_to_sell_2
- ready_to_sell_3
- gas_emissions_1
- gas_emissions_2
- gas_emissions_3
- height_difference_1
- height_difference_2

## Hesap B - 7 sayfa
- height_difference_3
- security_public_safety_1
- security_public_safety_2
- security_public_safety_3
- parcel_label_1
- parcel_label_2
- parcel_label_3

Kurallar:
- Aynı SLOT_ID aynı anda iki ChatGPT sayfasına verilmez.
- Yeni sayfa, ortak promptta yalnız kendi SLOT_ID değerini kullanır.
- Her `devam et` öncesinde remote branch HEAD ve slot checkpoint yeniden okunur.
- Non-fast-forward/çakışmada shared dosya zorlanmaz; güncel HEAD okunup yalnız kendi slot değişikliği yeniden uygulanır.
- İki hesap kullanımı platform kurallarını aşma amacı taşımaz; yalnız yetkili proje işini ayrı, benzersiz slotlarda yürütür.
