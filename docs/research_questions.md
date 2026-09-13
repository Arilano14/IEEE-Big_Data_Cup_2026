# AuditAI BI — Research Questions & Experimental Design

---

### 1. Research Prioritization Matrix

To maintain project feasibility under a solo-developer implementation schedule, research questions are explicitly prioritized and filtered:

| Research Question | Priority Tier | Feasibility | Experimental Approach |
| :--- | :--- | :--- | :--- |
| **RQ1: Extension Concept False Positives** | **CORE** | High | Graph traversal of calculation linkbases across 25–50 SEC filings. |
| **RQ2: Statement Discrepancy Distribution** | **CORE** | High | Cross-sectional aggregation across Balance Sheet, Income, and Cash Flow tables. |
| **RQ3: Deterministic Rules vs. LLM Reasoning**| **SECONDARY (Ext. MVP)** | Moderate | Controlled offline benchmark of 50–100 verified exception cases against zero-shot LLM prompts. |
| **RQ4: Auditor Triage Efficiency Study** | **REJECTED FOR MVP** | Unfeasible | Requires human-subject institutional review and CPA recruitment. Relegated to future theoretical work. |

---

### 2. Core Research Questions

#### RQ1: Incomplete Linkbases & Custom Extension Taxonomies
* **Question**: *To what extent do automated calculation linkbases in US-GAAP XBRL filings produce false-positive calculation exceptions due to undisclosed registrant-specific extension concepts?*
* **Hypothesis**: Off-the-shelf calculation linkbase trees will trigger false-positive calculation roll-up errors in $> 15\%$ of filers unless extension elements (`domain-specific QNames`) are dynamically resolved and integrated into the summation graph.
* **Independent Variable**: Extension concept handling method (Strict Standard Taxonomy vs. Dynamic Extension Tree Resolution).
* **Dependent Variables**: False Positive Rate on audited control filings; Total Unreconciled Dollar Delta.
* **Experimental Protocol**:
  1. Ingest 25 annual reports from multi-segment issuers.
  2. Execute Category 2 (`CALC`) rules under strict US-GAAP standard concept mapping.
  3. Re-execute rules after incorporating company-specific extension relationship linkbases.
  4. Measure reduction in spurious calculation exceptions.

#### RQ2: Discrepancy Distribution Across Financial Statements
* **Question**: *What is the empirical distribution of financial statement discrepancies across Statement Types (Balance Sheet vs. Statement of Operations vs. Statement of Cash Flows)?*
* **Hypothesis**: Statements of Cash Flows exhibit the highest frequency of semantic and period reconciliation discrepancies ($> 50\%$ of all detected exceptions), driven by non-standard operating adjustment items and quarterly duration aggregations.
* **Independent Variable**: Statement Type (`BalanceSheet`, `StatementOfIncome`, `StatementOfCashFlows`).
* **Dependent Variables**: Exception count per statement; Exception severity distribution (`CRITICAL` vs. `LOW`); Reconciliation failure rate.
* **Experimental Protocol**:
  1. Process verified multi-year filing cohorts across 3 sectors (Technology, Manufacturing, Retail).
  2. Group generated exceptions by statement type and rule category.
  3. Perform Chi-square test of independence to assess whether error propensity is non-uniformly distributed across statement types.

---

### 3. Secondary Research Question (Extended MVP)

#### RQ3: Deterministic Rule Verification vs. LLM Financial Reasoning
* **Question**: *How do deterministic rule-based verification outputs compare with zero-shot Large Language Model financial reasoning on identical financial discrepancy instances?*
* **Hypothesis**: While LLMs can generate plausible natural language explanations, their mathematical precision and recall on multi-step roll-up calculations will lag deterministic symbolic rules, exhibiting hallucination rates $> 20\%$ on arithmetic deltas.
* **Independent Variable**: Reasoning Engine (Deterministic Symbolic Rule Engine vs. Zero-Shot Prompted LLM).
* **Dependent Variables**: Arithmetic Precision; Delta Exactness; Hallucination Frequency; Execution Latency.
* **Experimental Protocol**:
  1. Isolate 50 verified exceptions (25 genuine errors from perturbation set, 25 compliant balances).
  2. Feed raw statement tables and prompt an LLM to identify arithmetic errors, calculate exact deltas, and cite evidence.
  3. Compare LLM classifications and numerical calculations against the deterministic engine ground truth.

---

### 4. Rejected Scope: RQ4 (Auditor User Study)

* **Original Proposal**: *How does evidence-based provenance improve human auditor triage efficiency compared to traditional spreadsheet reviews?*
* **Formal Rejection Justification**:
  - Requires recruiting certified public accountants (CPAs) or audit professionals.
  - Requires institutional human-subjects research ethics approval (IRB).
  - Unrealistic, costly, and resource-prohibitive for a solo data engineering portfolio project.
* **Disposition**: Excluded from technical implementation. The theoretical advantages of provenance in audit workflows will be reviewed solely via literature synthesis in documentation.
