---
**Memory Bank Protocol**
**Reading Priority:** HIGH
**Read When:** At the start of V2 execution, executive alignment, and roadmap replanning
**Dependencies:** `memory-bank/version2/architecture-v2.md`, `memory-bank/version2/tech-stack-v2.md`, `memory-bank/version2/implementation-plan-v2.md`
**Purpose:** V2 mission, business outcomes, scope boundaries, KPI targets, and governance
**Last Updated:** 2026-02-17
---

# Project Brief V2: StartInsight Runtime Reliability Program

## 1. Executive Decision (Locked)
StartInsight V2 will adopt **direct OpenClaw dependency** as the backend AI-agent runtime foundation.

V2 is a runtime replatform program. It is not a product rewrite. Existing user-facing behavior and product APIs remain stable while execution ownership migrates from mixed scheduler/task flows to a single command/workflow runtime control plane.

## 2. Why V2 Exists
Current backend execution ownership is split across:
- APScheduler-based triggers in `backend/app/tasks/scheduler.py`
- Arq worker functions and cron jobs in `backend/app/worker.py`
- Route-triggered and service-triggered execution paths in `backend/app/api/routes/` and `backend/app/services/`

This split model creates inconsistent retry, timeout, lineage, and replay behavior. V2 fixes this by centralizing execution on OpenClaw with StartInsight adapters.

## 3. Program Objectives
1. **Runtime Canonicalization**
Move all agent execution to one command/workflow model with explicit state transitions.

2. **Operational Reliability**
Standardize retry, timeout, dead-letter, and replay semantics across all workflows.

3. **Forensics and Observability**
Guarantee end-to-end traceability from trigger to final persisted outcome.

4. **Cost Governance**
Track LLM usage and cost at command and workflow granularity.

5. **Safe Migration**
Migrate through dual-run parity gates with reversible cutover and tested rollback.

## 4. Current Baseline (V1)
### Runtime and orchestration baseline
- AI agents: `backend/app/agents/` (chat, enhanced analyzer, research, competitive intel, market intel, content generator, quality reviewer, market insight publisher)
- Scheduler: `backend/app/tasks/scheduler.py`
- Worker and cron ownership: `backend/app/worker.py`
- Admin control surface: `backend/app/api/routes/agent_control.py`

### Key operational weaknesses
- Execution ownership is fragmented.
- Policy handling is path-specific rather than runtime-wide.
- Replay/dead-letter behavior is not uniformly managed.
- Incident triage requires joining multiple logs and code paths.

## 5. Scope and Boundaries
### In scope
- Direct OpenClaw runtime integration.
- New runtime contracts and persistence for commands, attempts, workflows, memory, dead letters.
- Runtime adapter layer for all existing core agents.
- Dual-run parity validation, gated cutover, rollback readiness, and legacy decommission.
- Admin runtime control and telemetry unification.

### Out of scope
- Major frontend redesign.
- Domain-logic rewrite for existing agent intelligence prompts.
- Product pricing/package redesign.
- Unrelated feature expansion outside runtime reliability goals.

## 6. Success Metrics (Locked)
| Category | Metric | Baseline Capture | Target | Owner |
|---|---|---|---|---|
| Reliability | Workflow completion reliability | Capture from V1 30-day production window | >99.0% | Runtime Lead |
| Reliability | Replay success for eligible dead letters | Capture from V1 incident/retry logs | >=95% | Platform + Ops |
| Observability | Runtime command trace coverage | Baseline expected partial | 100% | DevOps Lead |
| Incident Ops | MTTR | Capture from last 20 Sev-2/Sev-3 incidents | >=50% improvement | Ops Lead |
| Cost | LLM cost attribution coverage | Partial in V1 | 100% command/workflow coverage | Platform + Finance Ops |
| Efficiency | Reprocessing overhead from partial failures | Capture from pipeline reruns | >=40% reduction | Runtime Lead |

## 7. Stakeholder Impact
### End users
- No breaking route or API behavior during migration.
- More consistent freshness and reduced partial-output failures.

### Admin and operators
- Single runtime control model for trigger, monitor, retry, and replay.
- Faster root-cause analysis through command/workflow lineage.

### Engineering
- Standard adapter contract for integrating or modifying agents.
- Reduced execution path drift and lower operational complexity.

## 8. Risks, Triggers, and Mitigations
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| OpenClaw upstream drift | Breaking changes in upstream release | Version pinning, compatibility adapter, emergency freeze, optional vendored fork path | Platform Lead |
| Retry storm cost spike | Rapid growth in retries and token spend | Policy caps, backoff controls, attempt budgets, kill switches | Runtime Lead |
| Dual-control-plane confusion | Operators using mixed legacy/runtime controls during migration | Canonical runtime admin APIs, compatibility aliases, explicit deprecation schedule | Ops Lead |
| Migration regressions | Parity drift, user-visible freshness or quality drops | Dual-run gates, phased cutover, rollback drill before production switch | QA Lead |
| Data contract drift between adapters | Adapter outputs diverge by agent family | Mandatory contract tests and adapter conformance matrix | Runtime Lead |

## 9. Governance Model
### Program owners
- **Platform Lead:** architecture decisions, cutover authority.
- **Runtime Lead:** OpenClaw integration, runtime engine behavior.
- **DevOps Lead:** SLOs, observability, incident operations.
- **QA Lead:** parity and non-regression gate sign-off.

### Cadence
- Daily execution updates during active migration phases.
- Weekly architecture and risk review.
- Formal go/no-go records per gate (G0 through G8).

### Decision protocol
- No phase advances without gate evidence.
- Any Sev-1 runtime incident during cutover windows requires formal rollback evaluation.

## 10. Constraints (Non-Negotiable)
1. Product-facing API compatibility is preserved during migration.
2. Rollback path must remain runnable until V2.7 decommission gate passes.
3. Runtime mutation endpoints remain admin-authorized.
4. All runtime state transitions are persisted and auditable.
5. All V2 phase gates require test evidence and metric snapshots.

## 11. Assumptions and Defaults
1. OpenClaw can be integrated without forcing product API redesign.
2. Existing agent logic remains mostly intact and is wrapped by adapters.
3. Supabase/PostgreSQL remains source of truth.
4. Redis remains queue/cache substrate for runtime dispatch and replay.
5. Feature flags control shadow, cutover, and rollback ownership.

## 12. Program Deliverables
1. OpenClaw-backed runtime package and adapter layer.
2. Runtime persistence model and migration scripts.
3. Runtime admin API and event stream.
4. Parity, cutover, rollback, and decommission runbooks.
5. Final closeout report with 30-day SLO sustainment evidence.

## 13. Linked Execution Documents
- Master execution: `memory-bank/version2/implementation-plan-v2.md`
- Target design: `memory-bank/version2/architecture-v2.md`
- Stack and ops policy: `memory-bank/version2/tech-stack-v2.md`
- Deep work tracks: `memory-bank/version2/subsessions/`

## 14. Document Control
- **Owner:** Platform + AI Runtime Team
- **Review Cadence:** Weekly during migration, bi-weekly after stabilization
- **Change Policy:** Any KPI/scope/gate update requires synchronized edits in architecture, tech stack, and implementation plan docs
