# TY146 UI Acceptance Checklist

- Status: pending_manual_browser_acceptance
- Backend live smoke: passed
- Frontend live smoke: passed
- Backend endpoint: http://127.0.0.1:8010/health
- Frontend endpoint: http://127.0.0.1:3000
- Secrets logged: false

## Confirmed Before This Checklist

- Backend returned 200 OK.
- Backend database status returned ok.
- Frontend returned 200 OK.
- Frontend HTML title observed: Great Britain Parcel Map.
- Port 8010 was listening.
- Port 3000 was listening.

## Manual Browser Acceptance Still Required

1. Open http://127.0.0.1:3000 in a browser.
2. Confirm the Great Britain Parcel Map page renders visually.
3. Confirm the map controls are visible.
4. Confirm POI/topography/future-growth related controls are visible if available.
5. Click a parcel or visible map feature.
6. Confirm the AAYS/TerraYield parcel panel opens.
7. Confirm contractor/legal/future-growth/evidence data either renders or shows a clear empty state.
8. Confirm there are no visible JavaScript errors in the browser console.

## Remaining Production Evidence

- Browser screenshot or user confirmation required.
- Parcel click acceptance required.
- Production deployment evidence required.

## Conclusion

Endpoint-level integration is live. Full production readiness now depends on manual browser UI acceptance and production deployment evidence.
