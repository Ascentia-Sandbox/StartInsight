---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Executing V2.5 core workflow cutover
**Dependencies:** `memory-bank/version2/implementation-plan-v2.md`, `memory-bank/version2/subsessions/v2-4-dual-run.md`
**Purpose:** Operational cutover and 14-day stabilization runbook
**Last Updated:** 2026-02-17
---

# Subsession Plan: V2.5 Core Loop Cutover

## 1. Scope and Outcome
Transfer core workflow ownership from legacy to runtime with strict rollback readiness and 14-day stability validation.

Outcome:
- Core workflows are runtime-owned.
- Reliability and freshness remain within targets.
- Rollback path remains verified during stabilization.
- G5 evidence complete.

## 2. Entry Conditions
- [ ] G4 approved
- [ ] Cutover readiness report approved
- [ ] On-call and escalation matrix finalized

## 3. Cutover Command Sequence (Locked)
### T-24h
- [ ] Freeze non-critical deployment changes
- [ ] Validate runtime and legacy health checks
- [ ] Verify dashboards and alert channels

### T-60m
- [ ] Confirm shadow parity data final review
- [ ] Confirm rollback switch operational
- [ ] Confirm operator acknowledgements

### T0 (switch)
- [ ] Enable runtime ownership flags for core workflows
- [ ] Disable legacy ownership for same core workflows
- [ ] Trigger controlled canary workflow run

### T+15m
- [ ] Validate command traces and workflow outcomes
- [ ] Validate no critical dead-letter spike

### T+60m
- [ ] Validate freshness and quality indicators
- [ ] Publish cutover status update

## 4. Work Package V2.5.1: Pre-Cutover Validation
### Checklist
- [ ] Verify runtime API health and data access
- [ ] Verify queue depth and executor health
- [ ] Verify alert routing and paging
- [ ] Verify rollback runbook and comm templates

## 5. Work Package V2.5.2: Ownership Transfer
### Checklist
- [ ] Apply cutover flag sequence
- [ ] Validate legacy owner disablement for migrated core workflows
- [ ] Verify first production runtime runs
- [ ] Record initial success/failure metrics

## 6. Work Package V2.5.3: 14-Day Stability Operations
### Daily scorecard metrics
- workflow reliability
- command backlog
- dead-letter rate
- replay success rate
- user-facing freshness
- quality pass rate

### Checklist
- [ ] Run daily scorecard review
- [ ] Triage incidents under change control
- [ ] Track issue remediation SLAs
- [ ] Publish daily status summary

## 7. Work Package V2.5.4: Rollback Drill and Readiness
### Checklist
- [ ] Execute controlled rollback simulation (staging or mirrored env)
- [ ] Measure rollback recovery time
- [ ] Validate evidence capture and incident documentation
- [ ] Reconfirm production rollback command sequence

## 8. Gate Criteria (G5)
- [ ] Reliability >99% over 14 consecutive days
- [ ] No Sev-1 requiring full rollback
- [ ] Dead-letter and replay trends within policy thresholds
- [ ] User-facing freshness/quality no material degradation

## 9. Risk Register (V2.5)
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| Cutover regression | Elevated failures immediately post-switch | Immediate rollback guard + high-frequency monitoring | Ops Lead |
| Hidden freshness degradation | Metrics pass but user freshness drops | Add freshness KPI and manual sample checks | Product + Ops |
| Rollback execution error | Runbook mismatch under stress | Pre-validated rollback drill and comm scripts | DevOps Lead |

## 10. Evidence Pack
- [ ] Cutover timeline log
- [ ] Initial validation results (T+15m, T+60m)
- [ ] 14-day stability scorecards
- [ ] Rollback drill report

## 11. Exit Criteria
- [ ] Core loop runtime-owned and stable
- [ ] Rollback path validated and available
- [ ] G5 approved

## 12. Sign-Off Template
- Phase: V2.5
- Gate: G5
- Date:
- Runtime Lead:
- Ops Lead:
- QA Lead:
- Evidence Bundle Location:
- Decision:
- Follow-up Actions:
