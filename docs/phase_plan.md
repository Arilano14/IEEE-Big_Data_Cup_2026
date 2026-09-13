# AuditAI BI — Comprehensive Phase Plan (Phase 0 to Phase 12)

---

### 1. Phase Governance & Execution Principles

1. **Non-Overlapping Boundary Rule**: No phase may silently execute, modify, or repair work assigned to another phase.
2. **Stop-and-Rollback Rule**: If an upstream defect is discovered during a downstream phase, execution immediately halts, and the state rolls back to the responsible origin phase.
3. **Evidence-First Gate System**: Advancement to the subsequent phase requires 100% of defined acceptance criteria to be validated with objective evidence (automated test results, file checksums, or formal documents).

---

### 2. Detailed Phase Specifications (P0 to P12)

#### Phase 0: Project Charter & Scope Lock
* **Purpose**: Establish and lock the project charter, architecture blueprint, scope boundaries, and acceptance gates.
* **Inputs**: Workspace reconnaissance, challenge problem statement.
* **Deliverables**: Formal documentation in `docs/` (`project_charter.md`, `scope.md`, `data_scope.md`, `architecture.md`, `evaluation_plan.md`, `research_questions.md`, `phase_plan.md`, `phase_0_gate.md`).
* **Allowed Work**: Read-only workspace inspection, drafting planning documents.
* **Forbidden Work**: Source code writing, package installation, dataset download, database creation.
* **Acceptance Criteria**: 100% checklist satisfaction; explicit human approval.
* **Failure Condition**: Unresolved scope contradictions or unverified assumptions treated as facts.
* **Rollback Destination**: N/A (Phase 0).

#### Phase 1: Source Reconnaissance & Ingestion Architecture
* **Purpose**: Build public SEC EDGAR ingestion pipeline and establish immutable raw bronze caching.
* **Inputs**: SEC EDGAR API endpoints, target CIK list (5 diverse S&P 500 registrants).
* **Deliverables**: Ingestion module (`src/ingestion/`), raw bronze cache (`data/bronze/`) with SHA-256 integrity logs.
* **Allowed Work**: Network requests to public APIs, local disk caching, data profiling scripts.
* **Forbidden Work**: Database schema design, validation logic, Power BI model creation.
* **Acceptance Criteria**: 100% of target filings downloaded without HTTP errors; SHA-256 hashes generated; SEC rate limit (10 req/s) strictly enforced.
* **Rollback Destination**: Phase 0.

#### Phase 2: Data Contract & Canonical Model
* **Purpose**: Parse and normalize raw bronze JSON facts into relational, strongly typed silver tables.
* **Inputs**: Raw JSON cache from Phase 1.
* **Deliverables**: Canonical schemas, normalization pipeline (`src/canonical/`), clean Parquet silver tables (`data/silver/`).
* **Allowed Work**: Data type casting, ISO date parsing, surrogate key generation (`UUIDv5`), schema assertions.
* **Forbidden Work**: Executing audit validation rules, computing error deltas, UI design.
* **Acceptance Criteria**: Zero unhandled parsing errors; primary key uniqueness verified; 100% schema contract compliance.
* **Rollback Destination**: Phase 1.

#### Phase 3: Validation & Reconciliation Engine
* **Purpose**: Implement pure, deterministic accounting validation rules (Tier 1 Core: Balance Invariance, Rollups, Extraction).
* **Inputs**: Canonical silver tables from Phase 2.
* **Deliverables**: Validation engine module (`src/validation/`), automated test suite (`tests/test_validation_rules.py`).
* **Allowed Work**: Pure mathematical rule logic, deterministic assertion functions, unit testing.
* **Forbidden Work**: Severity scoring, warehouse ETL, Power BI DAX.
* **Acceptance Criteria**: 100% test pass rate across `pytest` rule suite; deterministic outputs confirmed across duplicate runs.
* **Rollback Destination**: Phase 2.

#### Phase 4: Exception Intelligence Layer
* **Purpose**: Score, classify, and prioritize discrepancies produced by the validation engine.
* **Inputs**: Raw validation outcomes from Phase 3.
* **Deliverables**: Exception classification engine (`src/exceptions/`), structured exception events (`FactAuditException`).
* **Allowed Work**: Mathematical delta calculation, percentage error computation, severity scoring algorithms.
* **Forbidden Work**: Modifying underlying validation outcomes, building dashboards.
* **Acceptance Criteria**: Zero unclassified exceptions; all error deltas mathematically reconcile with input facts.
* **Rollback Destination**: Phase 3.

#### Phase 5: Evidence & Provenance Layer
* **Purpose**: Guarantee 100% unbroken lineage from each audit exception back to the original statutory filing.
* **Inputs**: Exception records from Phase 4; raw bronze metadata from Phase 1.
* **Deliverables**: Provenance mapping module (`src/provenance/`), provenance graph dataset, audit trail validator.
* **Allowed Work**: Lineage graph generation, URL mapping to official SEC EDGAR disclosures.
* **Forbidden Work**: Modifying exception details, data cleaning.
* **Acceptance Criteria**: Provenance Traceability Rate = 100% on all `HIGH` and `CRITICAL` exceptions.
* **Rollback Destination**: Phase 4.

#### Phase 6: Evaluation & Benchmarking
* **Purpose**: Quantitatively evaluate precision, recall, and false alarm rates using control filings and synthetic perturbation error injection.
* **Inputs**: Validation engine (P3), exception engine (P4), compliant control filings (Tier B), perturbation suite (Tier D).
* **Deliverables**: Perturbation injection harness, benchmark report (`docs/benchmark_report.md`), confusion matrices.
* **Allowed Work**: Error injection, metric calculation, statistical logging.
* **Forbidden Work**: Modifying validation rules to artificially overfit evaluation sets.
* **Acceptance Criteria**: Precision $\ge 95\%$, Recall $\ge 90\%$, Clean Set False Positive Rate $< 1.0\%$.
* **Rollback Destination**: Phase 3 (if rules fail) or Phase 4 (if scoring is flawed).

