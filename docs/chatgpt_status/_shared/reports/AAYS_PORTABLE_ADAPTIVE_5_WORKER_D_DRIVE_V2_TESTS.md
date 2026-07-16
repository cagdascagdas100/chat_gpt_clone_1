# AAYS Portable Adaptive V2 Test Results

| Test | Result |
|---|---|
| SHA256 input package | PASS |
| Python coordinator syntax | PASS |
| Python panel syntax | PASS |
| PowerShell launcher/installer parse | PASS |
| One coordinator process | PASS |
| Second launch blocked | PASS |
| Five distinct child Git roots | PASS |
| Child direct push forbidden | PASS 5/5 |
| Five light fixtures simultaneous | PASS, measured 5 |
| Business files changed by fixtures | PASS, 0 |
| Same-slot/duplicate task guard | PASS |
| Wrong-slot aays1 classifier guard | PASS |
| Case-insensitive parent/child path overlap | PASS |
| RAM-heavy peak | PASS, 1 |
| Raster-heavy peak | PASS, 1 |
| Git publish peak | PASS, 1 |
| Runtime sync peak | PASS, 1 |
| Browser acceptance peak | PASS, 1 |
| Shared publish peak | PASS, 1 |
| Child crash isolation | PASS |
| Corrupt checkpoint quarantine | PASS |
| Alternate drive root simulation | PASS |
| Disk missing/reconnect simulation | PASS |
| Network loss/reconnect simulation | PASS |
| Sleep/resume simulation | PASS |
| Reboot resume simulation | PASS |
| Checkpoint hydration against publisher HEAD | PASS 5/5 |
| Graceful stop/restart and new PID | PASS |
| Panel safe-remove state | PASS |
| HTTP 8012 health | PASS, 200 |
| HTTP 8012 england_map_web | PASS, 200 |
| HTTP 8012 openapi | PASS, 200 |
| Remote code readback syntax/schema | PASS 8/8 |

Physical disk removal, reboot, sleep and network disconnection were not performed. Their injected simulations passed. `final_ready=false` remains unchanged.
