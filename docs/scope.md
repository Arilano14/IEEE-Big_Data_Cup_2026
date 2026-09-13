# AuditAI BI — Scope Specification & Boundary Matrix

---

### 1. In-Scope Specifications

The following functional and technical capabilities are strictly within the project scope:

1. **Ingestion & Caching**: Automated fetching and immutable disk caching of SEC EDGAR XBRL disclosures (Company Facts and Submissions APIs) for Forms 10-K, 10-Q, and amendments.
2. **Canonical Financial Normalization**: Parsing raw JSON disclosures into typed, normalized relational representations (`DimEntity`, `DimFiling`, `FactReportedFact`).
3. **Deterministic Validation Engine**: Implementing pure, mathematical rule verification across Balance Sheets, Statements of Operations, and Statements of Cash Flows.
4. **Structural & Calculation Rule Execution**: Enforcing fundamental accounting balance identities ($A = L + E$) and calculation rollups (Gross Profit, Operating Income).
5. **Exception Intelligence**: Generating structured discrepancy records with absolute error deltas, percentage variance, and multi-tier severity classifications (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`).
6. **100% Provenance Mandate**: Cryptographic/URI mapping linking every exception to filing accession numbers, concept QNames, and official SEC URLs.
7. **Analytical Data Warehouse**: Transforming verified outputs into a columnar star-schema data warehouse (DuckDB / Parquet).
8. **Power BI Semantic Layer**: Building enterprise-grade DAX measures, dimensional relationships, and interactive executive & forensic audit dashboards in Microsoft Power BI Desktop.
9. **Controlled Benchmark Suite**: Evaluating precision, recall, and false alarm rates using audited control filings and synthetic perturbation error injection.
10. **Modular Competition Adapter**: Architecting an extensible schema adapter for official IEEE Big Data Cup FinReason Task 3 data payloads upon release.

---

### 2. Out-of-Scope Specifications (Negative Scope)

The following capabilities are explicitly forbidden or excluded from this project:

1. **Fraud Detection & Intent Classification**: The system flags discrepancies and accounting violations; it does NOT infer legal intent, executive malice, or regulatory fraud.
2. **Investment & Trading Recommendations**: No stock price prediction, valuation models, sentiment analysis, or alpha signals.
3. **Automated CPA Replacement**: The system is a decision-support and audit-intelligence tool; it does not replace professional auditing judgment.
4. **Filing Modification**: The system NEVER alters, amends, or transmits data back to regulatory filing repositories.
5. **LLM as Source of Financial Truth**: Large Language Models are strictly prohibited from calculating financial totals or determining exception validity.
6. **Real-time Streaming Ticker Processing**: Focus is entirely on periodic statutory disclosures (annual and quarterly reports).
7. **Human-Subject User Studies**: Recruiting certified public accountants for empirical usability experiments is excluded due to solo-developer project constraints.

---

### 3. Categorical Boundary Matrix

| Boundary Category | Detailed Inclusions / Rules |
| :--- | :--- |
| **MUST HAVE** | Deterministic validation engine, 100% provenance on HIGH/CRITICAL exceptions, canonical financial model, star schema export, reproducible evaluation pipeline, complete audit exception schema. |
| **SHOULD HAVE** | Local DuckDB analytical warehouse, Power BI template (.pbit / DAX scripts), synthetic error injection benchmark harness, test suite (`pytest`) with 100% pass rate. |
| **OPTIONAL** | Optional LLM-assisted audit summary generation (strictly conditioned on deterministic exception output; NEVER calculating financial figures), Docker containerization. |
| **FORBIDDEN** | Black-box LLM calculations, modifying source filings, committing credentials, silent fallback on broken rules, executing unapproved implementation code in Phase 0. |

---

### 4. Developer Sizing & Delivery Tiers

To ensure reliable completion by a solo developer, deliverables are strictly partitioned into 3 sequential delivery tiers:

#### Tier 1: Minimum Viable Product (MVP)
* Focus: Core end-to-end operational pipeline.
* Components:
  - Isolated Python virtual environment (`.venv`) managed via `uv`.
  - Ingestion pipeline for 5 S&P 500 registrants across technology and manufacturing.
  - Relational normalization into Parquet silver tables.
  - Tier 1 Core Validation Rules (Balance Sheet Balance, Gross Profit Rollup, Data Extraction Integrity).
  - Exception Catalog with calculated deltas and severity scoring.
  - 100% Provenance linking for all generated exceptions.
  - Star schema analytical store (DuckDB / Parquet).
  - Core Power BI Dashboard (Executive Overview, Exception Triage, Lineage Drill-down).
  - Automated `pytest` suite validating accounting identities.

#### Tier 2: Extended MVP
* Focus: Research rigor and broad sector coverage.
* Components:
  - Expansion to Tier 2 Validation Rules (Semantic Non-negative Invariants, Period Rollforward, Currency Consistency).
  - Cohort expansion to 25–50 filers across diverse sectors (Retail, Energy, Healthcare).
  - Synthetic perturbation benchmark suite (evaluating precision, recall, and false positive rates).
  - Advanced Power BI DAX measures and forensic audit drill-through paths.
  - Empirical research findings addressing RQ1 and RQ2.

#### Tier 3: Optional Research
* Focus: Advanced experimentation and competition submission.
* Components:
  - Tier 3 Cross-Statement Articulation (Net income flow between Income Statement and Cash Flow Statement).
  - Offline comparative study against zero-shot LLM prompts (RQ3).
  - Docker containerization for one-click environment deployment.
  - Official IEEE FinReason Task 3 submission adapter upon release.
