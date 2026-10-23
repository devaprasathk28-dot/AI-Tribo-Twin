# AI-TriboTwin — Sprint 9: Original Composite Evidence Recovery Report

**Document Version:** 1.0  
**Date:** 2026-10-22  
**Status:** COMPLETE — ALL ORIGINAL TARGETS REMAIN STRICTLY BLOCKED (`NO_GO`)  
**Project Root:** `c:\Users\devap\Documents\AI-TriboTwin`  

---

## 1. Executive Summary & Objective

The primary objective of **Sprint 9** was to make concrete, auditable progress toward evaluating the scientific defensibility of a machine learning model for the original glass-fibre reinforced epoxy (GFRE) composite experiments. In accordance with project governance protocols (`docs/STEP4_5_BLOCKER_RESOLUTION.md`, `docs/STEP4_8_EVIDENCE_ASSESSMENT_PROTOCOL.md`, `docs/STEP4_9_EVIDENCE_INTAKE_CHECKLIST.md`, and `docs/STEP4_10_SCIENTIFIC_READINESS_GATE.md`), Sprint 9 strictly prioritized **evidence recovery, physical traceability verification, and scientific integrity** over new UI features or premature modeling.

Key outcomes of Sprint 9:
1. **Manuscript XML Source Audit Completed:** The author's source manuscript (`C:\Users\devap\Downloads\Tribological Properties.docx`) was inspected at the XML text and relationship level. It contains 0 XML data tables (`<w:tbl>`) and 23 embedded image figures, establishing that the raw experimental tables exist solely in the three external DOCX files.
2. **Physical Traceability Failure Confirmed:** The published paper's COF figures (Figures 8–10) cannot be mapped to the 108 DOCX source rows. Plotted COF values are tightly clustered in $[0.300, 0.303]$ under a claimed constant 10 N load, whereas DOCX COF rows range from $0.160$ to $0.962$ (mean $0.441$, std $0.201$), with 10 N rows reaching $0.962$.
3. **Physical Test Condition Incompatibility Discovered (ZrSiO4 System):** In `WEAR TEST ZrSiO4 and TiO2 fillers.docx`, experiments were performed at sliding distances of **50 m, 75 m, and 100 m** (velocities 1.0, 1.5, 2.0 m/s; loads 10, 15, 20 N). In contrast, the manuscript's Figures 7, 10, and 13 plot responses at **100 m, 200 m, and 300 m**. There are **zero** 200 m or 300 m experimental rows in the Zr source table, creating an irreconcilable physical contradiction.
4. **Internal Material Conflict Corroborated:** The conflict between `ZrSiO4:SiO2` (Section 2.1 methodology flowchart) and `ZrSiO4:TiO2` (Section 3 text, figure captions, and DOCX title) is confirmed to be directly native to the author's Word document text stream.
5. **Readiness Gate Strictly Enforced:** All 4 original composite targets (`TARGET-COF`, `TARGET-WEAR`, `TARGET-SWR`, `TARGET-WVL`) remain strictly **`BLOCKED`** (`NO_GO`). No synthetic data, proxy data, or unrelated Cambridge carbon-fibre data may be substituted.
6. **Raw Data Integrity Preserved:** `data/raw/tribological_experiments_raw.csv` SHA-256 hash remains verbatim identical: `BC4B438BFCB472BDB92D653953B23ACD3FF20DBAF3E0220704AA0A16BDDEDD1D`.

---

## 2. Evidence Audit & Forensic Traceability Investigation

### 2.1 Author Manuscript Audit (`Tribological Properties.docx`)

We audited `C:\Users\devap\Downloads\Tribological Properties.docx` directly:
- **Core Metadata:**
  - Creator: `ashif shamsudeen`
  - Last modified by: `kps` (K. P. Srinivasa Perumal, corresponding author)
  - Revisions: 133
  - Document structure: 31 pages, 9,104 words, 23 embedded media image files.
- **Embedded Table Verification:**
  - Search for OpenXML table tags (`<w:tbl>` in `word/document.xml`) yielded exactly **0 tables**.
  - All tabular representations of wear or friction data were omitted from the manuscript body or rendered as image figures. The primary tabular data resides exclusively in the three Taguchi DOCX files.
