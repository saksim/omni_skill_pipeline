# Omni Skill Pipeline Full Assessment Report

> Assessor: glm-5.1 | Date: 2026-04-22
> Revision basis: verified against the current repository source, tests, CI, and operations docs.

## 1. Project Overview

This is a **multi-modal knowledge distillation pipeline** (v0.2.0) whose core mission is to distill text, audio, image, video, and tabular/time-series input into reusable, traceable, and evolvable `SKILL.md` skill artifacts. The project follows a Hexagonal + Provider/Fallback architecture with ~70+ Python source files and 22 test files.

---

## 2. Architecture Assessment (7.5/10)

### Strengths

- **Clean layer separation**: Models → Adapters → Providers → Extraction → Assembly → Quality → Service → Repository, well-defined responsibility boundaries
- **Protocol-based interface design**: Uses `@runtime_checkable` Protocol for `DistillAdapter`, `InsightExtractor`, `SkillComposer`, etc., enabling easy replacement and testing
- **Robust Fallback mechanism**: External Providers (OpenAI, Tesseract, FFmpeg) all have fallback chains; `ProviderUnavailableError` handled gracefully
- **Clear V2 evolution path**: Roadmap progresses E0→E13 in order; Phase 5→7 landed (Quality Gate, Review Policy, Feedback)

### Issues

- **`service.py` bears too many responsibilities** (432 lines): orchestration, corpus loading, publication harmonization, review plumbing, and dependency construction are still concentrated in one module. Should extract factory and orchestration boundaries first.
- **Model layer remains overweight**: `models.py` at 715 lines carries both stable domain objects and transition helpers. `ReviewTask._build_revision_suggestions` still contains hard-coded reason→suggestion mapping that belongs behind config or strategy.
- **No repository abstraction interface**: `FileArtifactRepository` is directly constructed and used by `DistillationService` without an `ArtifactRepository` Protocol. E8 (PostgreSQL) migration will require major service-layer changes

---

## 3. Code Quality Assessment (7.2/10)

### Strengths

- Complete type annotations; `dataclass(slots=True)` used properly
- All enums are `str, Enum` for serialization friendliness
- Unified `to_dict()`/`to_json()` serialization
- Clean error hierarchy: `OmniSkillPipelineError` → `ProviderUnavailableError`/`ProviderExecutionError`/`MediaProcessingError`

### Issues

- **Implicit coupling**: `service.py:build_service()` is a monolithic factory function hard-coding all provider assembly logic. Dependency injection should be more granular
- **Entry-point coverage is still uneven**: core multimodal flows are covered, but API-layer validation and HTTP contract tests are still missing.
- **`pipeline.py` heuristic keywords are all hard-coded** (`DECISION_KEYWORDS`, `ANTI_KEYWORDS`, etc.), with Chinese keywords mixed into English logic; should be made configurable
- **Some methods too long**: `repository.py:save_bundle()` ~80 lines, `service.py:_distill()` ~50 lines; should be split
- **`api_app.py` lacks request model validation**: Uses bare `dict` for payload; no Pydantic model validation, weak type safety

---

## 4. Data Model Assessment (8/10)

### Strengths

- V2 model system is complete: `EvidenceNode` (spatio-temporal positioning), `SemanticAtom` (semantic atoms), `SkillGraph` (graph-structured skill), `Publication` (multi-view publishing), `ReviewTask` (review task), `LifecycleDecision` (lifecycle)
- `SkillGraph.validate()` has reasonable completeness checks
- JSON Schema (`schema.py`) stays in sync with dataclasses
- `Corpus` supports multi-asset joint distillation

### Issues

- **Runtime is still dual-path during transition**: the roadmap is clear that `SkillGraph` should become the truth source, but current compatibility rendering still depends on `SkillDocument` as an output bridge.
- **`EvidenceUnit` and `EvidenceNode` overlap**: Both coexist in `DistillBundle`; understandable for transition period but migration timeline needs clarity
- **Enums lack `__str__`**: Printing enums in logs/errors shows `Modality.TEXT` instead of `text`

---

## 5. Quality Gate Assessment (7.5/10)

### Strengths

- 6-dimension scoring system complete: traceability, actionability, coverage, consistency, noise, novelty
- Review Policy three-tier decisions: `auto_publish`/`review_required`/`reject` with configurable thresholds
- Review Feedback Engine maps reason codes to structured remediation actions (atom_actions, graph_actions, policy_actions, follow_up_checks)
- All review results persisted alongside bundle

### Issues

- **Scoring is entirely heuristic**: `QualityScorer` uses hard-coded weights and simple heuristics; no ML or statistical model backing. `_novelty()` token-density detection is too crude
- **Thresholds are hard-coded constants**: `ReviewPolicyThresholds` defaults have no data-driven calibration. Acceptable for initial period, but needs real data validation
- **Lack of scoring interpretability**: Quality scores are only numeric; no per-dimension breakdown explanation (though `diagnostics` field exists, it only records counts)
- **Feedback actions are declarative, not executable**: `ATOM_REMOVE_NOISY`, `GRAPH_DOWNWEIGHT_NOISY_EVIDENCE`, etc. are not consumed by any automated pipeline

---

## 6. Security & Operations Assessment (5.5/10)

### Strengths

