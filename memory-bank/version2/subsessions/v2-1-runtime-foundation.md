---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Executing V2.1 runtime foundation
**Dependencies:** `memory-bank/version2/implementation-plan-v2.md`, `memory-bank/version2/architecture-v2.md`, `memory-bank/version2/tech-stack-v2.md`
**Purpose:** Detailed execution track for V2.1 runtime foundation with OpenClaw integration
**Last Updated:** 2026-02-17
---

# Subsession Plan: V2.1 Runtime Foundation

## 1. Scope and Outcome
Build the foundational runtime layer that integrates OpenClaw directly and establishes StartInsight's canonical command/workflow execution stack.

Target outcome:
- Runtime dependency integrated and pinned.
- Runtime package and schema in place.
- Command lifecycle, policy engine, executor, memory manager implemented.
- Admin read APIs and SSE event stream available.
- Gate G1 evidence complete.

## 2. Entry Conditions
- [ ] G0 approved (contracts, taxonomy, policy defaults frozen)
- [ ] Runtime dependency strategy approved (direct OpenClaw + pinned version)
- [ ] Baseline metrics and rollback criteria documented

## 3. Preflight Checks
- [ ] Confirm baseline execution owners from `backend/app/tasks/scheduler.py`
- [ ] Confirm worker task inventory from `backend/app/worker.py`
- [ ] Confirm primary agent set in `backend/app/agents/`
- [ ] Confirm runtime table names and key contracts from architecture doc

---

## 4. Work Package V2.1.1: OpenClaw Dependency Integration
### Objective
Install and operationalize direct OpenClaw dependency behind a stable runtime adapter boundary.

### Implementation Checklist
- [ ] Add OpenClaw dependency with locked/pinned version strategy
- [ ] Add runtime version metadata config (`RUNTIME_OPENCLAW_VERSION`)
- [ ] Create `backend/app/runtime/openclaw_adapter.py`
- [ ] Implement OpenClaw bootstrap initialization function
- [ ] Implement no-op smoke execution path for adapter validation
- [ ] Document upstream breakage fallback (freeze or vendor path)

### Deliverables
- [ ] Dependency lock entry and runtime dependency notes
- [ ] `openclaw_adapter.py` baseline implementation

### Evidence
- [ ] OpenClaw bootstrap test output
- [ ] Version pin evidence in dependency manifest/lock

---

## 5. Work Package V2.1.2: Runtime Package Scaffold
### Objective
Create all runtime modules and enforce boundary hygiene.

### Implementation Checklist
- [ ] Create `backend/app/runtime/__init__.py`
- [ ] Create `backend/app/runtime/contracts.py`
- [ ] Create `backend/app/runtime/dispatcher.py`
- [ ] Create `backend/app/runtime/executor.py`
- [ ] Create `backend/app/runtime/policies.py`
- [ ] Create `backend/app/runtime/workflow_router.py`
- [ ] Create `backend/app/runtime/memory.py`
- [ ] Create `backend/app/runtime/events.py`
- [ ] Create `backend/app/runtime/handlers/__init__.py`
- [ ] Add runtime exception hierarchy (validation, transition, policy, execution)
- [ ] Add logging and trace conventions in module docs

### Deliverables
- [ ] Runtime package tree
- [ ] Runtime module import map

### Evidence
- [ ] Import smoke test output
- [ ] Circular dependency check output

---

## 6. Work Package V2.1.3: Runtime Schema Migrations
### Objective
Introduce persistent runtime state model in PostgreSQL/Supabase.

### Implementation Checklist
- [ ] Add migration: `runtime_commands`
- [ ] Add migration: `runtime_command_attempts`
- [ ] Add migration: `runtime_workflow_runs`
- [ ] Add migration: `runtime_memory_snapshots`
- [ ] Add migration: `runtime_dead_letters`
- [ ] Add foreign key constraints for command-attempt-workflow links
- [ ] Add indexes for status, type, created_at, workflow linkage
- [ ] Add retention/TTL metadata fields for memory/dead-letter rows
- [ ] Define idempotency uniqueness constraint strategy

### Deliverables
- [ ] Alembic migration scripts
- [ ] Schema verification query pack

### Evidence
- [ ] Local upgrade log
- [ ] Staging upgrade log
- [ ] Downgrade/upgrade dry-run output

---

## 7. Work Package V2.1.4: Command Intake and Idempotency
### Objective
Provide deterministic command creation and dedup behavior.

### Implementation Checklist
- [ ] Validate inbound command payload against runtime contract
- [ ] Enforce idempotency key checks
- [ ] Return deterministic existing-command reference on duplicates
- [ ] Persist command metadata and creation timestamp
- [ ] Persist command context (`trigger_source`, actor metadata)
- [ ] Emit command-created event

### Deliverables
- [ ] Intake path in dispatcher
- [ ] Idempotency conflict policy

### Evidence
- [ ] Duplicate submission integration test output
- [ ] Contract validation test output

---

## 8. Work Package V2.1.5: Command State Transition Engine
### Objective
Enforce legal lifecycle transitions with auditable persistence.

### Implementation Checklist
- [ ] Implement legal transition map
- [ ] Reject illegal transitions with structured error
- [ ] Persist every transition with timestamp and actor/source
- [ ] Persist attempt counters and latest error class/message
- [ ] Emit lifecycle event per transition

