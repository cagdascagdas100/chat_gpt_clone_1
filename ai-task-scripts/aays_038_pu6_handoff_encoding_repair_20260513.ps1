$ErrorActionPreference = 'Continue'
$TaskId = 'aays-038-pu6-handoff-encoding-repair-20260513'
$PkgRoot = 'E:\AAYS_DATA\parcel_use6\handoff\parcel_use6_london_postgres_50step_handoff_20260513_040208'
$ZipPath = 'E:\AAYS_DATA\parcel_use6\handoff\parcel_use6_london_postgres_50step_handoff_20260513_040208.zip'
$Manifest = Join-Path $PkgRoot 'PU6_10_HANDOFF_MANIFEST.json'
$Sha = Join-Path $PkgRoot 'PU6_11_SHA256SUMS.txt'
$Csv = Join-Path $PkgRoot 'demo\london_6color_demo_rows.csv'
$Sql = Join-Path $PkgRoot 'db_transfer\upsert_parcel_use6_postgres.sql'
$Utf8 = New-Object System.Text.UTF8Encoding($false)
function W([string]$p,[string]$s){[System.IO.File]::WriteAllText($p,$s,$Utf8)}
function R([string]$p){[System.IO.File]::ReadAllText($p,[System.Text.Encoding]::UTF8)}
function Rel([string]$p){$p.Substring($PkgRoot.Length+1).Replace('\','/')}
$u = [char]0x00FC
$fixedLabel = 'M' + $u + 'stakil'
Write-Output "TASK=$TaskId"
Write-Output "PKG_ROOT=$PkgRoot"
Write-Output 'LIVE_REPO_TOUCH=NO'
if(-not(Test-Path $PkgRoot)){Write-Output 'ERROR=PKG_ROOT_MISSING';exit 2}
if(-not(Test-Path $Manifest)){Write-Output 'ERROR=MANIFEST_MISSING';exit 3}
$s = R $Manifest
$s = $s.Replace('MÃ¼stakil',$fixedLabel)
W $Manifest ($s + $(if($s.EndsWith("`n")){''}else{"`n"}))
$rows = Import-Csv -Encoding UTF8 $Csv
$dist = [ordered]@{'Sanayi'=0;$fixedLabel=0;'Apartman'=0;'Perakende'=0;'Ofis'=0;'Karma'=0}
foreach($r in $rows){$k=[string]$r.use6_label_tr;if($dist.Contains($k)){$dist[$k]=[int]$dist[$k]+1}}
$rowCount=@($rows).Count
$sqlText=R $Sql
$guarded=(($sqlText -match 'WHERE\s+EXISTS') -and ($sqlText -match 'ON\s+CONFLICT\s*\(\s*parcel_id\s*\)'))
$shaLines=Get-ChildItem $PkgRoot -Recurse -File|Where-Object{$_.FullName -ne $Sha}|Sort-Object FullName|ForEach-Object{$rp=Rel $_.FullName;$h=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToUpperInvariant();"$h *$rp"}
W $Sha (($shaLines -join "`n")+"`n")
$bad=@()
Get-ChildItem $PkgRoot -Recurse -File|Where-Object{@('.md','.txt','.json','.csv','.sql','.geojson') -contains $_.Extension.ToLowerInvariant()}|ForEach-Object{if((R $_.FullName) -match 'MÃ¼stakil'){$bad += (Rel $_.FullName)}}
if(Test-Path $ZipPath){Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue}
Compress-Archive -Path (Join-Path $PkgRoot '*') -DestinationPath $ZipPath -Force
$zip=Get-Item $ZipPath
Write-Output "DEMO_ROW_COUNT=$rowCount"
foreach($k in $dist.Keys){Write-Output ("CLASS_DIST_{0}={1}" -f $k,$dist[$k])}
Write-Output "GUARDED_UPSERT_OK=$guarded"
Write-Output "BAD_MOJIBAKE_HIT_COUNT=$(@($bad).Count)"
Write-Output "SHA_LINES=$(@($shaLines).Count)"
Write-Output "ZIP_REBUILT=$($zip.FullName)"
Write-Output "ZIP_SIZE_BYTES=$($zip.Length)"
if($rowCount -ne 12){exit 10}
if((@($dist.Values|Where-Object{$_ -eq 2}).Count) -ne 6){exit 11}
if(-not $guarded){exit 12}
if(@($bad).Count -gt 0){Write-Output ($bad -join ',');exit 13}
Write-Output 'TASK_COMPLETION=100/100'
exit 0
