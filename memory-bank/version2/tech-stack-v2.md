---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Dependency selection, runtime rollout decisions, and SRE/cost review
**Dependencies:** `memory-bank/version2/project-brief-v2.md`, `memory-bank/version2/architecture-v2.md`, `memory-bank/version2/implementation-plan-v2.md`
**Purpose:** Authoritative V2 stack baseline and migration technology standards
**Last Updated:** 2026-02-17
---

# Tech Stack V2: StartInsight OpenClaw Runtime Stack

## 1. Technology Posture Matrix
| Layer | Current (V1) | Transitional (V2) | Target (V2 Stable) |
|---|---|---|---|
| Product API | FastAPI | FastAPI + runtime adapters | FastAPI + runtime adapters |
| Runtime engine | Mixed APScheduler + Arq + wrappers | OpenClaw + compatibility shims | OpenClaw as canonical execution engine |
| Agent execution | Direct invocation patterns | Adapter-mediated invocation | Adapter-mediated invocation |
| Queue/cache | Redis | Redis (legacy + runtime queues) | Redis runtime queues + replay queues |
| Persistence | Supabase/PostgreSQL | + runtime tables | runtime tables + projection/audit layers |
| Frontend | Next.js | No structural platform change | No structural platform change |
| Observability | Mixed logs/SSE/metrics | Runtime lifecycle events added | Runtime-first event and metric model |

## 2. Locked Dependency Decision
V2 will use **direct OpenClaw dependency**.

### Dependency policy
1. Pin OpenClaw to a vetted version range in backend dependency lock.
2. Introduce StartInsight adapter layer to isolate app contracts from upstream API shifts.
3. Maintain compatibility test suite against pinned OpenClaw version.
4. Keep emergency fallback option:
- temporary freeze on upgrades
- optional internal vendor/fork path if upstream breaking changes block critical fixes

## 3. Backend Application Stack (Preserved + Extended)
### Preserved core
- FastAPI + Uvicorn
- Pydantic v2
- SQLAlchemy async + Alembic
- Supabase/PostgreSQL
- Redis

### V2 extension
- `backend/app/runtime/` package for OpenClaw integration and runtime contracts
- Runtime admin API namespace (`/admin/runtime/*`)
- Runtime persistence tables and event stream

## 4. Frontend Stack (No Major Rewrite)
### Preserved
- Next.js App Router
- TypeScript
- Tailwind + shadcn/ui
- Existing charts and admin pages

### V2 additions
- Consume runtime telemetry and runtime events in admin operations views
- Preserve public route behavior and existing authenticated workflows

## 5. Runtime Integration Stack
## 5.1 OpenClaw integration boundary
- OpenClaw handles core command/workflow execution semantics.
- StartInsight adapters translate existing agent/service contracts into runtime envelopes.

## 5.2 Runtime modules required
- dispatcher
- executor
- workflow router
- policy evaluator
- memory manager
- event publisher
- handler adapters
- dead-letter/replay manager

## 5.3 Compatibility design
- Runtime is additive during migration.
- Existing product APIs remain stable.
- Legacy ownership is removed only after gated parity and stability milestones.

## 6. Data and Storage
### Source of truth
- Supabase/PostgreSQL remains authoritative data store.

### New runtime tables
- `runtime_commands`
- `runtime_command_attempts`
- `runtime_workflow_runs`
- `runtime_memory_snapshots`
- `runtime_dead_letters`

### Existing table role in V2
- `agent_execution_logs`: retained for admin/audit projection and historical continuity.
- `agent_configurations`: policy/scheduling metadata source for runtime controls.

## 7. Configuration Model
### Existing config retained
- DB/Redis credentials
- auth and security secrets
- provider API keys
- monitoring integrations