- Environment variables are documented in `docs/current/operations/env.md`; configuration is not hidden only in source.
- Video jobs clean up per-run temporary work directories in a `finally` block, so the temp-file problem is a shared scratch-root retention issue rather than a per-request leak.

### Issues (Key Focus Area)

- **`OPENAI_API_KEY` via environment variable**: Config directly reads `os.getenv('OPENAI_API_KEY')` with no dedicated secrets management or redaction mechanism
- **No API authentication**: `api_app.py` has no API key, JWT, or any authentication middleware
- **No rate limiting**: API calls to OpenAI have no retry/throttle/circuit breaker protection
- **Temp governance is only partial**: per-job work directories are cleaned, but the shared `.tmp_omni_media/` scratch root has no retention/prune strategy
- **No structured logging**: No logging configuration across the project; no trace ID, no call chain tracing
- **Hard-coded Python interpreter path in README** (`D:\code_environment\anaconda_all_css\py311\python.exe`), should not appear in documentation
- **No `.env.example`**: environment variables are documented, but first-run bootstrap is still manual

---

## 7. Testing Assessment (7.5/10)

### Strengths

- 22 test files covering major V2 feature modules
- CI configuration complete (GitHub Actions, Python 3.11, pip cache)
- Has `scripts/run_ci.py` and `scripts/run_tp_tests.py` (TP=Task Package)
- `test_mvp.py` covers text, audio, image, video, and tabular main-path distillation flows
- `test_v2_schema_and_corpus.py` directly covers `load_corpus()` / `distill_corpus()` and verifies review/publication persistence

### Issues

- **No dedicated API-layer tests**: there are no FastAPI/ASGI tests for request validation, status codes, or response contracts
- **Real provider boundary behavior is still thin in CI**: fake providers cover main paths, but actual OpenAI/FFmpeg/Tesseract failure modes are only lightly exercised
- **No performance benchmarks**: E11 planned `TP-E11-04` but not yet implemented
- **No coverage target**: No minimum coverage gate configured

---

## 8. Documentation Assessment (8/10)

### Strengths

- Documentation system is extremely thorough: ARCHITECTURE → System Overview → Data Flow → Providers → Storage → V2 Design → Roadmap → Implementation Backlog → Work Orders → Contracts → Operations
- All design docs have clear "判词" (one-sentence core viewpoint)
- Roadmap divided into 7 phases with risks and control strategies
- Implementation backlog broken down to Task Package level with file targets, acceptance criteria, and prohibitions
- JSON Schema synchronized with code
- API and environment documentation are present in `docs/current/operations/`

### Issues

- Some docs contain Windows hard-coded absolute paths (`D:\download\...`), not portable
- Status document `CURRENT_STATUS.md` may be outdated (not reviewed)
- API docs cover endpoints and payload examples, but still lack explicit auth, error contract, and operational limit guidance

---

## 9. Key Risks & Recommendations

| # | Risk | Severity | Recommendation |
|---|------|----------|----------------|
| 1 | `service.py` and repository wiring are over-coupled; E8+ migration will be painful | High | Introduce `ArtifactRepository` Protocol, then extract factory/orchestration boundaries |
| 2 | API surface has no auth, no request models, and no rate limiting | High | Add API key middleware, Pydantic request models, and throttling/resilience guards |
| 3 | No structured logging or trace context | High | Pull logging/trace work forward before externalizing the API further |
| 4 | Quality scoring is purely heuristic, no data calibration | Medium | Collect real distillation sample scores and tune thresholds against reviewed samples |
| 5 | Review feedback is not executable | Medium | Implement a feedback consumer or at least automated tagging/queueing |
| 6 | Temp governance is only partial | Medium | Add scratch-root retention/prune rules and operational cleanup guidance |
| 7 | Docs remain Windows-centric and bootstrap is manual | Medium | Remove hard-coded interpreter paths and add portable setup guidance plus `.env.example` |
| 8 | API layer lacks automated tests | Medium | Add FastAPI `TestClient` or ASGI integration tests for the public endpoints |

---

## 10. Overall Score Summary

| Dimension | Score | Notes |
|-----------|-------|-------|
| Architecture Design | 7.5/10 | Modular direction is right; service/repository boundary is still the bottleneck |
| Code Quality | 7.2/10 | Strong typing and serialization discipline; factory/config and API validation need work |
| Data Model | 8/10 | V2 model system is real and useful; transition debt remains |
| Quality Gate | 7.5/10 | Review framework is implemented, but calibration and automation are still immature |
| Security & Ops | 5.5/10 | Weakest area; auth, logging, and provider resilience are not yet hardened |
| Testing | 7.5/10 | Main-path multimodal coverage is stronger than a superficial read suggests; API/perf gaps remain |
| Documentation | 8/10 | Strong system design docs; portability and ops contract detail still lag |
| **Overall** | **7.3/10** | Engineering foundation is solid; biggest debt is operational hardening plus service-layer decoupling |

---

## 11. Conclusion

The project is stronger than the original draft implied in **testing** and **documentation**, and weaker exactly where it matters most for externalization: **API hardening, observability, and service/repository decoupling**. The design vision is credible, the V2 migration path is materially implemented, and the main-path multimodal pipeline is already test-backed. The next serious work should prioritize API protection, structured logging/traceability, and repository abstraction before pushing further into E8/PostgreSQL or broader external exposure.
