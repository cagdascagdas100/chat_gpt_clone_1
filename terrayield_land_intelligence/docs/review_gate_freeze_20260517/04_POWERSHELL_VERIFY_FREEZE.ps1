cd C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
Invoke-RestMethod "http://127.0.0.1:8010/api/review/gates" | ConvertTo-Json -Depth 8
Invoke-RestMethod "http://127.0.0.1:8010/api/review/status/by-listing/OTM-16748769" | ConvertTo-Json -Depth 8
Invoke-WebRequest "http://127.0.0.1:8010/england_map_web/" -UseBasicParsing | Select-Object StatusCode
python -m compileall app -q
$tmp = "$env:LOCALAPPDATA\Temp\aays_pytest"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
python -m pytest -q tests/test_review_status_api.py --basetemp "$tmp"
