# Performance Budget Template (TR)

| Endpoint | Cold p95 target (ms) | Warm p95 target (ms) | Payload cap | Cache key | TTL | Notes |
|---|---:|---:|---:|---|---:|---|
| /handoff/status | 1500 | 600 | 150 KB | handoff:status:v1 | 30s | read-only |
| /cost/integration/status | 1800 | 700 | 200 KB | cost:integration:v1 | 30s | read-only |
| /map/listings?limit=200 | 2500 | 1200 | 2 MB | map:listings:l200 | 45s | pagination |
| /map/sales-history/combined?limit=200 | 3000 | 1500 | 3 MB | map:sales:combined:l200 | 60s | heavy route |
