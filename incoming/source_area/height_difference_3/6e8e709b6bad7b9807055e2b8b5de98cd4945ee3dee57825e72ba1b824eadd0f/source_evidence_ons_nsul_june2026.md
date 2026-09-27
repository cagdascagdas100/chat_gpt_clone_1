# ONS National Statistics UPRN Lookup (NSUL), June 2026 — source-area / crosswalk evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-28T00:07:00+03:00

Official source
- Publisher: Office for National Statistics, ONS Geography
- Product: National Statistics UPRN Lookup (NSUL)
- Current window: June 2026 for the United Kingdom / Great Britain UPRN coverage
- Open Geography Portal lists the June 2026 release on 7 August 2026.
- ONS states NSUL is available for Great Britain and is released every six weeks.
- Format: CSV.
- ONS UPRN products are open data; ONS licensing guidance places UPRN products under the Open Government Licence with required OS/Royal Mail/GeoPlace/ONS attributions.

Lookup semantics
- NSUL relates the UPRN for each current GB address to a 2021 Census Output Area using the UPRN and point-in-polygon methodology.
- Those Output Areas are then related to higher statistical and statutory geographies, including local authority districts, mainly by ONS best-fit methodology.
- ONS confirms postcodes have been included in NSUL and ONSUD; source/currency of the postcode attribution is documented per product release.

Official URLs
- Product overview: https://www.ons.gov.uk/methodology/geography/geographicalproducts/nationalstatisticsaddressproducts
- Open Geography Portal: https://geoportal.statistics.gov.uk/
- Licensing: https://www.ons.gov.uk/methodology/geography/licences
- Postcode-in-UPRN-products confirmation: https://www.ons.gov.uk/aboutus/transparencyandgovernance/freedomofinformationfoi/inclusionofpostcodesintheonsudandnsulproducts

Scope decision
This is a non-spatial official lookup/source-area window. No arbitrary UPRN, postcode, Output Area or local-authority value is assigned to canonical rows 61523–92283 because this execution context does not expose a trusted canonical UPRN, postcode or geometry field.

Height Difference next step
If local canonical rows expose a trusted UPRN or postcode/geometric anchor, local OpenCode can use NSUL to resolve administrative/statistical geography, use OS Open Linked Identifiers to bridge UPRN to TopographicArea TOID, verify a real building footprint, and then calculate official DEM/LIDAR min/max/mean/max-min.
