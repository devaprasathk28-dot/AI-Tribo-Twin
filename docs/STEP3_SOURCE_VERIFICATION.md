# Step 3 — Data Audit and Source Verification

**Status:** Source-row verification complete for the three available DOCX
records. Scientific target definitions and selected paper claims remain
unresolved. The raw dataset is not approved for ML training.

## Files inspected

- `data/raw/tribological_experiments_raw.csv`
- `data/raw/README.md`
- `docs/DATA_DICTIONARY.md`
- `docs/DATA_AUDIT.md` (previous audit, updated)
- `data/validation/STEP3_PRELIMINARY_VALIDATION.md` (previous preliminary
  report; its source-availability limitation is superseded by this report)
- `data/validation/README.md`
- `README.md`
- Project source/test files. No validation script was found; `tests/` contains
  only `tests/__init__.py`.

The three DOCX files and the PDF were found in `C:\Users\devap\Downloads`, not
in the project or the Step 2 extraction-package folder:

| Source | Tables found | Relevant structure |
|---|---:|---|
| `Wear test FeTiO3 and SiO2 L27 orthogonal array.docx` | 8 | Tables 0–3: nine wear-test records each; tables 4–7: separate before/after weight and weight-loss tables |
| `Wear test TiO2 and SiO2 L9 orthogonal array (5).docx` | 4 | Four tables of nine wear-test records |
| `WEAR TEST ZrSiO4 and TiO2 fillers.docx` | 4 | Four tables of nine wear-test records |
| `Tribological Properties.pdf` | 31 pages shown by local PDF viewer | Embedded text was extracted and relevant pages were visually inspected during Step 3.5 using a project-local review copy verified byte-identical by SHA-256. Printed page numbers were not visible in the captured areas; the review records PDF page numbers and zero-based indices separately. See `docs/SCIENTIFIC_SOURCE_REVIEW.md`. |

## Row-level verification results

| Result | Count |
|---|---:|
| CSV records | 108 |
| Exact `raw_cells_json` matches to indexed source table row | 108 |
| Mismatches | 0 |
| Unverified records | 0 |
| Mapped raw-field comparisons | 1,116 |
| Mapped-field mismatches | 0 |

Verification used the exact `source_document`,
`source_table_index_zero_based`, and `source_row_index_zero_based` values from
each CSV record. DOCX table cells were read from the original Word XML. Word
horizontal `gridSpan` cells were expanded and vertical-merge continuation
cells resolved from their merged source cells before comparing the ordered
strings with `raw_cells_json`. This accounts for the duplicated cells retained
for FeTiO3 table 0. Source field positions were mapped using each table's
header layout; FeTiO3 table 0 has a different merged-cell layout from its
other three wear tables.

Every record's canonical raw measurement/input fields match the mapped source
cell strings. The row-level register contains the CSV and source cell arrays,
source path, row/table indices, comparison outcomes, and evidence for all 108
records:

- [`ROW_LEVEL_SOURCE_VERIFICATION.csv`](../data/validation/ROW_LEVEL_SOURCE_VERIFICATION.csv)

## Structural and quality checks

- Schema: 108 rows; 25 expected columns; all rows have a consistent width.
- Material categories: FeTiO3:SiO2 36; TiO2:SiO2 36; ZrSiO4:TiO2 36.
- Provenance groups: 12 groups, each with nine records and sample numbers 1–9.
- Duplicate `record_id`: 0. Duplicate source document/table/row keys: 0.
- Duplicate source raw rows within a source table: 0.
- Invalid `raw_cells_json`: 0.
- CSV values have no declared type metadata and are read as strings. Numeric
  parseability was checked separately: all checked numeric fields parse except
  two COF strings. `RAW-096` is exactly `0. 29`;
  `RAW-105` is exactly `0. 36`. Both are retained unchanged and match their
  source rows.
- Missing CSV cells: test remarks 72; temperature 72; specific wear rate 108;
  wear volume loss 108; source table label 72. All other CSV fields have zero
  blanks. The meaning of blank fields is source-specific and not universally
  a missing measurement.
- Fourteen measurement signatures are identical across the FeTiO3:SiO2 and
  TiO2:SiO2 sets (28 records). Each has its own exact DOCX row match. Whether
  these represent intentionally shared controls or duplicated measurements
  is unknown; none were removed.
- The raw CSV SHA-256 before and after audit is
  `bc4b438bfcb472bdb92d653953b23acd3ff20dbaf3e0220704aa0a16bddedd1d`.

Detailed checks and missingness counts are in
[`DATA_QUALITY_REPORT.csv`](../data/validation/DATA_QUALITY_REPORT.csv).

## Scientific issues

### Confirmed from the source DOCX files

- FeTiO3 wear-table heading: `Wear rate(Micron)(x10-6 m3/m)`.
- TiO2:SiO2 and ZrSiO4:TiO2 wear-table headings: `Wear rate (Micron)` and a
  separate `Specific Wear rate (m3/Nm)` column. The separate column is blank
  in all 72 rows where it exists. FeTiO3 tables have no separate specific
  wear-rate column.
