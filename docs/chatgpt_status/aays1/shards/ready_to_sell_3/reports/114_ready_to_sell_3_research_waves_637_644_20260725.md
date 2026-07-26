# ready_to_sell_3 — Research Waves 637–644

- Continuation key: `6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a`
- Source scope: current official Auction House catalogue and official lot-detail pages.
- Screened rows: **22**.
- New research-only candidates: **16** across waves **637–644**.
- Official catalogue identities: **16/16**.
- Full official lot-detail readback: **16/16**.
- Exact-address repository checks: **20**, matches: **0**.
- Average source confidence: **99.87/100**.
- Fail-closed exclusions: **4** temporal/detail conflicts, **1** conflicting achieved-rent record and **1** incomplete current-detail record.
- Guarded source warning: **1** remaining-lease inconsistency; the conflicting remainder was omitted.
- Transient official-source 503: recovered with bounded exact-address official searches; no infinite retry.
- Web progress events: **40/40 completed**.
- Visible research rows after wave 644: **3459**.
- Canonical promotion: **0**.

## Candidate summary

1. 83 Carr Road — two-bedroom semi-detached cottage; guide £180,000.
2. 102 Caunce Street — three-bedroom freehold mid terrace; title LA897013; guide £50,000.
3. 49 Copeland Avenue — three-bedroom semi-detached house; guide £50,000.
4. Hawksworth Road Land — freehold vacant plot, approximately 260 sq m; guide £2,000–£5,000.
5. Apartment 23, 4 Hick Street — leasehold studio; 998 years from 1 June 2005; guide £17,000.
6. 32 James Street — two-bedroom end-terrace refurbishment; guide £38,000.
7. Nebula 716 — vacant leasehold student room; guide £10,000.
8. 45A Princes Street — vacant one-bedroom freehold single-storey dwelling; guide £32,000+.
9. 59 Camm Street — freehold one-bedroom property with unfinished reconfiguration; guide £55,000+.
10. 19 Severn Street — vacant two-bedroom freehold mid terrace; guide £30,000.
11. Land at Bullfinch Close — freehold vacant plot, approximately 225 sq m; guide £500–£2,000.
12. 114 Collingwood Court — vacant two-bedroom maisonette; guide £5,000.
13. Apartment 6 Kemley House — two-bedroom leasehold apartment, tenant at £650 pcm; guide £10,000–£20,000.
14. 8 Brindley Court — leasehold one-bedroom first-floor flat; guide £12,000.
15. 11 Charles Street — freehold two-bedroom investment, tenant at £500 pcm; guide £35,000.
16. 2 Beeston Ridge — vacant three-bedroom freehold detached house; guide £110,000.

## Integrity controls

- Missing legal, tenure and occupancy values were not inferred.
- Projected or comparable rents were not treated as achieved income.
- Land marketing and CGI/development possibilities were not treated as planning or geometry proof.
- Current conflicting rent and lease-remainder values were excluded rather than reconciled by inference.
- All rows remain `research_only=true` and `promotion_allowed=false`.

## Current blocker

`AUTOMATION_167_DOM_PROOF` remains the first unverified step. The canonical execution host has no live owner or current heartbeat, and the port-8012 headless DOM proof is absent. Canonical parcel and geometry proof are also absent. Research may continue, but promotion and final acceptance remain blocked.