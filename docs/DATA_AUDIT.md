# Data Audit

## Current status

The raw extraction has now been compared against the three original test-record
DOCX files located in `C:\Users\devap\Downloads`. All 108 CSV rows match the
source row identified by the CSV's document, zero-based table index, and
zero-based row index. This verifies transcription against those DOCX files; it
does not resolve the scientific meaning of every column or reconcile the
records with the paper.

**The CSV remains raw and is not approved for model training.** No source values
were changed, no duplicates were removed, and no cleaned dataset was created.

Detailed evidence is in
[`STEP3_SOURCE_VERIFICATION.md`](./STEP3_SOURCE_VERIFICATION.md) and the
row-level and issue registers under `data/validation/`.

## Sources inspected

- `C:\Users\devap\Downloads\Wear test FeTiO3 and SiO2 L27 orthogonal array.docx`
  — 8 Word tables: the first four are the 0%, 5%, 10%, and 15% wear-test
  tables; tables 4–7 are separate before-weight/after-weight/weight-loss tables.
- `C:\Users\devap\Downloads\Wear test TiO2 and SiO2 L9 orthogonal array (5).docx`
  — 4 wear-test tables.
- `C:\Users\devap\Downloads\WEAR TEST ZrSiO4 and TiO2 fillers.docx`
  — 4 wear-test tables.
- `C:\Users\devap\Downloads\Tribological Properties.pdf` was located. Its
  embedded text was extracted locally with Python's standard library and
  reviewed for Step 3.5. A later visual review inspected cited result pages
  and confirmed the methodology flowchart label; printed page numbers were
  not visible in the captured areas. See
  [`SCIENTIFIC_SOURCE_REVIEW.md`](./SCIENTIFIC_SOURCE_REVIEW.md) for
  page-level excerpts and remaining limitations.

## Confirmed CSV and provenance checks

- The CSV contains 108 rows and 25 columns, with the expected header sequence
  documented in `docs/DATA_DICTIONARY.md`.
- The material labels are FeTiO3:SiO2 (36 rows), TiO2:SiO2 (36 rows), and
  ZrSiO4:TiO2 (36 rows).
- Twelve source-document/table groups contain nine records each. In each group
  sample numbers 1–9 occur once.
- All 108 records have an exact `raw_cells_json` match to their indexed DOCX
  row. The comparison expands Word `gridSpan` cells and vertical-merge
  continuations so the source-cell sequence is compared in the same expanded
  layout retained by the extraction.
- 1,116 source-to-CSV comparisons of mapped raw measurement/input fields
  returned no mismatches.
- There are no duplicate record IDs, duplicate source-document/table/row keys,
  repeated raw rows within one source table, or invalid `raw_cells_json`
  values.
- Fourteen identical measurement signatures occur in both the FeTiO3:SiO2 and
  TiO2:SiO2 datasets (28 records total). Each record matches its own source
  row. These may be shared controls or duplicated measurements; they are
  retained pending investigation.
- The raw CSV SHA-256 before and after verification was
  `bc4b438bfcb472bdb92d653953b23acd3ff20dbaf3e0220704aa0a16bddedd1d`.

## Data-quality findings

- `coefficient_of_friction_raw` has two strings that fail numeric parsing:
  `RAW-096` is `0. 29`, and `RAW-105` is `0. 36`. Both strings are present
  verbatim in the matching DOCX source rows. They are formatting anomalies,
  not corrected values.
- Numeric parsing succeeds for every other checked numeric input and
  `wear_rate_value_raw` field.
- A CSV does not carry declared field types; values were read as text and
  validated for numeric parseability separately. The material-system
  categories and 0%, 5%, 10%, and 15% filler-level labels match the inspected
  source tables. The only numeric parse failures are the two COF formatting
  anomalies above.
- Missing-value counts are: `test_remarks_raw` 72,
  `temperature_raw` 72, `specific_wear_rate_raw` 108,
  `wear_volume_loss_raw` 108, and `source_table_label_raw` 72. Other columns
  have no blank CSV cells. Source-column/context meaning is described in the
  Step 3 report.
- The source uses both `Std. atm.` and `Std.atm.` temperature strings. They
  match the source and remain unnormalized.
- The TiO2:SiO2 and ZrSiO4:TiO2 group labels are paragraphs preceding their
  tables, rather than cells copied into `source_table_label_raw`; that CSV
  field is blank for those 72 records.

## Confirmed source facts and unresolved questions

### Confirmed in the inspected DOCX files

- FeTiO3 wear tables use the heading
  `Wear rate(Micron)(x10-6 m3/m)`.
- TiO2:SiO2 and ZrSiO4:TiO2 wear tables use `Wear rate (Micron)` and a
  separate `Specific Wear rate (m3/Nm)` column. All 72 cells in those
  specific-wear-rate columns are blank. The FeTiO3 wear tables do not have a
  separate specific-wear-rate column.
- The ZrSiO4 test-record filename and group paragraphs identify
  ZrSiO4:TiO2.
- The FeTiO3 DOCX has separate tables 4–7 headed `Before Weight`,
  `After Weight`, and `Weight Loss` for 36 samples. Those values are not
  row-level wear volume measurements, and no unit or conversion is inferred.
- The TiO2:SiO2 and ZrSiO4:TiO2 DOCX group paragraphs show paired filler
  proportions 2.5:2.5, 5:5, and 7.5:7.5 wt%. The FeTiO3 table labels give
  total-style 5%, 10%, and 15% labels for the two fillers but do not expressly
  state each component's proportion. The CSV's half-split interpretation is
  therefore not fully source-confirmed for the FeTiO3 records.

### Unresolved

- Paper p. 12 reports COF values from 0.300 to 0.303, and pp. 13 and 15–17
  describe/plot values around that range. This conflicts with the wider
  DOCX-verified row-level ranges. The paper claim is now text-verified, but
  its relationship to the DOCX rows and the stated test conditions remains
  unresolved.
- The wear-rate headings do not establish a consistent, unambiguous physical
  target or unit. Do not infer a specific wear rate or convert the numeric
  values.
- Row-level wear volume loss is not established by the three wear-table sets.
  Do not substitute weight loss or calculate missing volume values.
- Accessible PDF results text/figures and the DOCX records identify
  `ZrSiO4:TiO2`. Visual review of PDF page 9 confirms that the methodology
  flowchart instead reads `ZrSiO4:SiO2`. This is a direct source contradiction;
  retain it as unresolved pending author clarification. See
  [`SCIENTIFIC_SOURCE_REVIEW.md`](./SCIENTIFIC_SOURCE_REVIEW.md).
- The 14 cross-material matching measurement signatures require confirmation
  as shared controls versus duplicated records.

## Validation scripts and tests

No project validation script was found; `tests/` contains only
`tests/__init__.py`. `python -m pytest -q` was run in `.venv` and reported
`no tests ran` (exit code 5). CSV structure, source-row comparisons, numeric
parseability, missingness, and duplicate checks were executed directly for
this audit; their actual results are recorded in the Step 3 report and CSV
registers.

## Disposition

Preserve `data/raw/tribological_experiments_raw.csv` unchanged. Do not train,
normalize, infer units, impute missing values, or remove possible duplicates.
Resolve the open source and scientific questions before preparing a separate
processed dataset.
