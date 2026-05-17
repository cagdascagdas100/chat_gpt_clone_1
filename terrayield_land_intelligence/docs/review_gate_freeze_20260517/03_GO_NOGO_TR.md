# Review-Gate GO / NO-GO

| Alan | Karar | Not |
|---|---:|---|
| Backend live | GO | Smoke ile dogrulanir |
| UI live | GO | /england_map_web/ 200 olmali |
| Review endpointleri | GO | Read-only |
| Compile | GO | python -m compileall app -q |
| Pytest | GO | tests/test_review_status_api.py --basetemp |
| Read-only popup/status | GO | Kabul anlamina gelmez |
| Production auto-accept | NO-GO | Kesinlikle kapali |
| DB write | NO-GO | Freeze kapsam disi |
| Scoring promotion | NO-GO | Freeze kapsam disi |
| accept/high-confidence | NO-GO | evidence_checked=yes ve verified polygon/source yoksa yasak |
| threshold relax | NO-GO | DO_NOT_RELAX_THRESHOLDS |
