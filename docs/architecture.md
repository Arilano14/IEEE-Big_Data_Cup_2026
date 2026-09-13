# AuditAI BI — System Architecture & Technical Specifications

---

### 1. 8-Layer Architecture Overview

AuditAI BI decouples data ingestion, normalization, deterministic verification, exception management, and business intelligence into eight strictly partitioned layers:

```
[ Layer 1: Data Source Layer ]
       │  (SEC EDGAR APIs / Official FinReason Task 3 Data)
       ▼
[ Layer 2: Raw Ingestion Layer (Bronze) ]
       │  (Immutable JSON/XML file storage + SHA-256 integrity hashes)
       ▼
[ Layer 3: Canonical Financial Layer (Silver) ]
       │  (Relational normalization: DimEntity, DimFiling, FactReportedFact)
       ▼
[ Layer 4: Validation & Reconciliation Engine ] <=== SINGLE SOURCE OF TRUTH
       │  (Deterministic accounting rules, mathematical roll-up checks)
       ▼
[ Layer 5: Exception Intelligence Layer ]
       │  (Error delta computation, severity scoring: CRITICAL to INFO)
       ▼
[ Layer 6: Evidence & Provenance Layer ]
       │  (100% Cryptographic/URI Tracing: Exception -> Rule -> Fact -> Filing)
       ▼
[ Layer 7: Analytical Warehouse Layer (Gold) ]
       │  (Star Schema: FactAuditException, FactValidationRun, DimRule)
       ▼
[ Layer 8: Power BI Semantic Layer & Executive Dashboard ]
          (DAX Measures, interactive drill-through, audit triage reports)
```

---

### 2. Layer Responsibilities & Technical Contracts

| Layer | Responsibility | Input | Output | Technology | Validation Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **L1: Source** | Expose statutory filings and APIs. | External requests | HTTP/REST payloads | SEC EDGAR / Web APIs | Operational data source |
| **L2: Raw (Bronze)** | Guarantee immutable local storage of raw disclosures. | Raw API payloads | Cached `.json`/`.xml` files + hashes | Local Filesystem / `uv` | SHA-256 checksum verification |
| **L3: Canonical (Silver)** | Normalize disclosures into typed relational tables. | Raw Bronze files | Typed Parquet tables (`silver/`) | Python / Pandas / Polars | Structural schema validation |
| **L4: Validation Engine** | Execute pure deterministic accounting verification. | Canonical facts | Rule execution results (True/False) | Pure Python / `pytest` | **SINGLE SOURCE OF TRUTH** |
| **L5: Exception Intel** | Compute mathematical deltas, percentages, and severity. | Failed validations | Structured exception records | Python / Numerical logic | Exception severity ranking |
| **L6: Provenance** | Construct immutable audit trail to statutory source. | Exception records + raw metadata | Lineage graph with SEC URLs | Python Graph Logic | 100% Provenance verification |
| **L7: Warehouse (Gold)** | Provide high-performance columnar star-schema querying. | Silver facts + Exceptions + Provenance | Gold Star Schema tables | DuckDB / Parquet | Foreign key & grain integrity |
| **L8: BI Presentation** | Provide interactive visual triage for auditors. | Star Schema tables | Power BI Dashboard (`.pbix`/`.pbit`) | Power BI Desktop (x64) | Presentation only (No logic) |

---

### 3. Single Source of Truth Mandate

**Layer 4 (Validation & Reconciliation Engine) is the sole authority on financial verification.**
* Downstream layers (Warehouse, Power BI) are strictly analytical consumers.
* Power BI DAX measures may aggregate, filter, and summarize audit exceptions, but they are strictly forbidden from altering the mathematical outcome or severity of an exception.
* If a validation rule is found to be incorrect, remediation MUST occur in Layer 4 and propagate downstream.

---

### 4. Technology Decisions & Staging

| Component | Selected Technology | Epistemic Classification | Rationale | Re-evaluation Milestone |
| :--- | :--- | :--- | :--- | :--- |
| **Core Runtime** | Python 3.10.11 | `[LOCKED]` | Host system environment confirmed. Stable ecosystem for numerical and financial engineering. | N/A |
| **Package Manager**| `uv` (v0.11.29) | `[LOCKED]` | Host system confirmed. Provides sub-second resolution and isolated `.venv` environments. | N/A |
| **BI Presentation**| Microsoft Power BI Desktop | `[LOCKED]` | Version 2.152.1279.0 confirmed installed on host machine. Industry standard for enterprise BI. | N/A |
| **Test Framework** | `pytest` | `[LOCKED]` | Standard for automated deterministic rule assertions and continuous test gates. | N/A |
| **Analytical Store**| DuckDB vs. Parquet | `[PROVISIONAL]` | DuckDB enables zero-server embedded OLAP querying, direct Parquet reading, and fast Power BI ingestion. | Phase 2 (Data Contract) |
| **Normalization** | Polars vs. Pandas | `[PROVISIONAL]` | Pandas 2.3.3 is currently installed in Python 3.10; Polars offers higher speed. | Phase 1 (Source Recon) |
| **XBRL Parser** | Custom Light JSON vs. `arelle` | `[PROVISIONAL]` | SEC EDGAR Company Facts API returns pre-parsed JSON. A heavy XML Arelle engine may add unnecessary overhead. | Phase 1 (Source Recon) |
| **Containerization**| Docker Desktop / Compose | `[OPTIONAL / DEFERRED]` | Host Docker daemon is currently inactive. Pipeline runs natively in `.venv`. | Phase 10 (Productionization) |

---

### 5. Audit Exception Data Model

Every exception produced by Layer 4 and scored by Layer 5 conforms to the following schema:

```json
{
  "exception_id": "EXC-2026-00049281",
  "rule_id": "CALC_GROSS_PROFIT_001",
  "rule_category": "CALCULATION",
  "severity": "HIGH",
  "cik": "0000320193",
  "entity_name": "Apple Inc.",
  "form": "10-K",
  "fiscal_year": 2024,
  "fiscal_period": "FY",
  "statement": "INCOME_STATEMENT",
  "target_concept": "us-gaap:GrossProfit",
  "reported_value": 170782000000.0,
  "expected_value": 170782000000.0,
  "difference": 0.0,
  "difference_pct": 0.0,
  "tolerance_applied": 1.0,
  "status": "VALID",
  "source_document": "0000320193-24-000123",
  "evidence_reference": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json#facts/us-gaap/GrossProfit",
  "timestamp": "2026-09-13T09:34:00Z"
}
```

* **Field Requirements**:
  - `Mandatory`: `exception_id`, `rule_id`, `rule_category`, `severity`, `cik`, `form`, `fiscal_year`, `fiscal_period`, `reported_value`, `status`, `source_document`, `evidence_reference`.
  - `Optional`: `expected_value`, `difference`, `difference_pct` (used when mathematical comparison applies).
  - `Derived`: `severity` (derived from absolute magnitude, relative percentage error, and accounting materiality).
