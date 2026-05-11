$ErrorActionPreference = "Stop"

$TaskId = "terrayield-047-future-growth-stage1-source-registry"
$Root = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
Set-Location $Root

Write-Output "PROJECT=terrayield"
Write-Output "DISPLAY_PROJECT=TerraYield"
Write-Output "CHATGPT_PAGE_PROJECT=aays1"
Write-Output ("TASK=" + $TaskId)
Write-Output "MODE=stage1_source_registry_minimal_diff"

$Target = Join-Path $Root "FG_STAGE1_SOURCE_REGISTRY.csv"

$Csv = @"
source_key,source_name,purpose,geography,update_frequency,mode,source_url,demo_note
hmlr_price_paid,HM Land Registry Price Paid Data,market_momentum,address/postcode/transaction,monthly,fixture,https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads,"20th working day monthly update; full file large; fixture mode keeps tests deterministic"
planning_data_api,Planning Data API,planning+policy+constraints,parcel/area,varies,live,https://www.planning.data.gov.uk/docs,"point+UPRN query; no batch endpoint"
planning_brownfield,Brownfield land,planning_growth,site/polygon,collector-run,live,https://www.planning.data.gov.uk/dataset/brownfield-land,"CSV/JSON/GeoJSON downloads"
planning_conservation,Conservation area,planning_constraints,polygon,collector-run,live,https://www.planning.data.gov.uk/dataset/conservation-area,"work in progress/incomplete source coverage; do not allow high confidence without parcel-specific evidence"
planning_listed_building,Listed building,planning_constraints,point,collector-run,live,https://www.planning.data.gov.uk/dataset/listed-building,"point representation; extent caution"
planning_green_belt,Green belt,planning_policy,polygon,annual snapshot,live,https://www.planning.data.gov.uk/dataset/green-belt,"snapshot timing caveat"
ons_snpp,ONS Subnational Population Projections,demographic_demand,local_authority,release-based,fixture,https://www.ons.gov.uk/releases/subnationalpopulationprojections2022based,"LA level projections; fixture mode until release loader is wired"
ons_internal_migration,ONS Internal Migration Projections,demographic_demand,local_authority,release-based,fixture,https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationprojections/datasets/internalmigrationz5,"25-year internal migration projections; fixture mode until release loader is wired"
naptan,NaPTAN,transport_infra,point,daily,fixture,https://www.data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/naptan,"CSV/XML plus API links; fixture mode avoids live dependency in tests"
bods,Bus Open Data Service,transport_infra,route/stop,operator-published,stub,https://www.gov.uk/guidance/find-and-use-bus-open-data,"consumer API use documented; typed stub until API credentials/config are present"
national_rail_darwin,Darwin Data Feeds,transport_infra,station/service,realtime/live feeds,stub,https://www.nationalrail.co.uk/developers/darwin-data-feeds/,"Rail Data Marketplace sign-up required; typed stub only"
tfl_ptal,TfL WebCAT PTAL,transport_infra,london grid,source-defined,stub,https://tfl.gov.uk/info-for/urban-planning-and-construction/planning-applications/planning-with-webcat?intcmp=25861,"London-only PTAL workflow; import path not live connector yet"
gias_schools,Get Information about Schools,social_amenity,establishment,daily,fixture,https://get-information-schools.service.gov.uk/,"public downloads updated daily; fixture mode for deterministic tests"
nhs_ods_ord,NHS ODS ORD API,social_amenity,organisation/address,api-based,fixture,https://digital.nhs.uk/developer/api-catalogue/organisation-data-service-ord,"sync endpoint available; fixture mode until connector contract is implemented"
os_open_greenspace,OS Open Greenspace,social_amenity,polygon,six-monthly,fixture,https://www.ordnancesurvey.co.uk/products/os-open-greenspace,"download formats available; fixture mode until collector is implemented"
ea_flood_zones_cc,EA Flood Zones plus Climate Change,risk_penalty,polygon,as-needed,fixture,https://www.data.gov.uk/dataset/77931470-ee6b-4f8e-8868-82842aed2e5d/flood-map-for-planning-flood-zones-plus-climate-change,"OGC/WFS/WMS/download links; fixture mode until spatial loader is implemented"
"@

Set-Content -Path $Target -Value $Csv -Encoding UTF8

Write-Output "VALIDATION=started"

$Rows = Import-Csv $Target

$AllowedModes = @("live","fixture","stub")

$MissingUrl = @($Rows | Where-Object { [string]::IsNullOrWhiteSpace($_.source_url) })
$BadMode = @($Rows | Where-Object { $AllowedModes -notcontains $_.mode })
$BadUrl = @($Rows | Where-Object { $_.source_url -notmatch "^https?://" })

Write-Output ("ROW_COUNT=" + $Rows.Count)
Write-Output ("MISSING_SOURCE_URL_COUNT=" + $MissingUrl.Count)
Write-Output ("BAD_MODE_COUNT=" + $BadMode.Count)
Write-Output ("BAD_URL_COUNT=" + $BadUrl.Count)

if ($MissingUrl.Count -gt 0) {
  Write-Output "FAILED=missing_source_url"
  $MissingUrl | Format-Table | Out-String | Write-Output
  exit 1
}

if ($BadMode.Count -gt 0) {
  Write-Output "FAILED=bad_mode"
  $BadMode | Format-Table | Out-String | Write-Output
  exit 1
}

if ($BadUrl.Count -gt 0) {
  Write-Output "FAILED=bad_url"
  $BadUrl | Format-Table | Out-String | Write-Output
  exit 1
}

Select-String -Path $Target -Pattern "fixture/live|stub/live|stub/import" -SimpleMatch | Out-String | Write-Output

Write-Output "VALIDATION=passed"

git diff -- FG_STAGE1_SOURCE_REGISTRY.csv 2>&1 | Out-String | Write-Output

Write-Output "TERRAYIELD_STAGE1_DONE"
exit 0