### Deliverables
- [ ] Transition map implementation
- [ ] Transition guard unit tests

### Evidence
- [ ] Valid transition test output
- [ ] Invalid transition rejection test output

---

## 9. Work Package V2.1.6: Policy Engine Baseline
### Objective
Centralize retry/backoff/timeout/dead-letter behavior.

### Implementation Checklist
- [ ] Implement policy profiles: `critical_path`, `standard_async`, `best_effort`, `manual_review`
- [ ] Map runtime error classes to retry eligibility
- [ ] Implement backoff function and attempt caps
- [ ] Implement timeout budgets per profile
- [ ] Implement dead-letter threshold logic
- [ ] Implement replay eligibility rules

### Deliverables
- [ ] Policy evaluator module
- [ ] Profile matrix documentation

### Evidence
- [ ] Retry/backoff tests
- [ ] Timeout/dead-letter routing tests

---

## 10. Work Package V2.1.7: Executor Loop
### Objective
Execute queued commands with atomic attempts and robust shutdown behavior.

### Implementation Checklist
- [ ] Implement queue polling/dequeue lock behavior
- [ ] Implement atomic attempt start persistence
- [ ] Execute mapped handler adapter and capture outcomes
- [ ] Persist attempt completion and command final state
- [ ] Handle transient dependency failures with policy integration
- [ ] Implement graceful shutdown semantics for in-flight commands

### Deliverables
- [ ] Executor loop implementation
- [ ] Graceful shutdown handling

### Evidence
- [ ] Success/failure/retry integration tests
- [ ] Graceful shutdown test output

---

## 11. Work Package V2.1.8: Runtime Memory Manager
### Objective
Implement scoped runtime memory with versioning and TTL.

### Implementation Checklist
- [ ] Implement `run_scope` read/write
- [ ] Implement `agent_scope` read/write
- [ ] Implement `user_scope` read/write where applicable
- [ ] Implement optimistic version checks
- [ ] Implement TTL validation and expiration behavior

### Deliverables
- [ ] Memory manager module
- [ ] Scope policy notes

### Evidence
- [ ] Memory scope CRUD tests
- [ ] Version conflict tests

---

## 12. Work Package V2.1.9: Runtime Admin Read APIs
### Objective
Expose runtime command/workflow visibility to admin operators.

### Implementation Checklist
- [ ] Add `GET /admin/runtime/commands/{id}`
- [ ] Add `GET /admin/runtime/commands`
- [ ] Add `GET /admin/runtime/workflows/{id}`
- [ ] Add list filters for status/type/workflow id/time range
- [ ] Add pagination and sorting controls
- [ ] Add admin authz checks and audit markers

### Deliverables
- [ ] Runtime read API surface

### Evidence
- [ ] Endpoint auth tests
- [ ] Filtering and pagination tests

---

## 13. Work Package V2.1.10: Runtime Event Stream
### Objective
Stream runtime lifecycle events for operational monitoring.

### Implementation Checklist
- [ ] Add event publication for command lifecycle
- [ ] Add event publication for workflow lifecycle
- [ ] Add `GET /admin/runtime/events` SSE endpoint
- [ ] Implement heartbeat and client disconnect handling
- [ ] Implement event schema version marker

### Deliverables
- [ ] Runtime event stream endpoint
- [ ] Event payload schema reference

### Evidence
- [ ] SSE connection tests
- [ ] Event sequencing validation output

---

## 14. Work Package V2.1.11: Test Harness and CI Integration
### Objective
Enforce continuous runtime validation in pipeline.

### Implementation Checklist
- [ ] Add runtime unit test suite
- [ ] Add runtime integration test suite
- [ ] Add schema migration safety tests
- [ ] Add contract conformance checks in CI
- [ ] Add runtime gate artifacts collection in CI

### Deliverables
- [ ] CI runtime job definitions

### Evidence
- [ ] CI pipeline run with runtime jobs passing

---

## 15. Work Package V2.1.12: Gate G1 Review and Closeout
### Objective
Complete phase handoff with formal evidence.

### Checklist
- [ ] Compile V2.1 implementation report
- [ ] Attach all required evidence items
- [ ] Run architecture/runtime/ops/QA sign-off
- [ ] Record G1 decision (approved/rejected/conditional)

## 16. Risk Register (V2.1)
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| OpenClaw bootstrap instability | Runtime initialization failures | Compatibility smoke tests + pinned version | Runtime Lead |
| Schema drift | Migration mismatch across environments | Mandatory local/staging migration validation | Platform Lead |
| Transition logic defects | Illegal state transitions in execution path | Guard tests + transition map audits | QA Lead |
| SSE event overload | High event throughput causing stream instability | Backpressure strategy + heartbeat monitoring | DevOps Lead |

## 17. Exit Criteria
- [ ] OpenClaw integration stable and pinned
- [ ] Runtime package scaffold complete
- [ ] Runtime schema migrated and validated
- [ ] Command/policy/executor/memory/read API/event stream operational
- [ ] Runtime tests and CI integration green
- [ ] G1 approved

## 18. Sign-Off Template
- Phase: V2.1
- Gate: G1
- Date:
- Runtime Lead:
- Platform Lead:
- DevOps Lead:
- QA Lead:
- Evidence Bundle Location:
- Decision:
- Follow-up Actions:
