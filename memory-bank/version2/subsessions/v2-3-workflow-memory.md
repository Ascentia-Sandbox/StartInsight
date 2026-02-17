---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Executing V2.3 workflow and memory orchestration
**Dependencies:** `memory-bank/version2/implementation-plan-v2.md`, `memory-bank/version2/architecture-v2.md`
**Purpose:** Detailed workflow-router and memory-scope implementation track
**Last Updated:** 2026-02-17
---

# Subsession Plan: V2.3 Workflow Router and Memory

## 1. Scope and Outcome
Implement deterministic workflow orchestration, scoped memory persistence, checkpoint/resume, and workflow-level observability.

Outcome:
- Workflow registry with core and secondary templates.
- Transition engine with explicit valid/invalid state moves.
- Memory manager integrated into workflow runtime context.
- Checkpoint/resume behavior validated.
- Gate G3 evidence complete.

## 2. Entry Conditions
- [ ] G2 approved
- [ ] Primary adapters available
- [ ] Runtime command execution stable

## 3. Workflow Templates (Locked)
### Core template: `workflow.insight_core_pipeline`
1. collect_signals
2. analyze_signal
3. enrich_research
4. quality_review
5. publish_or_hold
6. notify

### Secondary templates
- `workflow.research_automation`
- `workflow.content_automation`
- `workflow.intel_automation`
- `workflow.digest_automation`

## 4. Work Package V2.3.1: Workflow Registry
### Checklist
- [ ] Define workflow definition schema
- [ ] Implement registry loader and validation
- [ ] Register core template
- [ ] Register secondary templates
- [ ] Add startup validation checks

### Deliverables
- [ ] Workflow registry specification

### Evidence
- [ ] Workflow schema validation tests

## 5. Work Package V2.3.2: Transition Engine
### Transition Rules Table
| Current | Allowed Next | Disallowed Examples |
|---|---|---|
| pending | active | completed |
| active | blocked, partial, completed, failed_terminal | pending |
| blocked | active, failed_terminal | completed |
| partial | active, failed_terminal, completed | pending |
| failed_terminal | replay_active | active |
| replay_active | active, failed_terminal | pending |

### Checklist
- [ ] Implement legal transition enforcement
- [ ] Reject illegal transitions with structured errors
- [ ] Persist transition events and timestamps
- [ ] Add transition unit tests

## 6. Work Package V2.3.3: Memory Scope Integration
### Memory policy matrix
| Scope | Key Pattern | TTL | Version Rule | Typical Writers |
|---|---|---|---|---|
| run_scope | workflow_run_id | workflow lifetime + retention | monotonic increment | workflow router, handlers |
| agent_scope | agent_name + domain key | policy-configured | optimistic version check | adapter handlers |
| user_scope | user_id + context key | policy-configured | optimistic version check | chat/research adapters |

### Checklist
- [ ] Implement read/write for run_scope
- [ ] Implement read/write for agent_scope
- [ ] Implement read/write for user_scope
- [ ] Enforce version conflict handling
- [ ] Enforce TTL and expiration behavior

## 7. Work Package V2.3.4: Checkpoint and Resume
### Invariants
1. Resume never replays already completed step effects.
2. Resume always starts from last durable checkpoint.
3. Duplicate resume requests resolve idempotently.

### Checklist
- [ ] Persist checkpoint at every step boundary
- [ ] Implement resume from checkpoint
- [ ] Implement duplicate-prevention guards
- [ ] Add integration tests for mid-workflow failure and resume

## 8. Work Package V2.3.5: Workflow Observability
### Checklist
- [ ] Emit workflow start event
- [ ] Emit step transition event
- [ ] Emit blocked/partial/failed/completed events
- [ ] Add workflow trace detail endpoint
- [ ] Add per-step latency metrics

### Deliverables
- [ ] Workflow event schema reference

### Evidence
- [ ] Workflow event stream samples

## 9. Work Package V2.3.6: Failure and Replay Validation
### Checklist
- [ ] Simulate transient failure in mid-step
- [ ] Simulate deterministic terminal failure
- [ ] Validate dead-letter handoff for terminal path
- [ ] Validate replay restores continuity

### Evidence
- [ ] Failure/replay test report

## 10. Risk Register (V2.3)
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| Step duplication on resume | Checkpoint race or duplicate resume call | Idempotent checkpoint keys + replay guards | Runtime Lead |
| Memory contamination | Scope misuse between runs | Scope key partitioning + schema checks | QA Lead |
| Transition drift | Illegal transitions accepted | Transition table tests + guard rails | Platform Lead |

## 11. Exit Criteria
- [ ] Workflow registry and transition engine operational
- [ ] Memory scopes integrated with versioning/TTL
- [ ] Checkpoint/resume validated
- [ ] Workflow observability complete
- [ ] G3 approved

## 12. Sign-Off Template
- Phase: V2.3
- Gate: G3
- Date:
- Runtime Lead:
- Platform Lead:
- QA Lead:
- Evidence Bundle Location:
- Decision:
- Follow-up Actions:
