# TerraYield Naming Policy

This policy is used for TerraYield worker jobs, result files, dashboard references, task ids, heartbeat files, and page-job descriptors.

## Goal

Prevent TerraYield jobs from being mixed with other project jobs. Every reference must include the project name and a clear work scope.

## Required prefix

Use this prefix for all TerraYield automation artifacts:

```text
terrayield
```

## Standard task id format

```text
terrayield-<stepNumber>-<scope>-<action>
```

Examples:

```text
terrayield-068-backend-api-validation
terrayield-068-frontend-map-admin-ui
terrayield-068-ops-docker-health
terrayield-068-data-cache-inventory
terrayield-068-tests-compile-smoke
```

## Page-job descriptor filename format

```text
terrayield-<stepNumber>-<scope>-<action>.job
```

Examples:

```text
ai-page-jobs/inbox/terrayield-068-backend-api-validation.job
ai-page-jobs/inbox/terrayield-068-frontend-map-admin-ui.job
ai-page-jobs/inbox/terrayield-068-ops-docker-health.job
ai-page-jobs/inbox/terrayield-068-data-cache-inventory.job
ai-page-jobs/inbox/terrayield-068-tests-compile-smoke.job
```

## Result filename format

```text
ai-results/terrayield-<stepNumber>-<scope>-<action>-result.md
```

For worker slots:

```text
ai-results/terrayield-<stepNumber>-slot-<slotNumber>-<scope>-result.md
```

Examples:

```text
ai-results/terrayield-068-slot-1-backend-api-result.md
ai-results/terrayield-068-slot-2-frontend-map-admin-ui-result.md
ai-results/terrayield-068-slot-3-ops-docker-health-result.md
ai-results/terrayield-068-slot-4-data-cache-inventory-result.md
ai-results/terrayield-068-slot-5-tests-compile-smoke-result.md
```

## Heartbeat filename format

```text
ai-heartbeat/terrayield-<stepNumber>-slot-<slotNumber>-<scope>.md
```

Examples:

```text
ai-heartbeat/terrayield-068-slot-1-backend-api.md
ai-heartbeat/terrayield-068-slot-2-frontend-map-admin-ui.md
ai-heartbeat/terrayield-068-slot-3-ops-docker-health.md
ai-heartbeat/terrayield-068-slot-4-data-cache-inventory.md
ai-heartbeat/terrayield-068-slot-5-tests-compile-smoke.md
```

## Dashboard job display names

Use short project-aware names:

```text
TerraYield Backend API
TerraYield Frontend Map/Admin
TerraYield Ops Docker
TerraYield Data Cache
TerraYield Tests Smoke
TerraYield Active Pool
```

## Rules

1. Do not use generic names such as `backend`, `frontend`, `ops`, `tests` alone.
2. Always include `terrayield` in task ids and file names.
3. Use the same step number across all worker slots created for the same user command.
4. Use new step numbers for new `devam et` cycles.
5. Do not reuse a task id already present in `.last-task-id`.
6. Each active slot must write its own project-specific result file.
7. Each active slot must write its own project-specific heartbeat file.
8. Polling alone must not be counted as real work.
9. Finished evidence must include slot count, completed count, timeout count, error count, and output file paths.

## Current preferred five-slot naming model

```text
terrayield-068-slot-1-backend-api-validation
terrayield-068-slot-2-frontend-map-admin-ui
terrayield-068-slot-3-ops-docker-health
terrayield-068-slot-4-data-cache-inventory
terrayield-068-slot-5-tests-compile-smoke
```
