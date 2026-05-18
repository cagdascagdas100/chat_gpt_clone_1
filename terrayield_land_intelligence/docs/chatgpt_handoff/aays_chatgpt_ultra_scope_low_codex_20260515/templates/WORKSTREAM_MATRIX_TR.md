# Workstream Matrix (TR)

| Workstream | Owner | Scope | Input | Output | Gate |
|---|---|---|---|---|---|
| Canonical Data Minset | Platform | DB min core + raw separation | page exports + manifests | minset spec | p95 safe |
| Registry/Resolver | Backend | path + env canonicalization | runtime registry + step reports | resolver policy | no hardcoded drift |
| API Contract | Backend | payload minimization | cost/handoff/ops endpoints | contract table | smoke 7/7 |
| Performance | Backend | p95 budget + cache | endpoint traces | perf budget | p95 targets |
| Safety | QA | secret/mutation guard | step reports | safety verdict | all none/false |
| Release Gate | QA | final classification | step10/11/12 | go/no-go | confirmed |
