# AuditAI BI — Evaluation Plan & Benchmark Governance

---

### 1. Metric Control & Specification Matrix

To ensure evaluation integrity, all metrics are classified by their operational role, formula, and gate status:

| Metric Name | Purpose | Mathematical Formula | Required Dataset | Ground Truth Required? | Metric Classification | Used as Phase Gate? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Verification Precision** | Quantify proportion of flagged exceptions that are true discrepancies. | $\frac{TP}{TP + FP}$ | Synthetic Perturbation Set (Tier D) | Yes (Injected error labels) | `[INTERNAL PROJECT TARGET]` | Yes (P6 Gate: Target $\ge 95\%$) |
| **Perturbation Recall** | Quantify ability to detect injected accounting anomalies. | $\frac{TP}{TP + FN}$ | Synthetic Perturbation Set (Tier D) | Yes (Injected error labels) | `[INTERNAL PROJECT TARGET]` | Yes (P6 Gate: Target $\ge 90\%$) |
| **Clean Set False Alarm Rate** | Ensure compliant filings produce zero false critical alarms. | $\frac{FP_{\text{critical}}}{N_{\text{compliant}}}$ | Compliant Control Cohort (Tier B) | Yes (Audited restatement-free 10-Ks) | `[INTERNAL PROJECT TARGET]` | Yes (P6 Gate: Target $< 1.0\%$) |
| **Execution Throughput** | Evaluate data engineering pipeline scalability. | $\frac{\text{Facts Verified}}{\text{Elapsed Seconds}}$ | Any filing batch | No | `[PORTFOLIO PERFORMANCE METRIC]` | No (Informational) |
| **Provenance Traceability Rate** | Verify that every exception links to an immutable source fact. | $\frac{\text{Exceptions with Valid Accession \& URI}}{\text{Total Exceptions}}$ | All processed filings | No (Schema integrity check) | `[INTERNAL PROJECT TARGET]` | Yes (P5 Gate: Mandatory $100\%$) |
| **Official Task 3 Score** | Official competition evaluation metric. | `[UNKNOWN]` / `[NOT VERIFIED]` | Official Task 3 Evaluation Set (Tier A) | Yes (Official competition labels) | `[OFFICIAL COMPETITION REQUIREMENT]` | Yes (P11 Submission Gate) |

---

### 2. Evaluation Datasets & Ground Truth Strategy

Because official competition test labels are currently `[UNKNOWN]`, the project establishes a dual-dataset benchmark strategy:

```
                                  ┌─────────────────────────────────────────┐
                                  │ Evaluation Benchmark Strategy           │
                                  └────────────────────┬────────────────────┘
                                                       │
                     ┌─────────────────────────────────┴─────────────────────────────────┐
                     ▼                                                                   ▼
       ┌───────────────────────────┐                                       ┌───────────────────────────┐
       │ 1. Compliant Control Set  │                                       │ 2. Perturbation Test Set  │
       │ (False Positive Benchmark)│                                       │ (Recall/Precision Bench)  │
       └─────────────┬─────────────┘                                       └─────────────┬─────────────┘
                     │                                                                   │
         Top 50 S&P 500 10-K Filings                                        Synthetically Injected Errors
         Audited & Restatement-Free                                         Controlled Ground Truth Labels
         Target: FP Rate < 1%                                               Target: Precision ≥ 95%
```

1. **Compliant Control Set (Tier B)**:
   - *Sample*: 10–25 verified annual 10-K filings from high-compliance issuers (e.g., Apple, Microsoft, Johnson & Johnson).
   - *Ground Truth Assumption*: Statutory audited balance sheets and operations statements reconcile within standard rounding tolerances ($\epsilon = 1.00$).
   - *Target*: Zero critical false positives. Any flagged exception on this set triggers investigation into rule over-sensitivity or missing extension concept handling.
2. **Synthetic Perturbation Test Bench (Tier D)**:
   - *Sample*: Controlled algorithmic mutations applied to valid Tier B facts.
   - *Injected Defects*:
     - Inverted arithmetic signs on assets/inventory.
     - Perturbed line-item sums in Gross Profit and Operating Income.
     - Artificially modified reporting period end dates.
     - Currency and unit mismatches.
   - *Target*: Precision $\ge 95\%$, Recall $\ge 90\%$.

---

### 3. Error Taxonomy

When exceptions are generated, they are mapped to an explicit accounting error taxonomy:

1. **Structural Balance Errors (`STR`)**: Violations of the fundamental balance sheet equation ($A \ne L + E$).
2. **Calculation Rollup Errors (`CALC`)**: Component line items do not sum to reported total headers.
3. **Extraction & Format Errors (`EXT`)**: Missing required dimensions, non-ISO dates, or corrupt numeric strings.
4. **Semantic Invariance Errors (`SEM`)**: Non-contra asset accounts reporting negative balances without explanation.
5. **Temporal Duration Discrepancies (`PER`)**: Sum of quarterly cash flow increments does not equal reported annual total.
6. **Unit / Currency Discordance (`UNT`)**: Summing facts tagged with conflicting units (e.g., USD and EUR) without conversion.
7. **Cross-Statement Articulation Errors (`CRS`)**: Net Income reported on the Income Statement conflicts with Net Income starting line on Cash Flows.

---

### 4. Quality Gates & Stop-the-Line Thresholds

Progress through evaluation phases (specifically Phase 6) is strictly halted if:
* Provenance Traceability Rate falls below **100.0%** for `CRITICAL` or `HIGH` exceptions.
* Clean Set False Positive Rate exceeds **1.0%** (indicates flawed calculation linkbase parsing).
* Perturbation Recall falls below **90.0%** (indicates validation rules are too permissive).