- **Text Analysis of Results & Discussion:**
  - Paragraph 68 states: *"The experiments were conducted over a duration of ten minutes, using different sliding distances and speeds while maintaining a constant load of 10 N."*
  - This statement directly contradicts the DOCX tables, which systematically vary load across 3 levels (10 N, 20 N, 30 N for FeTiO3/TiO2; 10 N, 15 N, 20 N for ZrSiO4).

### 2.2 Traceability Analysis: Published COF Figures vs. DOCX Table Rows

The published manuscript presents COF in Figures 8, 9, and 10 as grouped bar charts:
- **Figure 8** (FeTiO3 & SiO2): Reports COF values at 100 m (~0.300), 200 m (~0.301–0.302), and 300 m (~0.302–0.303).
- **Figure 9** (TiO2 & SiO2): Reports COF values at 100 m (~0.300), 200 m (~0.300–0.302), and 300 m (~0.302–0.303).
- **Figure 10** (ZrSiO4 & TiO2): Reports COF values at 100 m (~0.300), 200 m (~0.301–0.302), and 300 m (~0.301–0.303).

**Comparison with Primary Row-Level Data (`tribological_experiments_raw.csv`):**

| Material System | DOCX Rows | DOCX COF Range | DOCX COF Mean ± Std | DOCX COF Range at 10 N Load | Paper Plotted Range |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FeTiO3:SiO2** | 36 | 0.216 – 0.962 | 0.557 ± 0.222 | 0.265 – 0.962 | 0.300 – 0.303 |
| **TiO2:SiO2** | 36 | 0.161 – 0.821 | 0.377 ± 0.172 | 0.161 – 0.454 | 0.300 – 0.303 |
| **ZrSiO4:TiO2** | 36 | 0.160 – 0.721 | 0.390 ± 0.144 | 0.160 – 0.520 | 0.300 – 0.303 |
| **All Systems** | **108** | **0.160 – 0.962** | **0.441 ± 0.201** | **0.160 – 0.962** | **0.300 – 0.303** |

**Key Findings:**
1. At 10 N load, row RAW-019 records $\text{COF} = 0.962$ (10 wt% FeTiO3:SiO2, $v=0.5\text{ m/s}$, $d=100\text{ m}$), and row RAW-029 records $\text{COF} = 0.954$ (15 wt% FeTiO3:SiO2, $v=1.0\text{ m/s}$, $d=200\text{ m}$). These values are over $300\%$ higher than the paper's plotted range of $0.300–0.303$.
2. There are no run numbers, specimen serial IDs, or timestamps connecting DOCX rows to the chart bars.
3. The paper figures cannot be derived as simple means, medians, or subset slices of the DOCX rows.
4. **Scientific Conclusion:** It is physically impossible to map the paper's COF figures to individual DOCX rows without access to the author's primary laboratory data logs.

### 2.3 Physical Condition Incompatibility: The ZrSiO4 Sliding Distance Discrepancy

A critical discrepancy was discovered between `WEAR TEST ZrSiO4 and TiO2 fillers.docx` and the manuscript:
- In `WEAR TEST ZrSiO4 and TiO2 fillers.docx`, the operating conditions for all 4 tables (0 wt%, 5 wt%, 10 wt%, 15 wt%) are:
  - Normal Load: 10 N, 15 N, 20 N
  - Sliding Speed: 1.0 m/s, 1.5 m/s, 2.0 m/s
  - Sliding Distance: **50 m, 75 m, 100 m**
- In `Tribological Properties.docx` (and `.pdf`):
  - Figure 7 (Specific Wear Rate), Figure 10 (COF), and Figure 13 (Wear Volume Loss) plot bar charts against sliding distances of **100 m, 200 m, and 300 m**.
  - Section 3, paragraph 73 explicitly claims: *"Figure 7 presents the specific wear rate of GFRP composites at sliding distances of 100, 200, and 300 meters..."*
  - Section 3, paragraph 87 explicitly claims: *"The figure 10 illustrates the coefficient of friction... across three sliding distances: 100 m, 200 m, and 300 m."*
  - Section 3, paragraph 101 explicitly claims: *"This figure 13 illustrates the effect of varying sliding distances (100, 200, and 300 m) on wear volume loss..."*

**Scientific Impact:**  
The ZrSiO4 experimental table in the project's possession has **zero** data points at 200 m or 300 m. The figures in the published manuscript plot data points that literally do not exist in the primary DOCX table. Either the authors conducted an entirely separate series of 200 m and 300 m tests not included in the DOCX files, or the figures were plotted from a different dataset.