#### Phase 7: Analytical Warehouse Layer
* **Purpose**: Construct the gold dimensional star schema for high-performance BI queries.
* **Inputs**: Silver facts (P2), exceptions (P4), provenance links (P5).
* **Deliverables**: Star schema tables (`data/gold/`), warehouse pipeline (`src/warehouse/`), DuckDB analytical database file.
* **Allowed Work**: Dimensional data modeling, star schema view generation, columnar indexing.
* **Forbidden Work**: Calculating new exceptions, altering raw financial values.
* **Acceptance Criteria**: Zero orphan foreign keys; star schema queries execute in $< 500\text{ms}$.
* **Rollback Destination**: Phase 2 (schema defect) or Phase 5 (provenance defect).

#### Phase 8: Power BI Semantic Layer & Dashboard
* **Purpose**: Design the enterprise Power BI data model, DAX measures, and interactive forensic audit dashboards.
* **Inputs**: Star schema warehouse from Phase 7.
* **Deliverables**: Power BI report template (`powerbi/audit_intelligence.pbit`), DAX measure library, visual screenshots.
* **Allowed Work**: DAX development, UI visual layout, drill-through paths, audit triage UX.
* **Forbidden Work**: Data cleaning in Power Query that bypasses the validation engine.
* **Acceptance Criteria**: Interactive drill-through functional; DAX measures reconcile 100% with warehouse aggregates.
* **Rollback Destination**: Phase 7.

#### Phase 9: Research Experiments & Empirical Analysis
* **Purpose**: Execute empirical investigations to answer core research questions (RQ1 and RQ2).
* **Inputs**: Verified processed filing cohorts across diverse sectors.
* **Deliverables**: Empirical research report, publication-quality distribution tables and figures.
* **Allowed Work**: Statistical aggregation, hypothesis testing, cross-statement error correlation.
* **Forbidden Work**: Modifying engine logic to force desired experimental outcomes.
* **Acceptance Criteria**: Statistical significance tests completed; empirical distribution documented with exact sample counts.
* **Rollback Destination**: Phase 6.

#### Phase 10: Reproducibility & Automation Suite
* **Purpose**: Package the entire platform for push-button execution and verifiable reproduction.
* **Inputs**: Codebase across all completed phases.
* **Deliverables**: Unified execution runner (`run_pipeline.py`), locked environment (`uv.lock`), automated verification scripts.
* **Allowed Work**: Script consolidation, configuration management, CLI interface building.
* **Forbidden Work**: Adding new unverified features.
* **Acceptance Criteria**: Clean reproduction from scratch in a fresh virtual environment in $< 10$ minutes.
* **Rollback Destination**: Phase 9.

#### Phase 11: Competition Integration & Submission
* **Purpose**: Adapt system outputs to official IEEE Big Data Cup FinReason Task 3 submission formats.
* **Inputs**: Pipeline outputs; official Task 3 submission specifications (Tier A).
* **Deliverables**: Formatted competition submission payload, validation check log.
* **Allowed Work**: Schema mapping, payload serialization, submission verification.
* **Forbidden Work**: Altering core analytical logic.
* **Acceptance Criteria**: Submission payload passes official competition format validator without error.
* **Rollback Destination**: Phase 10.

#### Phase 12: Portfolio Packaging & Demonstration
* **Purpose**: Polish documentation, executive architecture overviews, and demonstration assets for public showcase.
* **Inputs**: Completed platform, benchmark results, Power BI dashboards.
* **Deliverables**: Public-facing `README.md`, architectural diagrams, demonstration video walkthrough script.
* **Allowed Work**: Technical documentation, media creation, repository organization.
* **Forbidden Work**: Modifying tested application code.
* **Acceptance Criteria**: Peer-review-ready repository structure with clear installation and usage guides.
* **Rollback Destination**: Phase 11.

---

### 3. Dependency Graph & Rollback Paths

```
[ P0: Charter & Scope Lock ]
            │
            ▼
[ P1: Source Reconnaissance ] ──(Fail)──► [ Rollback to P0 ]
            │
            ▼
[ P2: Canonical Data Model ] ──(Fail)──► [ Rollback to P1 ]
            │
            ▼
[ P3: Validation Engine ] ──────(Fail)──► [ Rollback to P2 ]
            │
            ▼
[ P4: Exception Intelligence ] ─(Fail)──► [ Rollback to P3 ]
            │
            ▼
[ P5: Evidence & Provenance ] ──(Fail)──► [ Rollback to P4 ]
            │
            ▼
[ P6: Evaluation & Benchmark ] ─(Fail)──► [ Rollback to P3/P4 ]
            │
            ▼
[ P7: Data Warehouse Layer ] ───(Fail)──► [ Rollback to P2/P5 ]
            │
            ▼
[ P8: Power BI Dashboard ] ─────(Fail)──► [ Rollback to P7 ]
            │
            ▼
[ P9: Research Experiments ] ───(Fail)──► [ Rollback to P6 ]
            │
            ▼
[ P10: Reproducibility Suite ] ─(Fail)──► [ Rollback to P9 ]
            │
            ▼
[ P11: Challenge Submission ] ──(Fail)──► [ Rollback to P10 ]
            │
            ▼
[ P12: Portfolio Packaging ] ───(Fail)──► [ Rollback to P11 ]
```
