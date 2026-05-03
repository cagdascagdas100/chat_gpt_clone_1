# Kendi Site Chat Watchdog

Bu klasör, yalnızca kendi sitende çalıştırmak için hazırlanmış yerel bir Playwright otomasyonudur.

## Ne yapar?

- Belirlediğin siteyi açar.
- 10 dakikada bir chat kutusunu bulup mesaj yazar.
- Sayfada işlem devam ediyor gibi görünen metin varsa mesaj göndermeyi atlar.
- Onay modalı içinde `Onayla`, `Evet`, `Tamam`, `Approve`, `Confirm` gibi butonları görürse tıklar.
- Sadece `allowed_hosts` içinde tanımladığın domainde çalışır.

## Kurulum

```powershell
cd automation
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Ayar

`config.example.json` dosyasını kopyala:

```powershell
copy config.example.json config.json
```

`config.json` içinde şunları düzenle:

```json
{
  "site_url": "https://senin-siten.com",
  "allowed_hosts": ["senin-siten.com"],
  "message": "devam et kapsamlı bir işlem yaptır devam ediyorsa bozma takılma varsa tespit et düzelt"
}
```

## Çalıştırma

```powershell
python site_chat_watchdog.py
```

İlk çalıştırmada tarayıcı açılır. Giriş gerekiyorsa manuel giriş yap. Profil `browser-profile` klasöründe saklanır.

## Notlar

- Site koduna erişimin yoksa `chat_input_selectors`, `send_button_texts` ve `approve_button_texts` değerlerini sayfandaki metinlere göre düzenle.
- Bu script görüntüden tıklama yerine DOM/erişilebilirlik metni ile çalışır; daha stabil ve güvenlidir.
- Sadece kendi sitende ve kendi yetkili hesabında kullan.
