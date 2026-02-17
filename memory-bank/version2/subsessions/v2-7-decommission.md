---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Executing V2.7 legacy decommission
**Dependencies:** `memory-bank/version2/implementation-plan-v2.md`, `memory-bank/version2/subsessions/v2-6-secondary-migration.md`
**Purpose:** Controlled retirement of legacy execution ownership
**Last Updated:** 2026-02-17
---

# Subsession Plan: V2.7 Legacy Decommission

## 1. Scope and Outcome
Retire legacy orchestration ownership for migrated workflows and validate stability in a post-disable observation window.

Outcome:
- Legacy ownership paths removed for migrated workflows.
- No orphan triggers remain.
- Post-disable stability confirmed.
- G7 evidence complete.

## 2. Entry Conditions
- [ ] G6 approved
- [ ] Runtime ownership stable across core and secondary workflows
- [ ] Compatibility alias policy active

## 3. Legacy Decommission Inventory
Use this table as authoritative tracker.

| Legacy Owner Path | Runtime Replacement | Disable Method | Disable Date | Rollback Availability | Status |
|---|---|---|---|---|---|
| `backend/app/tasks/scheduler.py` core job ownership | Runtime workflow triggers | Feature flag + scheduler disable |  | required until G7 | [ ] |
| `backend/app/worker.py` migrated wrappers ownership | Runtime executor + adapters | Queue routing switch |  | required until G7 | [ ] |
| Route-triggered legacy ownership paths | `/admin/runtime/*` controls | Endpoint behavior deprecation |  | alias window only | [ ] |

## 4. Work Package V2.7.1: Final Ownership Audit
### Checklist
- [ ] Confirm each migrated workflow has runtime owner only
- [ ] Confirm no active legacy owner remains for migrated flows
- [ ] Confirm required temporary aliases are explicitly documented

## 5. Work Package V2.7.2: Controlled Disable Sequence
### Checklist
- [ ] Disable legacy scheduler ownership for migrated domains
- [ ] Disable obsolete route-trigger ownership paths
- [ ] Keep only approved compatibility aliases
- [ ] Verify runtime ownership remains healthy after each disable step

## 6. Work Package V2.7.3: Cleanup and Regression Validation
### Checklist
- [ ] Remove/quarantine obsolete wrappers and references
- [ ] Validate no orphan scheduled jobs remain
- [ ] Execute regression suite for impacted runtime and product paths
- [ ] Update architecture and runbook docs to final ownership model

## 7. Work Package V2.7.4: 14-Day Observation Window
### Checklist
- [ ] Track reliability and backlog daily
- [ ] Track dead-letter/replay trend stability daily
- [ ] Track incident counts and classify decommission-related defects
- [ ] Escalate immediately on systemic regression indicators

## 8. Risk Register (V2.7)
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| Hidden dependency on legacy owner | Unexpected execution gap after disable | Stepwise disable + ownership audit checks | Platform Lead |
| Orphan scheduling | Jobs still enqueued from stale path | Orphan trigger scan and queue audit | DevOps Lead |
| Incomplete cleanup | Residual code/config causing operator confusion | Quarantine list + documentation sync | Runtime Lead |

## 9. Evidence Pack
- [ ] Final decommission inventory with statuses
- [ ] Disable sequence logs
- [ ] Orphan trigger scan results
- [ ] 14-day observation scorecards

## 10. Exit Criteria
- [ ] Legacy ownership removed for migrated workflows
- [ ] No orphan legacy triggers
- [ ] 14-day stability window passed
- [ ] G7 approved

## 11. Sign-Off Template
- Phase: V2.7
- Gate: G7
- Date:
- Platform Lead:
- Runtime Lead:
- DevOps Lead:
- QA Lead:
- Evidence Bundle Location:
- Decision:
- Follow-up Actions:
