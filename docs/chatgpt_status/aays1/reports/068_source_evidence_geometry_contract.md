# 068 Source Evidence Geometry Contract

Status: READY_FOR_RUNNER_IMPLEMENTATION
Final ready: false

This task replaces table-only restore with the real target workflow.

Required workflow:
1. Read the 2OF4 geometry review queue CSV from the F repo data folder.
2. For each listing URL, collect source evidence: page status, title, price, area, address or postcode, description, image links, map links, and saved evidence path.
3. Use postcode, centroid, bbox, title/address, and source evidence to produce a better candidate parcel review record.
4. Do not create or upgrade a polygon unless the evidence contains a reliable boundary source.
5. Keep every row as 2OF4 pending when evidence is missing or weak.
6. Write HTML, CSV, status, and report outputs under docs/chatgpt_status/aays1 and england_map_web.

Safety gates:
- no fake evidence
- no fake polygon
- no DB write
- no migration
- no DDL
- no production deploy
- final_ready=false until real evidence supports completion

Current blocker:
The previous long source-fetch implementation was blocked during GitHub file creation. The next runner work must implement this contract in small files or reuse an existing local helper, then process small batches.
