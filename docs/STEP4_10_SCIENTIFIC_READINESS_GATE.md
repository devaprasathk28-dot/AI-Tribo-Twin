# AI-TriboTwin — Step 4.10 Scientific Readiness Gate

## Decision

**NO-GO for supervised model training, predictive evaluation, and optimization.**
All four candidate response targets remain **BLOCKED**. No target is released
by the presence of a CSV column, numeric-looking values, a paper-level summary,
or the source transcription checks alone.

This gate synthesizes the existing project evidence. It does not claim a new
page-by-page paper inspection or a new comparison against the original DOCX
files. The source review, source-verification manifest, audit, and issue
registers record the prior inspections and their scope. The machine-readable
decisions are in
[`../data/validation/STEP4_10_READINESS_GATE.csv`](../data/validation/STEP4_10_READINESS_GATE.csv).

## Target-by-target decision

| Target | Decision | Evidence basis and reason |
|---|---|---|
| Coefficient of friction (COF) | **NO-GO — BLOCKED** | There are 108 raw strings, but only 106 parse as decimals; `RAW-096` (`0. 29`) and `RAW-105` (`0. 36`) are source-confirmed formatting anomalies. The paper reports roughly 0.300–0.303 while the DOCX-verified row-level ranges are much wider. No run-to-figure mapping reconciles them. The quantity is dimensionless, but that alone does not establish which observations the paper claims represent. See `TARGET-COF`, `SA-001`, `SI-001`, and `SI-002`. |
| Wear rate / raw wear-related measurement | **NO-GO — BLOCKED** | All 108 values are numerically parseable, but the source headings differ by material system and do not establish a common response definition, unit, scale, or mapping to the paper's prose. Numeric completeness does not establish scientific validity or comparability. See `TARGET-WEAR`, `SA-002`, and `SI-003`. |
| Specific wear rate | **NO-GO — BLOCKED** | All 108 raw CSV target cells are blank. A separate source column is blank in 72 rows and absent from the FeTiO3 table layout for 36 rows. Paper-level notation and scales are not consistently reconciled and do not provide row-level measurements. See `TARGET-SWR`, `SA-003`, and `SI-004`. |
| Wear volume loss | **NO-GO — BLOCKED** | All 108 raw CSV target cells are blank. The cited paper plots are grouped summaries without visible units or sample-level identifiers; the conclusion value is not a row-level observation. Separate weight-loss records are not volume-loss measurements. See `TARGET-WVL`, `SA-004`, and `SI-005`. |

The source records support the conclusion that the raw CSV transcription matches
the indexed DOCX rows; they do not prove that the DOCX runs correspond to the
paper's figures or that a populated wear field means the same thing across
systems. Preserve both statements as distinct evidence.

## Missing measurements versus measured values with quality issues

- **Measured values with quality/meaning issues:** COF has 108 source strings,
  including two non-decimal strings preserved verbatim. The wear-related field
  has 108 numeric-like values. These entries exist, but the COF reconciliation
  and wear measurement semantics/units remain unresolved. Their existence is
  not approval to coerce, correct, convert, or train on them.
- **Missing response measurements:** Specific wear rate and wear volume loss
  have no populated row-level values in the raw CSV. The available grouped
  figures or aggregate paper statements cannot supply missing rows. Do not
  digitize plots, derive values from wear rate or weight loss, or impute them.

The raw file remains immutable. Any future processing must create a separate,
documented dataset only after a target passes its evidence gate.

## Material identity and source-to-run traceability

Material identity is not fully verified for the intended experiment scope.
The paper's methodology flowchart says `ZrSiO4:SiO2`, while the results and
associated DOCX records say `ZrSiO4:TiO2`. The majority label does not establish
which formulation was prepared. The FeTiO3 filler-component split is also not
fully source-confirmed. Before treating material composition as an input,
require an authoritative preparation/composition record or confirmation tied
to actual sample labels and runs.

The 108-row manifest verifies CSV-to-DOCX transcription. It does not map each
record to the paper's reported methods, plotted results, or aggregate claims.
Require stable experimental identifiers linking each run to material and
filler composition, load, velocity, distance, measured response, source table,
and relevant paper figure/table. Preserve contradictory mappings and assess
them individually; do not choose one silently.

## Leakage, dependence, confounding, and sample-size risks

The existing audit describes 108 rows across 12 source-table groups and 14
identical cross-material measurement signatures affecting 28 rows. The
signatures may represent shared controls or duplicated measurements; their
status and independent experimental units are unknown. A random row split
could put linked design patterns in both training and test sets.

Other risks documented in the Step 4 readiness report include:

- Source document/table, row position, sample number, and extraction metadata
  can reveal cohort or design and should not be treated as ordinary physical
  predictors.
- Load, velocity, distance, rpm, diameter, duration, filler level, and
  material system may be mechanically related, structurally tied to the
  orthogonal-array design, or confounded with source/system.