### New runtime environment keys
| Key | Purpose | Default | Notes |
|---|---|---|---|
| `RUNTIME_ENABLED` | Enable runtime path | `false` | Production rollout by gate |
| `RUNTIME_SHADOW_MODE` | Non-authoritative dual-run | `true` | Used in V2.4 parity phase |
| `RUNTIME_OPENCLAW_VERSION` | Runtime engine version pin reference | required | Must match lockfile |
| `RUNTIME_MAX_CONCURRENCY` | Executor parallelism cap | conservative per env | Tune in V2.8 |
| `RUNTIME_POLICY_PROFILE_DEFAULT` | Fallback profile | `standard_async` | Can be overridden per command |
| `RUNTIME_REPLAY_ENABLED` | Allow replay actions | `false` initially | Enable with ops controls |
| `RUNTIME_DEAD_LETTER_THRESHOLD` | Attempt threshold for dead-letter | profile-based | Must be documented by profile |
| `RUNTIME_EVENT_SSE_ENABLED` | Runtime event streaming | `true` | Admin-only endpoint |

### Configuration governance
1. Every runtime key must have default, allowed range, and production override guidance.
2. Runtime config changes require rollout note and rollback note.
3. No runtime key change in production without audit trail.

## 8. AI Provider and Cost Strategy
### Provider routing
- Primary: Gemini family.
- Secondary fallback: Claude/OpenAI based on policy and failure class.

### Cost controls
- Command-level token and cost capture mandatory.
- Workflow-level cost aggregation mandatory.
- Retry budget and cost cap enforcement per policy profile.

### Cost alerting
- Budget threshold breach by workflow.
- Retry-cost anomalies.
- Provider failure-induced fallback spikes.

## 9. Observability and SRE Stack
### Required runtime telemetry
- Command lifecycle events and timings.
- Workflow step transitions.
- Attempt-level error class and retry history.
- Dead-letter and replay metrics.
- Token/cost attribution events.

### SLI/SLO targets
- Workflow reliability: >99.0%
- Command trace coverage: 100%
- MTTR improvement: >=50%

### Alert thresholds
- Reliability below 99% sustained window.
- Dead-letter growth above policy threshold.
- Replay failure spikes.
- Queue backlog growth above concurrency budget.

## 10. Security and Compliance
1. Runtime mutation endpoints are admin-authorized.
2. Runtime actions are audited with actor identity and trace id.
3. Replay operations require idempotency safeguards.
4. Request-size and rate protections remain enforced.

## 11. Testing and Quality Gates
### Existing suites retained
- Backend pytest
- Frontend Playwright

### New V2 suites
- Runtime unit tests (contracts, policy, state transitions)
- Runtime integration tests (dispatch/execute/persist/event)
- Adapter contract tests per agent family
- Dual-run parity tests
- Cutover and rollback drill tests

### Gate policy
No phase cutover if parity, rollback, or regression gates are failing.

## 12. CI/CD and Release Governance
1. Add runtime test job and parity comparator checks to CI.
2. Enforce migration safety checks for runtime schema updates.
3. Require gate evidence artifact bundle for each release phase.
4. Keep feature-flag rollback path available until V2.7 completion.

## 13. Dependency Governance
1. Major version pinning for critical runtime dependencies.
2. Scheduled monthly patch/minor updates after compatibility validation.
3. Emergency security updates prioritized with expedited validation.
4. Any new runtime dependency requires:
- rationale
- blast radius analysis
- rollback/fallback strategy

## 14. Deprecation Policy
### Deprecate after migration gates
- Legacy scheduler ownership for migrated workflows.
- Duplicated admin control behavior outside runtime API namespace.

### Retain
- Product route contracts.
- Existing domain business logic and models.

## 15. Acceptance Criteria for Tech Stack V2
1. OpenClaw dependency strategy is explicit and enforceable.
2. Runtime env keys are documented and operable.
3. Observability and cost governance are technically supported end-to-end.
4. CI and release governance can block unsafe cutovers.

## 16. Document Control
- **Owner:** Platform Engineering + DevOps
- **Review Cadence:** Bi-weekly during migration, monthly afterward
- **Related Docs:**
  - `memory-bank/version2/project-brief-v2.md`
  - `memory-bank/version2/architecture-v2.md`
  - `memory-bank/version2/implementation-plan-v2.md`
