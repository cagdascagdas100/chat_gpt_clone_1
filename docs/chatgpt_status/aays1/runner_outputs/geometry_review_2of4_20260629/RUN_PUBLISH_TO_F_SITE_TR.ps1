$ErrorActionPreference = "Stop"
Write-Host "AAYS / TerraYield 2/4 geometri review F-site publish basliyor..."
$script = "C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\publish_2of4_geometry_review_to_f_site.py"
if (!(Test-Path -LiteralPath $script)) { throw "Publish script bulunamadi: $script" }
python $script
Write-Host "Bitti. Review URL: http://127.0.0.1:8010/england_map_web/geometry_review_2of4_20260629.html"
Write-Host "Ana uygulama URL: http://127.0.0.1:8010/england_map_web/"
