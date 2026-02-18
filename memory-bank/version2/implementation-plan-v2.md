---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** During execution of V2 runtime migration and release governance
**Dependencies:** `memory-bank/version2/project-brief-v2.md`, `memory-bank/version2/architecture-v2.md`, `memory-bank/version2/tech-stack-v2.md`, `memory-bank/implementation-plan.md`
**Purpose:** Detailed, checkbox-driven implementation plan for V2 runtime replatform
**Last Updated:** 2026-02-17
---

# Implementation Plan V2: StartInsight OpenClaw Runtime Replatform

## 1. Executive Summary
This plan migrates StartInsight backend execution ownership from mixed scheduler/worker patterns to a direct OpenClaw-based runtime control plane.

The program is designed to be:
- **non-breaking** for product APIs
- **reversible** during migration
- **evidence-driven** through formal gates
- **operationally strict** with SLO, cost, and incident controls

Program targets:
- Workflow reliability: **>99.0%**
- Command trace coverage: **100%**
- MTTR improvement: **>=50%**
- Replay success for eligible dead letters: **>=95%**

## 2. Baseline Inventory (Codebase-Verified)
Current execution ownership is distributed across:
- Scheduler ownership: `backend/app/tasks/scheduler.py`
- Worker task wrappers and cron: `backend/app/worker.py`
- Agent implementations: `backend/app/agents/`
- Admin control APIs: `backend/app/api/routes/agent_control.py`
- Service-triggered orchestration: `backend/app/services/pipeline_orchestrator.py` and related service paths

## 3. Program Scope
### In scope
- Direct OpenClaw integration and runtime package creation.
- Runtime contract and persistence model.
- Adapter-based migration of all primary agent families.
- Workflow/memory model, checkpoint/resume, replay/dead-letter.
- Dual-run parity, controlled cutover, legacy decommission.
- Runtime admin API and telemetry unification.

### Out of scope
- Major frontend UX redesign.
- Core business-logic rewrite of agent intelligence behavior.
- Pricing/packaging redesign.

## 4. Phase and Gate Map
| Phase | Title | Gate | Status |
|---|---|---|---|
| V2.0 | Program Setup and Contract Freeze | G0 | [ ] Not Started |
| V2.1 | Runtime Foundation | G1 | [ ] Not Started |
| V2.2 | Agent Handler Adapters | G2 | [ ] Not Started |
| V2.3 | Workflow Router and Memory | G3 | [ ] Not Started |
| V2.4 | Dual-Run Shadow Validation | G4 | [ ] Not Started |
| V2.5 | Core Loop Cutover | G5 | [ ] Not Started |
| V2.6 | Secondary Migration + Admin Unification | G6 | [ ] Not Started |
| V2.7 | Legacy Decommission | G7 | [ ] Not Started |
| V2.8 | Hardening and Cost Optimization | G8 | [ ] Not Started |

## 5. Gate Criteria (Hard)
- **G0:** contracts, taxonomy, and policy defaults approved.
- **G1:** runtime core, schema, API read path, and event stream validated.
- **G2:** all primary adapters pass contract tests.
- **G3:** workflow transitions and memory checkpoint/resume validated.
- **G4:** 7-day parity thresholds pass.
- **G5:** 14-day core cutover stability passes.
- **G6:** secondary workflows migrated and admin controls unified.
- **G7:** legacy ownership removed with 2-week post-disable stability.
- **G8:** 30-day sustainment and optimization targets achieved.

## 6. Evidence Requirements (Every Phase)
- [ ] Checklist completion report
- [ ] Test run summary with pass/fail counts
- [ ] Metrics snapshot against phase targets
- [ ] Risk register updates
- [ ] Gate decision record (approved/rejected/conditional)

---

## 7. Phase V2.0: Program Setup and Contract Freeze

### V2.0.1 Execution ownership inventory
- [ ] Enumerate all scheduler-owned jobs from `backend/app/tasks/scheduler.py`
- [ ] Enumerate all worker tasks and cron jobs from `backend/app/worker.py`
- [ ] Enumerate route-triggered execution paths in `backend/app/api/routes/`
- [ ] Enumerate service-triggered orchestration paths in `backend/app/services/`
- [ ] Map every path to target runtime command type and workflow

Deliverables:
- [ ] Execution inventory matrix
- [ ] Ownership conflict list

### V2.0.2 Runtime taxonomy freeze
- [ ] Define canonical command types
- [ ] Define canonical workflow names and step maps
- [ ] Define policy profile defaults by workflow class
- [ ] Define idempotency strategy by trigger source

Deliverables:
- [ ] Command/workflow taxonomy document

### V2.0.3 Contract baseline freeze
- [ ] Define command envelope fields
- [ ] Define attempt envelope fields
- [ ] Define workflow envelope fields
- [ ] Define memory snapshot envelope fields
- [ ] Define dead-letter envelope fields
- [ ] Define event payload schema

Deliverables:
- [ ] Contract spec v1.0

### V2.0.4 Migration safety baseline
- [ ] Define parity metrics and thresholds
- [ ] Define rollback trigger conditions
- [ ] Define runtime kill switches
- [ ] Define phase gate ownership and approvers

Deliverables:
- [ ] Migration safety policy

### V2.0.5 Baseline metric capture
- [ ] Capture 30-day reliability baseline
- [ ] Capture MTTR baseline from recent incidents
- [ ] Capture replay/retry baseline behaviors
- [ ] Capture cost attribution baseline coverage

Deliverables:
- [ ] Baseline KPI report

### V2.0.6 Gate G0 review
- [ ] Review inventory/taxonomy/contracts/policy defaults
- [ ] Confirm unresolved decision count is zero
- [ ] Record G0 decision

V2.0 Exit Criteria:
- [ ] Inventory complete
- [ ] Contracts frozen for implementation
- [ ] Policy defaults approved
- [ ] G0 approved

---

## 8. Phase V2.1: Runtime Foundation

### V2.1.1 OpenClaw dependency integration
Objective: Install and validate direct OpenClaw dependency with a stable adapter boundary.

- [ ] Add OpenClaw dependency with pinned version strategy
- [ ] Add OpenClaw version metadata configuration (`RUNTIME_OPENCLAW_VERSION`)
- [ ] Implement `backend/app/runtime/openclaw_adapter.py`
- [ ] Add compatibility smoke tests for OpenClaw initialization and no-op execution
- [ ] Define emergency fallback procedure (freeze or vendor/fork path)

Deliverables:
- [ ] Runtime dependency lock and compatibility notes

Validation:
- [ ] Runtime bootstrap tests pass
- [ ] Dependency pin and rollback procedure documented

### V2.1.2 Runtime package scaffold
Objective: Create runtime package structure and internal boundaries.

- [ ] Create `backend/app/runtime/__init__.py`
- [ ] Create `backend/app/runtime/contracts.py`
- [ ] Create `backend/app/runtime/dispatcher.py`
- [ ] Create `backend/app/runtime/executor.py`
- [ ] Create `backend/app/runtime/policies.py`
- [ ] Create `backend/app/runtime/workflow_router.py`
- [ ] Create `backend/app/runtime/memory.py`
- [ ] Create `backend/app/runtime/events.py`
- [ ] Create `backend/app/runtime/handlers/`
- [ ] Define runtime exception hierarchy
- [ ] Define runtime logging conventions and trace ids

Deliverables:
- [ ] Runtime module tree and design notes

Validation:
- [ ] Import smoke tests pass
- [ ] No circular dependency detected

### V2.1.3 Runtime schema migrations
Objective: Add runtime persistence tables and indexes.

- [ ] Create migration for `runtime_commands`
- [ ] Create migration for `runtime_command_attempts`
- [ ] Create migration for `runtime_workflow_runs`
- [ ] Create migration for `runtime_memory_snapshots`
- [ ] Create migration for `runtime_dead_letters`
- [ ] Add required foreign keys and constraints
- [ ] Add status/time/type/workflow indexes
- [ ] Add retention and TTL-related fields

