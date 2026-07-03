# Security official source candidates

page_key=security_public_safety
layer=Safety / Security
program_output=Security Level percent
final_ready=false
fake_data=false
person_level_data=false

## Candidate official sources

1. data.police.uk Police API documentation for street-level public safety incidents.
2. data.police.uk Police API documentation for incident category vocabulary.

## Integration notes

- The street-level endpoint supports a point radius or custom polygon area.
- The category endpoint supports date-based category vocabulary.
- Current repo state has no verified non-empty joined parcel rows.
- No fake rows should be created.

## Remaining blockers

- Implement parcel polygon or centroid join.
- Generate verified non-empty parcel security rows.
- Produce final browser or DOM proof for the program UI.
