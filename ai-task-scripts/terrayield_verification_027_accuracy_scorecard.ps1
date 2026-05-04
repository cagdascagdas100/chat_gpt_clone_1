$ErrorActionPreference = 'Continue'
$Project = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$Start = Get-Date
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Project ".aays_next_fix\verification_027_accuracy_scorecard_$Run"
$SummaryFile = Join-Path $ReportDir 'summary.md'
$ScoreCsv = Join-Path $ReportDir 'accuracy_scorecard.csv'
$RoadmapFile = Join-Path $ReportDir 'accuracy_expansion_roadmap.md'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log([string]$Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $SummaryFile -Value $line}
function Exists([string]$Path){if(Test-Path $Path){1}else{0}}
function Health(){try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 'http://localhost:8010/health'; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){1}else{0}}catch{0}}
Log 'TASK: TerraYield verification 027 accuracy scorecard and expansion roadmap'
Log 'MODE: non-destructive; broad accuracy planning; two recurring score values; no scraping; no DB writes'
Log "PROJECT=$Project"
Log "REPORT_DIR=$ReportDir"
$api = Health
$plan = Exists '.aays_verification\README.md'
$svc = Exists 'app\services\sale_land_verification.py'
$route = Exists 'app\api\routes\aays_sale_land_verification.py'
$mig = Exists 'alembic\versions\20260504_022_sale_land_verification_evidence.py'
$gen = Exists 'scripts\generate_sale_land_verification_backlog.py'
$backlogSeedCount = 0
Get-ChildItem -Path '.aays_next_fix' -Recurse -Filter 'verification_backlog_seed.csv' -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { try { $backlogSeedCount = [Math]::Max(0,((Get-Content $_.FullName).Count-1)) } catch {} }
$inventoryCount = 0
Get-ChildItem -Path '.aays_next_fix' -Recurse -Filter 'local_data_inventory.txt' -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { try { $inventoryCount = (Get-Content $_.FullName).Count } catch {} }
$evidenceScore = 5 + 8*$plan + 8*$svc + 6*$route + 8*$mig + 8*$gen + [Math]::Min(15,[int]($backlogSeedCount/10)) + [Math]::Min(10,[int]($inventoryCount/50))
if($evidenceScore -gt 100){$evidenceScore=100}
$geometryScore = 3 + 10*$svc + 5*$mig + [Math]::Min(8,[int]($backlogSeedCount/20))
if($geometryScore -gt 100){$geometryScore=100}
$apiScore = if($api -eq 1){95}else{45}
$rows = @(
'scale,value,meaning,next_threshold',
"evidence_chain_accuracy,$evidenceScore,Kaynak URL fiyat alan konum resmi belge ve review zincirinin sistemsel hazır olma skoru,70 means usable backlog 90 means high trust evidence warehouse",
"geometry_boundary_accuracy,$geometryScore,Satış boundary poligonunun belge georeference alan kenar uzunluğu ve review ile doğrulanma skoru,60 means L3 review ready 85 means L4 production ready",
"api_operational_health,$apiScore,API ve otomasyonun çalışır durumda olma skoru,90 means safe to continue automation"
)
Set-Content -Encoding UTF8 -Path $ScoreCsv -Value $rows
$roadmap = @'
# TerraYield Doğruluk Artırma Geniş Kapsam Roadmap

## Sürekli raporlanacak iki ana doğruluk değeri
1. Evidence-chain accuracy: kaynak URL, fiyat, alan, konum, resmi belge, duplicate listing, review ve audit zinciri.
2. Geometry-boundary accuracy: gerçek satış parselinin poligon, alan, kenar uzunluğu, georeference ve L4 onay doğruluğu.

## Kritik prensip
Bu proje bitmiş sayılmayacak. Her yeni çalışma bu iki skoru yükseltmeye veya skorun neden yükselmediğini açıklamaya hizmet edecek. Candidate polygon veya resmi parsel eşleşmesi, gerçek satış boundary gibi gösterilmeyecek.

## Kapsam genişletme eksenleri
- 3110 kayıt tamamı için URL/fiyat/alan/konum normalize edilecek.
- Aynı araziyi satan birden fazla ilan tek opportunity group altında birleşecek.
- Public brochure, red-line, title plan, site plan ve planning document sinyalleri evidence tablosuna bağlanacak.
- AI görsel analizi sadece L3 aday boundary üretecek; L4 için georeference, alan toleransı, kenar uzunluğu ve review gerekecek.
- Su, elektrik, yol, flood, planning ve official parcel context ayrı due-diligence skorları olarak tutulacak.
- Her yıl verification_run tekrar çalışacak; değişen fiyat, alan, source ve geometri kararı raporlanacak.

## Sonraki teknik adımlar
1. /map/listings response içine verification_level, confidence_breakdown, missing_evidence ve display_polygon_warning ekle.
2. Backlog generatorı gerçek 3110 datasetine bağla.
3. Evidence tables migration zincirini mevcut alembic head ile uyumlu hale getir.
4. Duplicate listing grouper ekle.
5. Public document registry ve hash tablosu ekle.
6. Georeference + side-length calculation modülü ekle.
7. L3 review queue ve L4 approval workflow ekle.
8. Accuracy score dashboard üret.

## Takılma politikası
API sağlıklıysa restart yok. API sağlıksızsa sadece API container recovery. Runner/watchdog çalışıyorsa dokunma. Kritik olmayan warning varsa önce raporla, sonra hedefli küçük görev aç.
'@
Set-Content -Encoding UTF8 -Path $RoadmapFile -Value $roadmap
Log "EVIDENCE_CHAIN_ACCURACY=$evidenceScore/100"
Log "GEOMETRY_BOUNDARY_ACCURACY=$geometryScore/100"
Log "API_OPERATIONAL_HEALTH=$apiScore/100"
Log "BACKLOG_SEED_ROWS=$backlogSeedCount"
Log "LOCAL_INVENTORY_COUNT=$inventoryCount"
Log "SCORE_CSV=$ScoreCsv"
Log "ROADMAP_FILE=$RoadmapFile"
Log 'RESULT=accuracy_scorecard_created'
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
Log "ELAPSED_SECONDS=$elapsed"
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "SCORE_CSV=$ScoreCsv"
Write-Output "ROADMAP_FILE=$RoadmapFile"
Write-Output "EVIDENCE_CHAIN_ACCURACY=$evidenceScore/100"
Write-Output "GEOMETRY_BOUNDARY_ACCURACY=$geometryScore/100"
Write-Output "API_OPERATIONAL_HEALTH=$apiScore/100"
Write-Output 'RESULT=accuracy_scorecard_created'
Write-Output 'VERIFICATION_027_ACCURACY_SCORECARD_DONE'
exit 0