Deliverables:
- [ ] Alembic migration scripts

Validation:
- [ ] Upgrade passes in local
- [ ] Upgrade passes in staging
- [ ] Downgrade/upgrade dry-run passes

### V2.1.4 Command intake and idempotency engine
Objective: Build deterministic command creation and dedup behavior.

- [ ] Implement command validation against runtime contracts
- [ ] Implement idempotency key uniqueness checks
- [ ] Implement dedup return behavior for duplicate command submissions
- [ ] Persist canonical command creation event
- [ ] Add conflict handling and error responses for malformed input

Deliverables:
- [ ] Dispatcher intake implementation

Validation:
- [ ] Idempotency tests pass
- [ ] Duplicate submission behavior is deterministic

### V2.1.5 Command state transition engine
Objective: Persist and enforce valid lifecycle transitions.

- [ ] Implement legal transition map (`queued`, `running`, `succeeded`, etc.)
- [ ] Reject illegal transitions with explicit errors
- [ ] Persist transition metadata and timestamps
- [ ] Emit transition lifecycle events

Deliverables:
- [ ] State transition engine

Validation:
- [ ] Transition unit tests pass
- [ ] Invalid transition tests pass

### V2.1.6 Policy engine minimum viable implementation
Objective: Apply common retry/timeout/dead-letter semantics.

- [ ] Implement profile classes (`critical_path`, `standard_async`, `best_effort`, `manual_review`)
- [ ] Implement retry eligibility by error class
- [ ] Implement backoff strategy and cap enforcement
- [ ] Implement timeout budget checks
- [ ] Implement dead-letter routing rules

Deliverables:
- [ ] Policy evaluator module

Validation:
- [ ] Policy tests pass
- [ ] Retry budget and dead-letter threshold tests pass

### V2.1.7 Executor loop (runtime-owned)
Objective: Execute queued commands with atomic attempt persistence.

- [ ] Implement queue polling and command locking
- [ ] Implement attempt start and completion persistence
- [ ] Implement graceful shutdown and in-flight handling
- [ ] Implement transient dependency error guards
- [ ] Implement command completion and error finalization hooks

Deliverables:
- [ ] Executor loop implementation

Validation:
- [ ] Integration tests pass for success/failure/retry paths
- [ ] Graceful shutdown test passes

### V2.1.8 Runtime memory manager baseline
Objective: Add scoped memory CRUD with versioning and TTL.

- [ ] Implement `run_scope` memory read/write
- [ ] Implement `agent_scope` memory read/write
- [ ] Implement `user_scope` memory read/write (where applicable)
- [ ] Implement version increments and conflict handling
- [ ] Implement TTL enforcement and cleanup semantics

Deliverables:
- [ ] Memory manager module

Validation:
- [ ] Memory serialization/version tests pass

### V2.1.9 Runtime admin read APIs
Objective: Expose runtime data safely to admin operators.

- [ ] Add `GET /admin/runtime/commands/{id}`
- [ ] Add `GET /admin/runtime/commands`
- [ ] Add `GET /admin/runtime/workflows/{id}`
- [ ] Add admin auth and authorization checks
- [ ] Add pagination/filtering behavior for list endpoints

Deliverables:
- [ ] Runtime read APIs

Validation:
- [ ] API tests pass (auth, filters, pagination)

### V2.1.10 Runtime event stream baseline
Objective: Emit and stream lifecycle events for operations.

- [ ] Emit command lifecycle events
- [ ] Emit workflow lifecycle events
- [ ] Add `GET /admin/runtime/events` SSE endpoint
- [ ] Implement heartbeat and disconnect handling
- [ ] Implement event schema versioning marker

Deliverables:
- [ ] Runtime event stream and schema docs

Validation:
- [ ] SSE stream tests pass
- [ ] Event ordering and payload schema tests pass

### V2.1.11 Test harness and CI integration
Objective: Ensure runtime foundation is continuously validated.

