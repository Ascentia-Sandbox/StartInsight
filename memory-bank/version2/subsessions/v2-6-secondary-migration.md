---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Executing V2.6 secondary workflow migration and admin unification
**Dependencies:** `memory-bank/version2/implementation-plan-v2.md`, `memory-bank/version2/architecture-v2.md`
**Purpose:** Detailed migration plan for non-core workflows and canonical admin controls
**Last Updated:** 2026-02-17
---

# Subsession Plan: V2.6 Secondary Workflow Migration and Admin Unification

## 1. Scope and Outcome
Migrate secondary workflows to runtime and consolidate admin operations onto canonical runtime APIs.

Outcome:
- Secondary workflows are runtime-owned.
- Admin controls are unified under `/admin/runtime/*` with temporary aliases.
- Operational runbooks and training are complete.
- G6 evidence complete.

## 2. Entry Conditions
- [ ] G5 approved
- [ ] Core runtime ownership stable
- [ ] Admin runtime telemetry available

## 3. Secondary Workflow Migration Order (Locked)
1. Research automation
2. Content generation automation
3. Competitive/market intelligence automation
4. Digest and auxiliary automation

## 4. Work Package V2.6.1: Per-Workflow Migration Planning
### Checklist
- [ ] Define workflow-specific migration windows
- [ ] Define workflow-specific validation checks
- [ ] Define workflow-specific rollback triggers
- [ ] Assign migration owner per workflow

## 5. Work Package V2.6.2: Secondary Cutover Execution
### Checklist
- [ ] Migrate research workflows
- [ ] Migrate content workflows
- [ ] Migrate competitive intel workflows
- [ ] Migrate market intel workflows
- [ ] Migrate digest/aux workflows
- [ ] Validate post-cutover metrics per workflow

## 6. Work Package V2.6.3: Admin API Canonicalization
### Canonical endpoints
- [ ] `POST /admin/runtime/commands`
- [ ] `GET /admin/runtime/commands/{id}`
- [ ] `GET /admin/runtime/commands`
- [ ] `POST /admin/runtime/workflows/{name}/trigger`
- [ ] `GET /admin/runtime/workflows/{id}`
- [ ] `POST /admin/runtime/dead-letters/{id}/replay`
- [ ] `GET /admin/runtime/events`

### Compatibility aliases
- [ ] Define alias mapping for one release cycle
- [ ] Add deprecation notes and timeline
- [ ] Add removal criteria for alias retirement

## 7. Work Package V2.6.4: Admin UI Telemetry Alignment
### Checklist
- [ ] Repoint admin views to runtime telemetry sources
- [ ] Add dead-letter/replay operations screens
- [ ] Validate sort/filter/pagination behavior under runtime datasets
- [ ] Validate operator workflows end-to-end

## 8. Work Package V2.6.5: Operational Readiness
### Checklist
- [ ] Update runbooks and SOPs
- [ ] Deliver operator/admin enablement session
- [ ] Validate incident response flow using runtime-only controls

## 9. Risk Register (V2.6)
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| Mixed admin behavior | Legacy controls still used by ops | Canonical endpoint policy + deprecation enforcement | Ops Lead |
| Secondary workflow regressions | Individual domain cutover failures | Per-workflow rollback checks | Runtime Lead |
| UI/telemetry mismatch | Admin pages assume old fields | Contracted runtime telemetry adapters | Frontend + Platform |

## 10. Evidence Pack
- [ ] Workflow-by-workflow migration logs
- [ ] Admin API alias/deprecation mapping
- [ ] Updated runbook and training records
- [ ] Post-migration stability snapshots

## 11. Exit Criteria
- [ ] All secondary workflows runtime-owned
- [ ] Canonical runtime admin controls adopted
- [ ] Compatibility alias plan active and documented
- [ ] G6 approved

## 12. Sign-Off Template
- Phase: V2.6
- Gate: G6
- Date:
- Runtime Lead:
- Ops Lead:
- QA Lead:
- Evidence Bundle Location:
- Decision:
- Follow-up Actions:
