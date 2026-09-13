# AuditAI BI — Data Scope & Architectural Boundaries

---

### 1. 4-Tier Data Architecture

To prevent data contamination, maintain realistic expectations, and cleanly separate external benchmarks from development resources, data is organized into four strictly segregated tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Tier A: Official Competition Data (FinReason Task 3)                   │
│ Classification: [UNKNOWN / PENDING RELEASE]                            │
│ Role: Final evaluation target & official competition benchmark.        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Held in reserve / modular adapter)
┌───────────────────────────────────▼────────────────────────────────────┐
│ Tier B: SEC EDGAR Public Filings (Company Facts & Submissions)         │
│ Classification: [VERIFIED FACT / REMOTELY ACCESSIBLE]                  │
│ Role: Primary development, exploratory analysis, and reference corpus. │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Tier C: US-GAAP & DEI Taxonomies (FASB / XBRL US Standards)            │
│ Classification: [VERIFIED FACT / PUBLIC SPECIFICATION]                 │
│ Role: Invariant schema standards, concept trees, and calculation rules.│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Tier D: Synthetic Perturbation Engine (Project Generated)              │
│ Classification: [PROJECT DESIGN DECISION]                              │
│ Role: Controlled unit/integration testing (injected signs, sums, dates)│
└────────────────────────────────────────────────────────────────────────┘
```

#### Tier Specifications:
1. **Tier A (Official Competition Dataset)**: The benchmark evaluation corpus provided by IEEE Big Data Cup 2026 organizers. It is currently `[UNKNOWN]` and will be consumed via a dedicated adapter in Phase 11.
2. **Tier B (SEC EDGAR Reference Corpus)**: Real-world 10-K and 10-Q corporate disclosures downloaded via the SEC EDGAR Company Facts API (`https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`) and Submissions API (`https://data.sec.gov/submissions/CIK{cik}.json`). Used for exploratory development and control baselines.
3. **Tier C (Taxonomy Reference Standards)**: Official FASB US-GAAP and DEI XML/JSON taxonomies, defining concept definitions, standard balance types (debit/credit), and official calculation linkbases.
4. **Tier D (Synthetic Perturbation Test Bench)**: Controlled dataset generated internally by mutating valid Tier B facts (e.g., perturbing numbers, inverting signs, misaligning dates) to evaluate recall and precision without relying on unreleased competition labels.

---

### 2. Disclosures & Statement Coverage

* **Statutory Forms**:
  - `Form 10-K`: Annual comprehensive financial reports.
  - `Form 10-Q`: Quarterly interim financial reports.
  - `Form 10-K/A` & `10-Q/A`: Amended statutory filings.
* **Covered Statements**:
  - Balance Sheet / Statement of Financial Position (`BalanceSheet`)
  - Income Statement / Statement of Operations (`StatementOfIncome`)
  - Statement of Cash Flows (`StatementOfCashFlows`)
* **Key Concept Families**:
  - Assets (`us-gaap:Assets`, `AssetsCurrent`, `AssetsNoncurrent`)
  - Liabilities (`us-gaap:Liabilities`, `LiabilitiesCurrent`, `LiabilitiesNoncurrent`)
  - Stockholders' Equity (`us-gaap:StockholdersEquity`, `RetainedEarningsAccumulatedDeficit`)
  - Revenues (`us-gaap:Revenues`, `SalesRevenueNet`)
  - Cost of Goods Sold (`us-gaap:CostOfGoodsAndServicesSold`)
  - Operating Income (`us-gaap:OperatingIncomeLoss`)
  - Net Income (`us-gaap:NetIncomeLoss`)
  - Operating Cash Flows (`us-gaap:NetCashProvidedByUsedInOperatingActivities`)

---

### 3. Unit of Analysis & Atomic Data Grain

The atomic unit of analysis in the canonical financial layer is:

$$\mathbf{Grain} = \mathbf{CIK} \times \mathbf{AccessionNumber} \times \mathbf{ConceptQName} \times \mathbf{PeriodInterval} \times \mathbf{Unit}$$

#### Entity Keys & Constraints
* **Surrogate Primary Key (`fact_id`)**: A deterministically generated `UUIDv5` calculated from the composite string:
  $$\text{UUIDv5}(\text{Namespace\_DNS}, \text{cik} + \text{"\_"} + \text{accn} + \text{"\_"} + \text{concept} + \text{"\_"} + \text{period\_end} + \text{"\_"} + \text{unit})$$
* **Business Key**: `(cik, accn, concept_qname, period_end, unit, form)`
* **Uniqueness Constraint**: Exactly one reported value per unique business key. When an amendment modifies a previously reported figure, the amendment carries a distinct accession number (`accn`), creating a distinct historical fact record while establishing a lineage link via `superseded_by_accn`.

---

### 4. Data Availability Status Matrix

| Data Source / Artifact | Role in System | Local Availability | Remote Verification | Epistemic Status |
| :--- | :--- | :--- | :--- | :--- |
| **SEC EDGAR Company Facts API** | Reference / Dev Corpus | Local cache not created (P0) | Verified live via HTTP probe | `[VERIFIED FACT]` |
| **SEC EDGAR Submissions API** | Filing Metadata & Verification | Local cache not created (P0) | Verified live via HTTP probe | `[VERIFIED FACT]` |
| **US-GAAP Calculation Linkbases** | Calculation Graph Validation | Local cache not created (P0) | Verified public FASB standard | `[VERIFIED FACT]` |
| **IEEE FinReason Official Task 3 Data** | Competition Submission Target | Not Present locally | Unverified public distribution | `[UNKNOWN]` |
| **Synthetic Perturbation Suite** | Controlled Recall Testing | Engine not yet implemented | N/A (Internal generator) | `[PROJECT DESIGN DECISION]` |
