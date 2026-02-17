---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Executing V2.2 adapter migration
**Dependencies:** `memory-bank/version2/implementation-plan-v2.md`, `memory-bank/version2/architecture-v2.md`
**Purpose:** Detailed adapter migration plan for all primary agent families
**Last Updated:** 2026-02-17
---

# Subsession Plan: V2.2 Agent Handler Adapters

## 1. Scope and Outcome
Standardize runtime adapters for every primary agent path so all AI execution conforms to the same command/policy/error/memory contracts.

Outcome:
- Every agent path in `backend/app/agents/` has a runtime adapter.
- Adapter contracts and tests are complete.
- Retry/timeout/dead-letter behavior is normalized.
- Gate G2 evidence is complete.

## 2. Entry Conditions
- [ ] G1 approved
- [ ] Runtime contracts and policy profiles finalized
- [ ] Runtime executor path validated

## 3. Adapter Matrix (Locked)
| Agent / Path | Runtime Command Type | Input Envelope | Output Envelope | Error Class Mapping | Policy Profile |
|---|---|---|---|---|---|
| `enhanced_analyzer.py` | `insight.analyze_enhanced` | raw signal id + content refs | insight payload + persistence refs | provider_timeout, validation_error, dependency_error | `critical_path` |
| `research_agent.py` | `research.generate_report` | insight id + user context refs | research report payload | timeout, quota, validation_error | `standard_async` |
| `chat_agent.py` | `chat.respond` | session id + prompt + mode | assistant response + token usage | timeout, provider_error, bad_request | `standard_async` |
| `content_generator_agent.py` | `content.generate_assets` | insight/report refs | generated content assets | provider_timeout, validation_error | `standard_async` |
| `competitive_intel_agent.py` | `intel.competitive_analyze` | insight id + competitor refs | competitor analysis payload | scrape_dependency_error, validation_error | `standard_async` |
| `market_intel_agent.py` | `intel.market_report` | trends + insight refs | market report payload | provider_timeout, validation_error | `best_effort` |
| `market_insight_publisher.py` | `market.publish_insight` | curated source refs | publication payload + ids | persistence_error, validation_error | `critical_path` |
| `quality_reviewer.py` | `quality.review` / `quality.audit` | content refs + quality thresholds | quality decisions + metrics | validation_error, dependency_error | `manual_review` |

## 4. Work Package V2.2.1: Adapter Interface Freeze
### Checklist
- [ ] Define adapter registration mechanism
- [ ] Define required adapter input envelope
- [ ] Define required adapter output envelope
- [ ] Define required adapter error envelope
- [ ] Define required telemetry fields (latency, tokens, cost)

### Deliverables
- [ ] Adapter interface spec

### Evidence
- [ ] Interface contract tests

## 5. Work Package V2.2.2: Analyzer Adapter
### Checklist
- [ ] Wrap enhanced analyzer execution in runtime adapter
- [ ] Preserve persistence behavior parity
- [ ] Map analyzer failures to runtime error classes
- [ ] Attach analyzer telemetry fields

### Evidence
- [ ] Analyzer adapter happy/failure/retry tests

## 6. Work Package V2.2.3: Research and Chat Adapters
### Checklist
- [ ] Implement research adapter
- [ ] Implement chat adapter
- [ ] Map user context into runtime memory refs
- [ ] Validate timeout behavior under policy profile

### Evidence
- [ ] Research/chat adapter tests

## 7. Work Package V2.2.4: Content and Intelligence Adapters
### Checklist
- [ ] Implement content generator adapter
- [ ] Implement competitive intel adapter
- [ ] Implement market intel adapter
- [ ] Verify cross-adapter schema compatibility

### Evidence
- [ ] Content/intelligence adapter tests

## 8. Work Package V2.2.5: Publisher and Reviewer Adapters
### Checklist
- [ ] Implement market insight publisher adapter
- [ ] Implement quality review adapter
- [ ] Implement quality audit adapter
- [ ] Validate manual-review policy behavior

### Evidence
- [ ] Publisher/reviewer adapter tests

## 9. Work Package V2.2.6: Error Normalization and Policy Mapping
### Checklist
- [ ] Define transient vs terminal classes per adapter
- [ ] Validate retry eligibility mapping
- [ ] Validate timeout mapping
- [ ] Validate dead-letter routing mapping

### Evidence
- [ ] Error-class mapping report
- [ ] Retry/dead-letter conformance tests

## 10. Work Package V2.2.7: Adapter Contract Test Matrix
### Required test scenarios (every adapter)
- [ ] Success path
- [ ] Deterministic validation failure
- [ ] Transient dependency/provider failure
- [ ] Timeout and retry behavior
- [ ] Idempotent replay behavior

### Deliverables
- [ ] Adapter test matrix report
- [ ] Adapter compatibility matrix

## 11. Risk Register (V2.2)
| Risk | Trigger | Mitigation | Owner |
|---|---|---|---|
| Adapter drift | One adapter diverges from canonical contracts | Shared contract fixtures + contract CI gate | Runtime Lead |
| Hidden persistence coupling | Adapter changes domain write behavior | Parity persistence assertions | Platform Lead |
| Error misclassification | Wrong retry/dead-letter routing | Explicit mapping tests per adapter | QA Lead |

## 12. Exit Criteria
- [ ] All primary agent families wrapped
- [ ] Contract tests pass for all adapters
- [ ] Error/policy behavior normalized
- [ ] G2 approved

## 13. Sign-Off Template
- Phase: V2.2
- Gate: G2
- Date:
- Runtime Lead:
- Platform Lead:
- QA Lead:
- Evidence Bundle Location:
- Decision:
- Follow-up Actions:
