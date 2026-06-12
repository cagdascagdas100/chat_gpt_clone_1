# Sold Buildings Node Check Diagnosis

task_id: sold-buildings-historical-sales-node-check-diagnosis-20260613
status: NODE_CHECK_BLOCKING_FINAL_READY
final_ready: false
production_complete: false
branch_detected: feature/terrayield-aays-integration
power_shell_required_from_user: false

## node_exit_code
1

## node_output
C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\app.js:8694
    window.__lastHistoricalSalesStatus = await fetchJsonWithTimeout(${landIntelligenceApiBaseUrl}/map/sales-history/status, { timeout: 8000 });
                                                                    ^
System.Management.Automation.RemoteException
SyntaxError: missing ) after argument list
    at wrapSafe (node:internal/modules/cjs/loader:1469:18)
    at checkSyntax (node:internal/main/check_syntax:78:3)
System.Management.Automation.RemoteException
Node.js v22.11.0

## app.js context 8686-8702


## Known data gate
BLOCKED_MISSING_OFFICIAL_BRIDGE
