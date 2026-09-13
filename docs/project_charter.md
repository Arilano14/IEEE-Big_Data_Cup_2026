# AuditAI BI — Project Charter
## Explainable Financial Audit & Exception Intelligence Platform

---

### 1. Executive Summary

* **Project Name**: AuditAI BI (Explainable Financial Audit & Exception Intelligence Platform)
* **Primary Target**: IEEE Big Data Cup 2026 — FinReason Cup — Task 3: Financial Audit Verification
* **Core Mission**: Build a research-grade, deterministic, explainable financial audit verification and Business Intelligence system that:
  1. Ingests corporate financial/XBRL disclosures.
  2. Normalizes disclosures into a canonical financial representation.
  3. Formulates and executes deterministic accounting validation rules.
  4. Generates evidence-backed audit exceptions with 100% provenance back to source filings.
  5. Exposes validated results through a columnar analytical warehouse and an interactive Power BI dashboard.

---

### 2. Epistemic Classification Framework

To guarantee scientific rigor, data integrity, and engineering precision, every fact, boundary, and metric in this project is explicitly classified into one of seven epistemic categories:

1. `[VERIFIED FACT]`: Empirically confirmed through direct local environment inspection or authenticated API probe.
2. `[PROJECT DESIGN DECISION]`: An architectural, engineering, or structural choice established by this project.
3. `[ASSUMPTION]`: A working premise adopted in the absence of complete external verification; subject to refutation.
4. `[UNKNOWN]`: External information currently unavailable and unverified; strictly forbidden from being treated as fact.
5. `[PROVISIONAL DECISION]`: A working technical choice slated for empirical re-evaluation in Phase 1 or Phase 2.
6. `[OFFICIAL COMPETITION REQUIREMENT]`: Mandated by official IEEE Big Data Cup 2026 FinReason organizers.
7. `[INTERNAL PROJECT TARGET]`: An internal engineering aspirational goal or quality benchmark.

---

### 3. Problem Statement & Motivation

Corporate financial disclosures in structured XBRL formats frequently contain internal discrepancies, calculation roll-up errors, sign inversions, and reporting-period misalignments. Contemporary automated approaches often fall into two flawed extremes:
- **Black-box LLM Reasoners**: Prone to numerical hallucinations, non-deterministic outputs, and lack of mathematical explainability.
- **Naive Schema Validators**: Confined to syntactical XML/JSON schema validation, lacking semantic accounting depth, cross-statement articulation, and human-in-the-loop audit intelligence.

AuditAI BI solves this by establishing a **deterministic validation engine as the Single Source of Truth**, coupled with a multi-dimensional analytical warehouse and Power BI visual intelligence layer for auditor triage.

---

### 4. System Concepts & Boundaries

#### Operational Data vs. Validation Truth vs. Analytical BI Output
* **Operational Data (Source/Raw)**: As-reported disclosures from registrants (via SEC EDGAR or competition datasets). Contains revisions, rounding noise, and potential reporting defects. It is the *subject of verification*, never the standard of truth.
* **Validation Truth (Engine)**: Invariant mathematical accounting identities, US-GAAP calculation linkbases, and double-entry balance relationships. This layer is the *sole authority on validity*.
* **Analytical BI Output (Warehouse/Dashboard)**: Curated star schema tables, exception severity indices, and interactive drill-downs designed for auditor investigation.

#### Negative Boundary (What System Is NOT)
* NOT a fraud prediction or criminal intent engine.
* NOT a stock price forecasting or alpha-generation tool.
* NOT an automated replacement for certified public accountants.
* NOT an automatic statutory filing approval/rejection system.
* NOT an LLM-based financial calculation engine (LLMs may only assist in narrative summarization of deterministic findings).

---

### 5. Stakeholders & Users

1. **Financial Auditors & Reviewers**: Need rapid triage of mathematical roll-up errors and instant drill-through to original filing disclosures.
2. **XBRL Quality Assurance Analysts**: Need verification of taxonomy calculation networks and extension concept consistency.
3. **Academic Evaluators & Competition Judges**: Require reproducible benchmark evaluations, mathematical rigor, and transparent error taxonomies.
