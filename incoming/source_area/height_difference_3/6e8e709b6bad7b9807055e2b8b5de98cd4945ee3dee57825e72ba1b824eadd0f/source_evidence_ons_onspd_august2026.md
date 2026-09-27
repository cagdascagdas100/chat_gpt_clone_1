# ONS Postcode Directory (August 2026) — source-area / postcode crosswalk evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-28T00:07:00+03:00

Official current release
- Publisher: Office for National Statistics, ONS Geography
- Product: ONS Postcode Directory (August 2026) for the United Kingdom
- Open Geography Portal release: CSV Collection, 1 September 2026
- Open Geography Portal hosted table release: 16 September 2026
- Portal also displays a notice dated 10 September 2026 concerning an update to the August 2026 Postcode Directories. The notice is retained as a caveat; this package does not infer its detailed effect without the notice body.
- Open Geography Portal is public and states its content is open under OGL v3.0 except where otherwise stated.

ONSPD semantics
- ONS states ONSPD links all current and terminated UK postcodes to administrative, electoral, health and other geographies using point-in-polygon methodology.
- ONSPD grid references are available at 1-metre resolution.
- Postcode coordinates are also available as latitude and longitude.
- OSLAUA is the current Local Authority District / equivalent field; it may be blank for postcodes with no grid reference.

Official URLs
- Open Geography Portal: https://geoportal.statistics.gov.uk/
- ONS postcode-products documentation: https://www.ons.gov.uk/methodology/geography/geographicalproducts/postcodeproducts
- ONS postal-geography documentation: https://www.ons.gov.uk/methodology/geography/ukgeographies/postalgeography

Scope decision
This is a public official postcode crosswalk/source-area window. No arbitrary postcode is assigned to canonical partition rows 61523–92283 because this execution context still does not expose a trusted canonical postcode, UPRN, or geometry field.

Height Difference next step
If local canonical rows expose postcode, UPRN, or real geometry, local OpenCode can use ONSPD for postcode coordinates/geography, NSUL/OS Open UPRN and OS Open Linked Identifiers for identifier bridges, verify actual building footprints, then calculate official DEM/LIDAR min/max/mean/max-min statistics.