### 2.4 Material Formulation Conflict (`ZrSiO4:SiO2` vs `ZrSiO4:TiO2`)

The audit confirmed that this contradiction is not an external transcription error, but is embedded directly within the author manuscript:
- **Manuscript Section 2.1 (Methodology flowchart text stream):** Explicitly states:
  $$\text{Material Selection: } \text{FeTiO}_3:\text{SiO}_2, \; \text{TiO}_2:\text{SiO}_2 \; \& \; \text{ZrSiO}_4:\text{SiO}_2 \; (0:0, 2.5:2.5, 5:5 \text{ and } 7.5:7.5 \text{ wt}\%)$$
- **Manuscript Section 3 & Captions:** Explicitly state:
  - *"Figure 7. Specific wear rate ZrSiO4 & TiO2 Nano Particles inclusions..."*
  - *"Figure 10. Coefficient of Friction of ZrSiO4 & TiO2 Nano Particles inclusions..."*
  - *"Figure 13. Wear Volume Loss of ZrSiO4 : TiO2 Nano Particles inclusions..."*
- **Primary DOCX File:** Titled `WEAR TEST ZrSiO4 and TiO2 fillers.docx`.

**Resolution Status:** **UNRESOLVED / BLOCKED.** Without primary chemical batch cards, procurement receipts, or direct author clarification, neither formulation can be asserted as ground truth.

### 2.5 Wear Rate Headings, Units, and Target Missingness

1. **Heading Inconsistency:**
   - FeTiO3 DOCX table heading: `Wear rate(Micron)(x10-6 m3/m)`
   - TiO2 DOCX table heading: `Wear rate (Micron)`
   - ZrSiO4 DOCX table heading: `Wear rate (Micron)`
2. **Missing Specific Wear Rate:**
   - `specific_wear_rate_raw` is $100\%$ blank (108/108 rows) in `tribological_experiments_raw.csv`.
   - In `Wear test TiO2 and SiO2 L9 orthogonal array (5).docx` and `WEAR TEST ZrSiO4 and TiO2 fillers.docx`, the column `Specific Wear rate (m3/Nm)` exists in the table header but every single cell (72/72) is empty.
   - In `Wear test FeTiO3 and SiO2 L27 orthogonal array.docx`, the column does not exist at all.
3. **Missing Wear Volume Loss:**
   - `wear_volume_loss_raw` is $100\%$ blank (108/108 rows) in `tribological_experiments_raw.csv`.
   - Figures 11–13 plot grouped bars labelled "WEAR VOLUME LOSS" with values ~0.001 to 0.009, but the y-axis has **no units**, and no individual specimen IDs are provided.

---

## 3. External Repository & Author Outreach Audit

### 3.1 Public Repository & Bibliographic Search

We queried scholarly databases and registries (Crossref, OpenAlex, Semantic Scholar, Zenodo, Figshare):
- **Title Query:** *"AI-Enabled Prediction and Experimental Characterization of Tribological Behaviour and Wear Morphology in Ceramic-Filler included Glass Fiber Reinforced Epoxy Composites"*
- **Authors:** K. P. Srinivasa Perumal, L. Selvarajan, C. K. Murugesan, D. Subramaniam
- **Findings:**
  - No matching published journal article, volume, issue, or DOI was identified.
  - No public repository (Zenodo, Figshare, Dryad, GitHub) contains supplementary datasets or spreadsheets for this title.
  - The document in possession appears to be an unpublished author manuscript or draft preprint.

### 3.2 Author Clarification Tracker Status

Per `data/validation/AUTHOR_CLARIFICATION_TRACKER.csv`:
- All questions (Q-01 through Q-07) are logged with priority `HIGH` or `MEDIUM`.
- `sent_date`: `EMPTY`
- `delivery_status`: `NOT_SENT`
- `response_status`: `NOT_SENT`
- `verification_status`: `NOT_RECEIVED`

> [!IMPORTANT]
> In accordance with strict project rules, no message has been transmitted, no author contact has been claimed, and no responses or measurements have been fabricated. Transmission requires formal human review and dispatch.

---

## 4. Evidence Register Updates

The following updates were committed to `data/validation/` artifacts:

1. **`data/validation/STEP4_5_EVIDENCE_REGISTER.csv`**:
   - Added `EV-S9-01`: Direct manuscript XML audit of `Tribological Properties.docx` (0 tables, 23 images, native internal contradiction).
   - Added `EV-S9-02`: Physical sliding distance and load condition contradiction between Zr DOCX (50, 75, 100 m) and paper figures (100, 200, 300 m).
   - Added `EV-S9-03`: Quantitative COF divergence between DOCX rows ($0.160–0.962$) and paper figures ($0.300–0.303$).
   - Added `EV-S9-04`: Bibliographic and public repository audit establishing unpublished preprint status and `NOT_SENT` author tracker state.
2. **`data/validation/STEP4_8_EVIDENCE_ASSESSMENT.csv`**:
   - Updated assessment rows AS-01, AS-02, AS-06, and AS-07 to reflect Sprint 9 forensic audit findings.
3. **`data/validation/STEP4_10_READINESS_GATE.csv`**:
   - Re-affirmed `NO_GO - BLOCKED` for all 4 targets, citing EV-S9-01 through EV-S9-04.
4. **`data/validation/TARGET_READINESS.csv`**:
   - Updated scientific evidence columns with Sprint 9 findings; all targets remain `BLOCKED`.

---

## 5. Target-by-Target Scientific Readiness Decisions

| Target ID | Target Name | Status | Primary Blocker | Minimum Evidence Required to Unblock |
| :--- | :--- | :---: | :--- | :--- |
| **TARGET-COF** | Coefficient of Friction | **`BLOCKED`** (`NO_GO`) | DOCX row range ($0.160–0.962$) contradicts paper figures ($0.300–0.303$); Zr distances contradict DOCX ($50–100\text{ m}$ vs $100–300\text{ m}$); no run mapping. | Primary run-to-figure mapping from author; instrument calibration log; explanation of source strings `0. 29` and `0. 36`. |
| **TARGET-WEAR** | Wear Rate | **`BLOCKED`** (`NO_GO`) | Heterogeneous table headings (`Micron` vs `Micron x10-6 m3/m`); operational definition unverified across materials. | Author/instrument calibration sheet; unified physical unit definition; run-level mapping. |
| **TARGET-SWR** | Specific Wear Rate | **`BLOCKED`** (`NO_GO`) | $100\%$ missing in raw CSV (108/108 rows); 72/72 blank cells in DOCX; 36 rows absent. | Primary measured row-level specific wear rate data with run identifiers and units. |
| **TARGET-WVL** | Wear Volume Loss | **`BLOCKED`** (`NO_GO`) | $100\%$ missing in raw CSV (108/108 rows); no DOCX column; paper figures lack axis units. | Primary per-run volumetric wear data with calibration records and run identifiers. |

---

## 6. Single Most Useful Next Action

If the original composite targets remain blocked, what is the single most useful action?

> [!CAUTION]
> **Recommended Next Action: Human-Authorized Dispatch of Author Clarification Request**  
> No internal code change, data imputation, or synthetic modeling can resolve these primary physical contradictions.  
> The single most useful action is for the **project owner (human)** to review and manually transmit the pre-drafted clarification package ([`docs/AUTHOR_CLARIFICATION_REQUEST.md`](file:///c:/Users/devap/Documents/AI-TriboTwin/docs/AUTHOR_CLARIFICATION_REQUEST.md)) to corresponding author Dr. K. P. Srinivasa Perumal (`kpsrinivasaperumal@gmail.com`) and co-authors.  
> Until primary laboratory records, run mapping tables, and formulation sheets are provided, all 4 original composite targets must remain strictly **`BLOCKED`**.

---

## 7. Verification & Integrity Checklist

- [x] `data/raw/tribological_experiments_raw.csv` SHA-256 hash verified:  
  `BC4B438BFCB472BDB92D653953B23ACD3FF20DBAF3E0220704AA0A16BDDEDD1D` (verbatim unchanged).
- [x] Full Python test suite passed: **110 passed, 1 warning in 13.82s**.
- [x] Frontend test suite passed: **9 passed in 3.38s**.
- [x] Frontend typecheck, lint, and production Next.js build passed.
- [x] No synthetic or proxy data used for original composite targets.
- [x] Cambridge tow-on-tool carbon-fibre model remains completely isolated as an external demonstration.