- No inspected wear table gives a row-level column identified as wear volume
  loss. The FeTiO3 record has additional tables 4–7 with `Before Weight`,
  `After Weight`, and `Weight Loss` for 36 samples. They are not labeled wear
  volume and are not substituted or converted.
- The ZrSiO4 record filename and group labels identify ZrSiO4:TiO2.
- TiO2 and ZrSiO4 composition paragraphs explicitly state paired component
  proportions. The FeTiO3 table labels do not expressly state the split
  between the two components; the CSV's split remains provisional there.

### Paper claims reviewed in Step 3.5; interpretation still unresolved

- Embedded paper text on p. 12 reports COF values of 0.300–0.303, and pp. 13
  and 15–17 describe/plot similar values. The DOCX records contain wider
  row-level ranges. The paper narrative is now text-verified, but it is not
  known whether it summarizes the same experimental runs.
- Extracted paper text/results figures and the DOCX records identify
  ZrSiO4:TiO2. Step 3.5 visual review confirmed the methodology flowchart on
  PDF page 9 instead reads ZrSiO4:SiO2; the contradiction is unresolved
  pending author clarification.
- The paper describes wear rate as volume loss normalized over load and
  sliding distance. Visual review found no symbolic equation in the visible
  method text. Page 12 visibly prints specific-wear notation `mm³/Nm` and
  `×10⁻⁶`, while the DOCX headings differ and the separate specific-wear cells
  are blank where present. Their mapping remains unresolved.
- The paper's abstract, narrative, and figure text report wear-volume-loss and
  specific-wear-rate summaries. Visual review of Figures 11–13 found
  group-level wear-volume plots with no axis unit and no sample-level mapping;
  the verified DOCX rows do not provide corresponding traceable values.

All unresolved issues, evidence, and disposition are listed in
[`SOURCE_ISSUES.csv`](../data/validation/SOURCE_ISSUES.csv) and the Step 3.5
[`SCIENTIFIC_AMBIGUITIES.csv`](../data/validation/SCIENTIFIC_AMBIGUITIES.csv).

## Validation execution

No project validation script was present. The available test command was run
from `.venv`:

```text
python -m pytest -q
no tests ran in 0.05s
exit code 5
```

The Step 3 inline audit checks completed with 108/108 source-row matches,
1,116/1,116 mapped-field matches, and no source mismatches.

## Independent review (2026-10-09)

An independent read-only recheck found the three DOCX files at the paths listed
above. Re-expanding their Word table grid spans and merged cells and comparing
each source row to `raw_cells_json` again yielded 108 exact matches and zero
mismatches. The verification manifest also has 108 rows, one for each raw
record; every manifest row is `VERIFIED_EXACT`, its CSV and source cell arrays
agree with the raw CSV and the source DOCX row, and there are no manifest
disagreements. Its `canonical_fields_compared` counts sum to 1,116 and its
canonical mismatch fields are empty.

The recheck confirmed the existing missing-value counts, source categories and
table-level filler labels. Blank specific-wear-rate and wear-volume-loss fields
remain blank; no empty cell was replaced with zero or an assumed measurement.
The numeric zeros found in the CSV are source filler-level labels/interpretive
values, not imputed missing values. The 14 cross-material matching signatures
are identical measured conditions across two material labels, not proven
duplicate rows: they have distinct source records and exact matches in their
respective documents.

### Audit-artifact corrections made during independent review

1. In `SOURCE_ISSUES.csv`, changed the COF range text from the corrupted
   `0.300?0.303` to `0.300 to 0.303`. The replacement separator did not change
   either endpoint or imply a new source claim.
2. In `SOURCE_ISSUES.csv`, limited SI-004's affected IDs to the 72 TiO2:SiO2
   and ZrSiO4:TiO2 rows whose source tables contain a separate specific-wear
   rate column. The other 36 FeTiO3 rows have no such source column; they are
   still counted as blank in the standardized CSV field, but are not source
   cells missing from a present column.
3. In `SOURCE_ISSUES.csv`, changed SI-007's scope and affected IDs from 81
   nonzero-filler rows to the 27 nonzero FeTiO3:SiO2 rows. The uncertainty
   concerns the FeTiO3 split: its document labels give the pair and level but
   do not state component proportions. The paired TiO2 and ZrSiO4 proportions
   are explicit in their source paragraphs, and zero-filler records do not
   require a component split.

No raw measurement or source transcription was edited.

## Disposition and next step

The source transcription is verified against the located DOCX files, but the
dataset remains scientifically unaudited for model use. Keep the raw CSV
unchanged. Next, obtain an accessible/searchable paper text and primary
clarification for the wear target/units, paper COF claims, Zr filler naming,
FeTiO3 component proportions, and matching measurement signatures. Only after
those questions are recorded and reviewed should a separately documented
processed dataset be considered.
