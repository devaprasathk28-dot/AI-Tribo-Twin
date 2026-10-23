# AI-TriboTwin — Step 4.5 Blocker Resolution

**Decision: Step 5 target modelling remains blocked.** This completion adds the
requested evidence register and author-clarification draft. It does not resolve
scientific questions, modify raw data, create a modelling dataset, or train a
model.

## Deliverables and evidence basis

- [`../data/validation/STEP4_5_EVIDENCE_REGISTER.csv`](../data/validation/STEP4_5_EVIDENCE_REGISTER.csv)
  records evidence by blocker and distinguishes primary-source facts documented
  by the earlier visual/source review from the existing audit and verification
  artifacts.
- [`AUTHOR_CLARIFICATION_REQUEST.md`](./AUTHOR_CLARIFICATION_REQUEST.md)
  is an unsent draft for the authors.
- Existing sources reviewed for this continuation included
  [`SCIENTIFIC_SOURCE_REVIEW.md`](./SCIENTIFIC_SOURCE_REVIEW.md),
  [`STEP4_DATA_READINESS_REPORT.md`](./STEP4_DATA_READINESS_REPORT.md),
  [`STEP4_VARIABLE_INVENTORY.md`](./STEP4_VARIABLE_INVENTORY.md),
  [`STEP4_FEATURE_ASSESSMENT.md`](./STEP4_FEATURE_ASSESSMENT.md),
  [`TARGET_READINESS.csv`](../data/validation/TARGET_READINESS.csv),
  [`SCIENTIFIC_AMBIGUITIES.csv`](../data/validation/SCIENTIFIC_AMBIGUITIES.csv),
  [`SOURCE_ISSUES.csv`](../data/validation/SOURCE_ISSUES.csv),
  and [`ROW_LEVEL_SOURCE_VERIFICATION.csv`](../data/validation/ROW_LEVEL_SOURCE_VERIFICATION.csv).

The PDF and three named DOCX records are available under
`C:\Users\devap\Downloads` as recorded in the prior source review. The detailed
visual page findings and DOCX comparison outcomes below are carried forward
from those prior reports; this continuation does not represent a fresh
page-by-page visual inspection or a new 108-row DOCX comparison. The
verification manifest documents CSV-to-DOCX comparisons. It does not verify
the paper's figures against the DOCX runs.

The search scope was limited to the project tree and known source/research
locations under Downloads, and the known source filenames and evidence named
in existing audit records. No exhaustive content search of all files under
Downloads, all local folders, external repositories, supplementary-data
portals, author archives, or laboratory information systems was performed.
Consequently, absence from the current project CSV and the three inspected
DOCX tables is not proof that additional primary records do not exist. No
`NOT_FOUND_IN_SEARCHED_SOURCES` conclusion is made for external supplements,
instrument exports, or laboratory records.

## Blocker decisions

| Blocker | Status | Evidence-based finding | Target-readiness effect |
|---|---|---|---|
| A — COF | **AUTHOR CLARIFICATION REQUIRED** | The prior visual review records a paper narrative range of 0.300–0.303 and grouped plots around that range. DOCX-derived row values are much wider, and the plots lack sample-level IDs/mapping. The raw strings `0. 29` and `0. 36` are preserved. | COF remains **BLOCKED**. Need original run-level readings, measurement/protocol details, paper-to-run mapping, and authoritative disposition of the two raw strings. |
| B — Wear rate | **UNRESOLVED** | The prior DOCX review records different headings: FeTiO3 `Wear rate(Micron)(x10-6 m3/m)` versus `Wear rate (Micron)` for the other two systems. Paper prose does not establish that populated values share one definition, unit, scale, or mapping. | Raw wear-related measurement remains **BLOCKED**. Need measurement definition, formula, units/scale for each table, instrument records, and proof of cross-system comparability. |
| C — Specific wear rate | **UNRESOLVED** | The CSV field is blank across all rows; the prior source review reports a separate specific-wear column with blank rows in two DOCX sets and no such column in the third. Paper notation is not consistently reconciled and is not row-linked. | Specific wear rate remains **BLOCKED**. Need authoritative formula/unit/scale and primary row-level values tied to run IDs, if measured. Do not derive values. |
| D — Wear volume loss | **AUTHOR CLARIFICATION REQUIRED** | The prior visual review records grouped plots labelled `WEAR VOLUME LOSS` without visible units or sample IDs. The prior DOCX review found no row-level volume-loss field in the three wear-table sets. | Wear volume loss remains **BLOCKED**. Need per-run measurements, explicit units and method, calibration/procedure, and run identifiers mapped to conditions. |
| E — Material identity | **AUTHOR CLARIFICATION REQUIRED** | The prior visual review records `ZrSiO4:SiO2` in the methodology flowchart and `ZrSiO4:TiO2` in results/figures; the associated DOCX records use the latter. This contradiction does not identify the actual prepared formulation. | Zr material feature remains **BLOCKED**. Need authoritative formulation/preparation/sample-label records or written author confirmation. |
| F — Experimental run mapping | **UNRESOLVED** | The Step 3 manifest supports exact transcription from 108 CSV rows to indexed DOCX rows. It does not link those rows to paper plots/results. The prior paper review records grouped results without sample IDs. | Paper-to-row target mapping remains **BLOCKED**. Need an experiment/run matrix linking each identifier to material composition, test conditions, measurement outputs, and paper figure/table membership. |

## Target-readiness decision

No new authoritative measurements, definitions, source-to-paper mapping, or
author confirmation were added in this continuation. Therefore none of the
existing target decisions changes:

- COF: **BLOCKED**
- Raw wear-related measurement / wear rate: **BLOCKED**
- Specific wear rate: **BLOCKED**
- Wear volume loss: **BLOCKED**

No target is marked `READY` or `CONDITIONALLY_READY`. The evidence register
distinguishes the prior primary-source review record from primary data and
from secondary project reports; see its `evidence_type`, `authority_level`,
and `notes` fields.

## Evidence required before Step 5

1. An author- or laboratory-approved run-level mapping from each DOCX row to
   the paper's figures/tables, including stable run identifiers and all
   material/test-condition fields.
2. Original COF measurements or instrument exports and a reconciliation of the
   0.300–0.303 paper claims with the wider DOCX rows. Preserve the raw strings
   regardless of any later interpretation.
3. A definition, formula, exact units and scale for each wear-related source
   column, including whether the table values are comparable across systems.
4. Row-level specific-wear-rate and wear-volume-loss values with units and
   measurement methods, if those targets were actually measured. Do not
   calculate, digitize from grouped charts, or infer them.
5. Authoritative evidence of the actual Zr filler pair, and clarification of
   the FeTiO3 component split if those compositions are to be used as model
   inputs.
6. Confirmation of the protocol and whether the DOCX condition matrix and
   reported paper figures describe the same experiments.

## Final decision

Step 4.5 deliverables are now present, but the scientific blockers are not
resolved. The project may proceed with obtaining clarifications and primary
records only. It must not proceed to Step 5 target cleaning/model training
until the selected target's definition, units, row-level values, and source
mapping are independently supported by authoritative evidence.
