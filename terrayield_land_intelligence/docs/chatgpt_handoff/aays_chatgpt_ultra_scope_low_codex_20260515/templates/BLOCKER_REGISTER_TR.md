# Blocker Register (TR)

| Blocker ID | Severity | Owner | Trigger | Evidence | Unblock Action | Onay Gerekli mi |
|---|---|---|---|---|---|---|
| BLOCKED_BY_MANAGED_DB_SELECTION | High | Platform | Managed target yok | step reports | provider secimi | Evet |
| BLOCKED_BY_SECRET_STORE_BINDING | High | Ops | Secret store bagli degil | env audit | secure bind | Evet |
| BLOCKED_BY_DEPLOY_APPROVAL | High | Release | Prod deploy kapali | policy | deploy approval | Evet |
