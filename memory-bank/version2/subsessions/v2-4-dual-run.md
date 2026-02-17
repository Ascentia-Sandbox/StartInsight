---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Executing V2.4 dual-run parity validation
**Dependencies:** `memory-bank/version2/implementation-plan-v2.md`, `memory-bank/version2/architecture-v2.md`
**Purpose:** Production-grade dual-run shadow validation and parity governance
**Last Updated:** 2026-02-17
---

# Subsession Plan: V2.4 Dual-Run Shadow Validation

## 1. Scope and Outcome
Run runtime and legacy execution in parallel for 7 days, measure parity, and validate cutover readiness.

Outcome:
- Runtime shadow mode stable.
- Variance calculations and dashboard operational.
- Divergences triaged and remediated.
- G4 pass/fail decision evidence complete.

## 2. Entry Conditions
- [ ] G3 approved
- [ ] Core workflows executable in runtime mode
- [ ] Shadow feature flags and kill-switch available

## 3. Parity Framework (Locked)
### Comparison dimensions
- output count
- failure rate
- quality pass rate
- latency distribution (supporting diagnostic metric)

### Variance formulas
- Output variance % = `abs(runtime_count - legacy_count) / max(legacy_count,1) * 100`
- Failure-rate variance % = `abs(runtime_fail_rate - legacy_fail_rate) * 100`
- Quality variance % = `abs(runtime_quality_rate - legacy_quality_rate) * 100`

### Gate thresholds
- Output count variance <=2%
- Failure-rate variance <=1%
- Quality pass-rate variance <=1%

## 4. Work Package V2.4.1: Shadow Controls
### Checklist
- [ ] Enable `RUNTIME_SHADOW_MODE`
- [ ] Ensure runtime writes are non-authoritative in shadow path
- [ ] Implement emergency kill-switch
- [ ] Validate safe disable behavior during incident

## 5. Work Package V2.4.2: Parity Data Collection
### Checklist
- [ ] Capture runtime and legacy workflow outcomes by correlation key
- [ ] Normalize timestamps and identifiers
- [ ] Persist daily parity snapshots
- [ ] Preserve unmatched-run diagnostics

## 6. Work Package V2.4.3: Variance Reporting
### Checklist
- [ ] Implement daily variance calculation job
- [ ] Expose parity dashboard endpoint/view
- [ ] Add alert rules for threshold breaches
- [ ] Add variance drill-down for root-cause tagging

## 7. Work Package V2.4.4: Daily Operations Runbook
### Daily review responsibilities
- Runtime Lead: investigate runtime-side deltas
- QA Lead: verify statistical validity and threshold breaches
- Ops Lead: classify operational impact and escalation level

### Checklist
- [ ] Review previous 24h variance report
- [ ] Classify divergence severity (minor, major, blocker)
- [ ] Assign remediation owner and SLA
- [ ] Update divergence tracker

## 8. Work Package V2.4.5: 7-Day Parity Window
### Checklist
- [ ] Run shadow continuously for 7 days
- [ ] Resolve all blocker divergences
- [ ] Re-run impacted workflows where needed for validation
- [ ] Produce final parity summary and recommendation

## 9. Evidence Pack (Required)
- [ ] 7 daily variance snapshots
- [ ] Divergence tracker with root causes and resolutions
- [ ] Threshold compliance report
- [ ] Cutover readiness recommendation

## 10. Risk Register (V2.4)
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| False variance alerts | Inconsistent normalization keys | Fixed correlation key schema + data QA checks | QA Lead |
| Hidden behavioral drift | Aggregate variance looks acceptable but edge cases fail | Mandatory drill-down and sampling | Runtime Lead |
| Shadow overload | Increased load affects production stability | Concurrency caps and immediate kill-switch | DevOps Lead |

## 11. Exit Criteria
- [ ] All parity thresholds within limits
- [ ] Blocker divergences remediated
- [ ] Cutover readiness report accepted
- [ ] G4 approved

## 12. Sign-Off Template
- Phase: V2.4
- Gate: G4
- Date:
- Runtime Lead:
- QA Lead:
- Ops Lead:
- Evidence Bundle Location:
- Decision:
- Follow-up Actions:
