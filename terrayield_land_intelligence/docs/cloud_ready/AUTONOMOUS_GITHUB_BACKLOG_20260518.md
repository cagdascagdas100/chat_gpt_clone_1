# Autonomous GitHub-Only Backlog - 2026-05-18

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Batch backlog status

### Completed in GitHub-only mode

- [x] Cloud readiness docs
- [x] Current status file
- [x] Machine-readable status
- [x] Final manifest
- [x] Index
- [x] Provider decision package
- [x] Fast path deploy playbook
- [x] Provider env checklist
- [x] Hosted smoke script
- [x] Hosted smoke result template
- [x] Runtime proof gap register
- [x] GitHub-only completion report
- [x] GitHub-only autonomous scope matrix
- [x] Autonomy escalation plan
- [x] Persistent runner upgrade package
- [x] Safe runner task protocol
- [x] Watchdog runner design
- [x] Safe watchdog runner script
- [x] Watchdog start wrapper
- [x] Watchdog usage guide
- [x] Watchdog evidence template
- [x] Watchdog readiness validator
- [x] Next operator handoff
- [x] Long-run operating policy

### Known gaps that should not be loop-checked repeatedly

- [ ] 012A report publication
- [ ] 012B report publication
- [ ] Fresh local pytest
- [ ] Fresh local smoke
- [ ] Fresh local performance
- [ ] Hosted backend proof
- [ ] Cloud DB proof
- [ ] Public frontend proof
- [ ] Hosted smoke 6/6

### Future GitHub-only maintenance tasks

- [ ] Keep status files synchronized after new evidence appears.
- [ ] Update runtime proof gap register when evidence appears.
- [ ] Update final manifest if classification changes.
- [ ] Update index if new files are added.
- [ ] Keep safety invariants visible in all reports.

## Escalation gates

Escalate only when one of these becomes available:

- local watchdog execution
- hosted CI result
- public backend URL
- cloud DB provider confirmation
- hosted smoke output
- frontend public URL

## Safety invariant

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