- [ ] Add runtime unit test suite in backend tests
- [ ] Add runtime integration test suite
- [ ] Add migration safety test job
- [ ] Add contract schema validation checks in CI

Deliverables:
- [ ] CI pipeline updates

Validation:
- [ ] All runtime CI jobs green

### V2.1.12 Gate G1 review
- [ ] Compile implementation report
- [ ] Attach schema/API/event/test evidence
- [ ] Record G1 decision

V2.1 Exit Criteria:
- [ ] Runtime core modules implemented
- [ ] Runtime schema and read/event APIs operational
- [ ] Runtime tests in CI green
- [ ] G1 approved

---

## 9. Phase V2.2: Agent Handler Adapters

### V2.2.1 Adapter interface freeze
- [ ] Define adapter registration mechanism
- [ ] Define adapter input envelope
- [ ] Define adapter output envelope
- [ ] Define adapter error normalization model

### V2.2.2 Analyzer-family adapter migration
- [ ] Implement enhanced analyzer adapter
- [ ] Validate persistence behavior parity
- [ ] Validate error-to-policy mapping

### V2.2.3 Research and chat adapter migration
- [ ] Implement research adapter
- [ ] Implement chat adapter
- [ ] Validate context/memory mapping for user-associated commands

### V2.2.4 Content/intelligence/publisher/reviewer adapters
- [ ] Implement content generator adapter
- [ ] Implement competitive intel adapter
- [ ] Implement market intel adapter
- [ ] Implement market insight publisher adapter
- [ ] Implement quality reviewer adapter

### V2.2.5 Adapter policy integration
- [ ] Validate retry class mapping per adapter
- [ ] Validate timeout behavior per adapter
- [ ] Validate terminal failure routing to dead letters

### V2.2.6 Contract test matrix
- [ ] Success path tests for all adapters
- [ ] Failure path tests for all adapters
- [ ] Timeout tests for all adapters
- [ ] Replay/idempotency behavior tests

### V2.2.7 Gate G2 review
- [ ] Publish adapter compatibility matrix
- [ ] Attach test evidence
- [ ] Record G2 decision

V2.2 Exit Criteria:
- [ ] All primary adapters runtime-compatible
- [ ] Contract tests pass across adapter families
- [ ] G2 approved

---

## 10. Phase V2.3: Workflow Router and Memory

### V2.3.1 Workflow registry implementation
- [ ] Define workflow schema and registry loader
- [ ] Register core insight pipeline workflow
- [ ] Register secondary workflow templates
- [ ] Validate workflow definition consistency

### V2.3.2 Transition engine
- [ ] Implement step transitions and legal route map
- [ ] Implement `blocked`, `partial`, `failed_terminal` states
- [ ] Implement per-step retry semantics

### V2.3.3 Memory scope integration
- [ ] Integrate memory scopes into workflow execution context
- [ ] Implement step boundary memory writes
- [ ] Implement scoped memory retrieval by policy and scope key

### V2.3.4 Checkpoint and resume
- [ ] Persist checkpoint at step boundaries
- [ ] Implement resume-from-checkpoint behavior
- [ ] Ensure duplicate step prevention after resume

### V2.3.5 Workflow observability
- [ ] Emit step transition events
- [ ] Add workflow trace detail endpoint
- [ ] Add per-step duration metrics

### V2.3.6 Workflow failure/replay validation
- [ ] Simulate mid-workflow failures
- [ ] Validate dead-letter step behavior
- [ ] Validate replay continuity

### V2.3.7 Gate G3 review
- [ ] Publish workflow behavior report
- [ ] Attach metrics and test evidence
- [ ] Record G3 decision

V2.3 Exit Criteria:
- [ ] Workflow orchestration and memory scopes operational
- [ ] Checkpoint/resume verified
- [ ] G3 approved

---

## 11. Phase V2.4: Dual-Run Shadow Validation

### V2.4.1 Shadow controls
- [ ] Enable runtime shadow mode flags
- [ ] Ensure runtime outputs are non-authoritative in shadow
- [ ] Implement emergency shadow kill switch

