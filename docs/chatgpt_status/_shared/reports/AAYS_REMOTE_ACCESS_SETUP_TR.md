# AAYS Yeni Bilgisayar Uzaktan Erisim

Bu dosyalar F portable kokunden calisir. Router portu acmayin.

1. Yeni islem bilgisayarina Chrome Remote Desktop host kurun:
   https://remotedesktop.google.com/access
2. Kalici erisim PIN'i tanimlayin ve Google hesabinda iki asamali dogrulamayi acin.
3. Yeni bilgisayara ve kontrol bilgisayarina Tailscale kurun:
   https://tailscale.com/download/windows
4. Iki bilgisayarda ayni Tailscale hesabi ile oturum acin.
5. AAYS uygulamasini 8012'de baslatin.
6. Portable kokte CHECK_AAYS_REMOTE_ACCESS.ps1 calistirin.
7. Ardindan CONFIGURE_AAYS_TAILSCALE_SERVE.ps1 calistirin.
8. Tailscale'in gosterdigi ozel HTTPS adresini yalniz kendi cihazlarinizda kullanin.

Chrome Remote Desktop tam masaustu mudahalesi icindir. Tailscale Serve, AAYS panelini yalniz ozel aga acar.
Bilgisayar tamamen kapanirsa uzaktan yazilim acamaz; BIOS Restore on AC Power Loss, UPS veya akilli priz gerekir.
F diski baska bilgisayara takildiginda Chrome Remote Desktop ve Tailscale o bilgisayarda bir kez kurulup yetkilendirilmelidir.