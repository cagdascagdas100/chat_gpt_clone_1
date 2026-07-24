Visibility notes

Problem observed by user:
The local review page does not show the latest row evidence clearly. The screenshot shows older counts and unreadable Turkish characters.

Expected latest data from repository:
- live source verified rows: 30
- reviewed rows: 30
- visible progress: 86 percent
- confidence upgrade remains pending until photo and polygon visual comparison is complete

Observed local page:
- live source verified rows shown as 14
- visible progress shown as 70 percent
- Turkish labels are mojibake

Likely cause:
The local page is loading stale or cached AI evidence data, or it is served from an older local copy. The text encoding served by the local page also needs a UTF-8 fix.

Required site changes:
- show loaded AI evidence file path and loaded geometry file path at the top of the page
- show AI status, update time, reviewed rows, verified rows, result count, and visible progress
- add cache-busting to the page data fetches
- show a visible warning when the loaded local data is older than the expected repo data
- fix UTF-8 rendering for Turkish labels
- show per-row source URL, source status, source result, listing type, photo count, area, planning ref, page title, status file path, report file path, local source path, downloaded photo path, and run marker when available
- use an explicit empty value for missing local artifact paths
- highlight rows changed in the latest run with a clear badge

Acceptance:
- page displays clean Turkish text
- page shows 30 live-source verified rows and 86 percent visible progress when latest repo data is loaded
- page clearly warns if local data is stale
- rows 1 to 30 show source evidence row by row
- new rows are visually marked
- source and artifact paths are visible row by row when available

Next action:
Update the review HTML and data loader first. After the visibility problem is fixed, continue the existing verification task after row 30. Do not increase progress without a real pushed status file.