### V2.4.2 Parity collection pipeline
- [ ] Capture runtime and legacy outcomes by workflow instance
- [ ] Normalize comparison keys
- [ ] Persist daily parity snapshots

### V2.4.3 Variance reporting and alerting
- [ ] Build variance calculations
- [ ] Expose parity dashboard endpoint/view
- [ ] Configure alert thresholds for divergence

### V2.4.4 7-day parity run
- [ ] Run continuous 7-day shadow window
- [ ] Review variances daily
- [ ] Classify and remediate all blocking divergence classes

### V2.4.5 Gate G4 thresholds
- [ ] Output count variance <=2%
- [ ] Failure-rate variance <=1%
- [ ] Quality pass-rate variance <=1%
- [ ] Record G4 decision

V2.4 Exit Criteria:
- [ ] 7-day parity thresholds met
- [ ] Cutover readiness confirmed
- [ ] G4 approved

---

## 12. Phase V2.5: Core Loop Cutover

### V2.5.1 Cutover readiness
- [ ] Finalize cutover window and communication plan
- [ ] Confirm on-call and escalation coverage
- [ ] Validate rollback runbook in staging

### V2.5.2 Ownership transfer
- [ ] Enable runtime ownership flags for core workflows
- [ ] Disable legacy ownership for migrated workflows
- [ ] Verify first production runs and traces

### V2.5.3 14-day stability window
- [ ] Monitor reliability, backlog, dead letters daily
- [ ] Monitor user-visible freshness and quality signals
- [ ] Resolve incidents under change control

### V2.5.4 Rollback readiness checks
- [ ] Validate rollback switch behavior remains functional
- [ ] Preserve runtime forensic evidence capture

### V2.5.5 Gate G5 criteria
- [ ] Reliability >99% for 14 days
- [ ] No Sev-1 requiring full rollback
- [ ] Record G5 decision

V2.5 Exit Criteria:
- [ ] Core workflows runtime-owned and stable
- [ ] Rollback path validated
- [ ] G5 approved

---

## 13. Phase V2.6: Secondary Migration + Admin Unification

### V2.6.1 Secondary workflow migration planning
- [ ] Sequence secondary workflow migration order
- [ ] Assign owners and rollout windows
- [ ] Define per-workflow validation checklist

### V2.6.2 Secondary cutovers
- [ ] Migrate research automation workflows
- [ ] Migrate content generation workflows
- [ ] Migrate competitive/market intelligence workflows
- [ ] Migrate digest/auxiliary workflows

### V2.6.3 Canonical admin runtime APIs
- [ ] Implement canonical runtime control endpoint set
- [ ] Add compatibility aliases for one release cycle
- [ ] Add deprecation notice policy for old controls

### V2.6.4 Admin UI and telemetry alignment
- [ ] Point admin operations views to runtime telemetry
- [ ] Add dead-letter/replay operator views
- [ ] Validate filter/sort/pagination behavior

### V2.6.5 Gate G6 review
- [ ] Compile migration and compatibility report
- [ ] Capture operator sign-off
- [ ] Record G6 decision

V2.6 Exit Criteria:
- [ ] Secondary workflows runtime-owned
- [ ] Admin control model unified
- [ ] G6 approved

---

## 14. Phase V2.7: Legacy Decommission

### V2.7.1 Legacy ownership final inventory
- [ ] Confirm all migrated workflows no longer depend on legacy ownership
- [ ] Mark remaining temporary compatibility paths

### V2.7.2 Controlled disable sequence
- [ ] Disable legacy scheduler ownership for migrated workflows
- [ ] Disable obsolete route-trigger ownership where migrated
- [ ] Keep only required temporary compatibility aliases

### V2.7.3 Cleanup and validation
- [ ] Remove/quarantine obsolete wrappers and references
- [ ] Verify no orphan scheduled jobs remain
- [ ] Run full regression suite for impacted paths

