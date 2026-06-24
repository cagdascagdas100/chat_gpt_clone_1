# ChatGPT Task Split - Topography

## ChatGPT yapabilir

1. Eksik isleri kategori bazli ayirmak
2. Operator icin PowerShell script metni yazmak
3. Remote sync icin karar agaci cikarmak
4. England-wide coverage icin klasor ve data manifest planlamak
5. UI smoke icin manuel test checklist'i hazirlamak
6. Parcel lookup `no_data` durumunu raporlama formatina dokmek

## ChatGPT yapamaz

1. F worktree icindeki gercek branch divergence durumunu kendisi okuyamaz
2. 8010 servisini localde kaldiramaz
3. D/F disklerindeki gercek veri klasorlerini kendisi teyit edemez
4. Browserda parcel click smoke'u gercekten yapamaz
5. Git non-fast-forward durumunu local calisma alaninda gercekten cozemaz

## Codex veya operatorun yapmasi gerekenler

1. Remote branch sync'i gercek local branch'e gore cozmeye devam etmek
2. England-wide veri klasorleri gercekten var mi diye D/F uzerinden audit calistirmak
3. Parcel lookup coverage'i ornek parcel listesiyle endpoint uzerinden olcmek
4. Manuel UI smoke yapmak

## En hizli ilerleme modeli

1. Bu paketi ChatGPT'ye ver
2. ChatGPT'den script iyilestirme ve operator checklist iste
3. Kullanici PowerShell scriptlerini lokal calistirsin
4. Cikan raporlarla yalniz kalan local blocker varsa onu Codex'e geri ver
