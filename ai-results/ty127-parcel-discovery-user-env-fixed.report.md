# TY127 Parcel Discovery User Env Fixed

Plan completed: 95%
Plan remaining: 5%
DB credentials present after User env import: True
Python exit code: 4
Candidate count: 0

## Raw discovery
{"ok": false, "error": "db_query_failed", "detail": "connection failed: connection to server at \"127.0.0.1\", port 5432 failed: FATAL:  password authentication failed for user \"postgres\"\nconnection to server at \"127.0.0.1\", port 5432 failed: FATAL:  password authentication failed for user \"postgres\"\nMultiple connection attempts failed. All failures were:\n- host: 'localhost', port: '5432', hostaddr: '::1': connection failed: connection to server at \"::1\", port 5432 failed: FATAL:  password authentication failed for user \"postgres\"\nconnection to server at \"::1\", port 5432 failed: FATAL:  password authentication failed for user \"postgres\"\n- host: 'localhost', port: '5432', hostaddr: '127.0.0.1': connection failed: connection to server at \"127.0.0.1\", port 5432 failed: FATAL:  password authentication failed for user \"postgres\"\nconnection to server at \"127.0.0.1\", port 5432 failed: FATAL:  password authentication failed for user \"postgres\""}


## Next Action
Set User-level DB env and rerun. No secret values are written to GitHub.