### V2.7.4 2-week observation
- [ ] Monitor reliability and backlog for 14 days
- [ ] Monitor dead-letter/replay trend stability
- [ ] Track and classify incidents for decommission regressions

### V2.7.5 Gate G7 review
- [ ] Publish decommission report
- [ ] Record G7 decision

V2.7 Exit Criteria:
- [ ] Legacy ownership removed for migrated workflows
- [ ] 2-week post-disable stability passed
- [ ] G7 approved

---

## 15. Phase V2.8: Hardening and Cost Optimization

### V2.8.1 Policy tuning
- [ ] Tune retry/backoff by command/workflow class
- [ ] Reduce false retries and timeout misclassifications
- [ ] Tune dead-letter thresholds using production patterns

### V2.8.2 Replay optimization
- [ ] Analyze top dead-letter causes
- [ ] Improve replay path safety and success rates
- [ ] Document repeat-failure prevention controls

### V2.8.3 Cost governance hardening
- [ ] Add per-workflow cost budgets
- [ ] Add threshold alerts and escalation policy
- [ ] Optimize top-cost command paths

### V2.8.4 Observability finalization
- [ ] Finalize runtime SLO dashboards
- [ ] Validate alert routing and paging behavior
- [ ] Validate trace completeness and queryability

### V2.8.5 30-day sustainment
- [ ] Reliability >99% sustained 30 days
- [ ] Command trace coverage 100% sustained 30 days
- [ ] MTTR improvement >=50% sustained 30 days

### V2.8.6 Gate G8 review
- [ ] Publish V2 closeout package
- [ ] Record G8 decision

V2.8 Exit Criteria:
- [ ] Hardening and optimization targets met
- [ ] Sustainment period passed
- [ ] G8 approved

---

## 16. Program-Wide Test Matrix
### Unit tests
- [ ] Contract schema validation
- [ ] State transition validation
- [ ] Policy retry/timeout/backoff logic
- [ ] Memory serialization/versioning

### Integration tests
- [ ] Dispatch -> execute -> persist
- [ ] Retry/dead-letter/replay lifecycle
- [ ] Workflow step transition and resume
- [ ] Runtime API auth and filters

### System tests
- [ ] Dual-run parity execution
- [ ] Cutover drill
- [ ] Rollback drill
- [ ] Queue pressure and dependency fault injection

### Regression tests
- [ ] Existing product API behavior
- [ ] Existing quality validation gates
- [ ] Existing admin access and audit expectations

## 17. Rollback Triggers (Hard)
- [ ] Workflow reliability <97% for 2 consecutive days
- [ ] Backlog exceeds threshold for >4 hours with no recovery trend
- [ ] Dead-letter surge indicates systemic runtime defect
- [ ] User-facing freshness/quality regression confirmed runtime-induced

Rollback readiness checklist:
- [ ] Legacy ownership switch tested
- [ ] Runtime evidence preservation verified
- [ ] Incident communication templates ready

## 18. Reporting and Sign-Off Template
- Phase:
- Gate:
- Date:
- Owner:
- QA Reviewer:
- Ops Reviewer:
- Evidence Bundle Link:
- Decision:
- Follow-up Actions:

## 19. Deep Execution Tracks
- `memory-bank/version2/subsessions/v2-1-runtime-foundation.md`
- `memory-bank/version2/subsessions/v2-2-agent-adapters.md`
- `memory-bank/version2/subsessions/v2-3-workflow-memory.md`
- `memory-bank/version2/subsessions/v2-4-dual-run.md`
- `memory-bank/version2/subsessions/v2-5-cutover.md`
- `memory-bank/version2/subsessions/v2-6-secondary-migration.md`
- `memory-bank/version2/subsessions/v2-7-decommission.md`
- `memory-bank/version2/subsessions/v2-8-hardening.md`

## 20. Document Control
- **Owner:** Platform Runtime Program
- **Review Cadence:** Weekly during migration, monthly post-close
- **Reference Style Source:** `memory-bank/implementation-plan.md`