- COF and wear responses are post-test outcomes; using one as a predictor for
  another may leak outcome information unless it is demonstrably available at
  the intended prediction time.
- There are only 36 records per material label and 9 rows per source-table
  group. The number of independent experiments is not established; 108 rows
  must not be treated as 108 independent experimental units.
- The systems have differing condition ranges and recorded protocols. Transfer
  across materials or to unseen conditions cannot be inferred from a random
  split or an apparently high score.

No defensible split or cross-validation grouping can be selected until run,
batch, replicate, and shared-control identifiers are verified. Once evidence
supports a target and grouping, use leakage-aware grouped evaluation aligned
to the stated use case; explicitly distinguish in-domain interpolation from
held-out-condition/material extrapolation. Independent physical validation
will still be required for claims beyond the supported experimental domain.

## What can responsibly proceed now

The following work can proceed without response targets, provided it remains
descriptive and read-only:

- Inspect and document the source schema, provenance, literal value forms,
  missingness, and current evidence gaps.
- Produce descriptive summaries of observed **input** fields without
  converting or overwriting raw values, and label provisional or unresolved
  composition interpretations as such.
- Plan additional experiments and records needed to establish response
  measurements, material identity, independent experimental units, and
  evaluation groups.
- Improve provenance and acquisition templates for future records.

Do not represent these activities as predictive analysis, target validation,
causal inference, or optimization. Do not build a cleaned training dataset or
use ambiguous source labels as verified composition.

## Minimum evidence required to reconsider each target

1. **COF:** Original per-run measurements or an authoritative run-to-figure
   mapping; the measurement protocol and test conditions; explanation of how
   the paper's narrow range relates to the raw rows; and documented disposition
   of the two anomalous strings without changing the raw file.
2. **Wear rate:** Table-specific operational definition, measurement procedure
   and calibration, formula, exact units and scale, source-column mapping, and
   evidence that values are comparable across the intended systems.
3. **Specific wear rate:** Authoritative definition, formula and units/scale,
   plus original row-level values tied to stable run identifiers. A definition
   or confirmation that values once existed is not a substitute for the
   measurements.
4. **Wear volume loss:** Original row-level values, explicit units and
   measurement method/calibration, condition/run identifiers, and mapping to
   source rows and published results. Neither grouped plots nor weight loss
   qualifies.
5. **All targets and material inputs:** Authoritative material/preparation
   records, source-to-run and run-to-paper traceability, a documented
   disposition of contradictions, and independent-run/replicate/shared-control
   identifiers sufficient to assess dependence and leakage.

The evidence must be preserved with provenance and reviewed against the
existing PDF/DOCX review records, source manifest, raw CSV, and issue registers.
An author statement can clarify an explicit fact but cannot create absent
row-level measurements.

## Conditions before modeling or optimization

Before **training**, at least one target must have an unambiguous operational
definition, verified units and measurement procedure, traceable row-level
values, documented material/condition semantics, and evidence-based
dispositions for missingness, anomalies, and source contradictions. Existing
`TARGET_READINESS.csv` must be deliberately updated with linked evidence only
after independent review.

Before **evaluation**, also establish the independent experimental unit and
group keys, address repeated signatures/shared controls, exclude identifiers
and post-test leakage, justify the split for the intended prediction scope,
and ensure sufficient independent data for meaningful uncertainty and
subgroup reporting. Report the small-data limitations; do not claim
generalization beyond the tested domain.

Before **multi-objective optimization**, every optimized response must
independently pass its target gate; objective units, directions, constraints,
and feasible domain must be experimentally supported. Optimization must not
be used to bypass missing response values or uncertainty about the material
and process. Predicted optima would require prospective physical validation
before being described as experimentally supported.

## Validation and disposition

At this gate, the raw CSV was inspected read-only: it contains 108 rows and 25
columns; its recorded SHA-256 is unchanged; `0. 29` and `0. 36` remain verbatim;
and the specific-wear-rate and wear-volume-loss columns are blank in all 108
rows. The source-verification manifest remains 108 rows. Existing
`TARGET_READINESS.csv` decisions remain `BLOCKED` for COF, wear, specific wear
rate, and wear volume loss. Existing source-audit artifacts are referenced,
not overwritten.

No model training, optimization, synthetic target creation, raw-data edit, or
cleaned training dataset creation was performed. The current gate result is
**NO-GO for all response targets**.

## Exact next human action

Verify the paper-listed corresponding-author contact against an official
institutional or publication channel. If verified, decide whether to send the
approved clarification request manually. Request the primary row-level records
and mappings listed above, along with material/preparation and independent-run
identifiers. Record only the actual outreach event and preserve any reply or
attachments as received. Until evidence is archived and reviewed, keep all
targets `BLOCKED` and modeling/optimization on hold.
