# Step 3.5 — Scientific Source Review

**Status:** The paper's text layer was locally extracted and reviewed for the
claims listed below. Some paper statements are now confirmed as statements in
the paper, but the correspondence between those claims and the row-level DOCX
records remains unresolved. No target is approved for ML training.

## Scope and extraction method

The paper was found at
`C:\Users\devap\Downloads\Tribological Properties.pdf` (837,437 bytes; 31
pages in the local PDF viewer). The environment had no `pdftotext`, `pdfinfo`,
`mutool`, or `tesseract` command and no `pypdf`, `PyPDF2`, `pdfplumber`,
`PyMuPDF`/`fitz`, `pdfminer`, `pytesseract`, or OCR package installed.

Instead of installing dependencies, the PDF's local content streams were
inspected with Python's standard library: the PDF objects were read, Flate
streams decompressed with `zlib`, and text strings reconstructed from the
page content streams using the embedded font maps. This confirmed extractable
text on the paper pages; the PDF is not solely a scanned image. The viewer initially allowed visual inspection of the title page only. A
follow-up visual review was completed using a temporary project-local copy of
the original PDF. The review copy SHA-256 matched the original:
`C72EEFB8294C9890FF5D2AA7BA09AAAE755CA9EA3C98BCDE2310E9DDC9C5ECCD`.
No PDF-rendering or OCR package/command was installed. Some superscript
characters were legible in the viewer and are reported below only where
visually confirmed.

The three DOCX source records remain available under `C:\Users\devap\Downloads`.
Their table headings, cell values, table labels and group paragraphs were
compared with the raw CSV during Step 3. The paper narrative and graphs are
reported separately from these row-level observations.

## Visual PDF review

The viewer's page count is 1-based. The zero-based PDF index is given
separately below. Printed page numbers were not visible in the captured page
areas and are not inferred.

| PDF page (1-based) | Zero-based PDF index | Printed page | Visual evidence |
|---:|---:|---|---|
| 1 | 0 | Not visible | Title and authors were visible; only the start of the abstract entered the viewport, so no abstract measurement claim was assessed visually. |
| 8 | 7 | Not visible | Composite-fabrication prose and a filler image/caption were visible; no row-level results or target definition were assessed on this page. |
| 9 | 8 | Not visible | Methodology flowchart reads `FeTiO3:SiO2, TiO2:SiO2 & ZrSiO4:SiO2`; listed filler proportions are `(0:0, 2.5:2.5, 5:5, and 7.5:7.5 wt %)`. The ZrSiO4:SiO2 label is legible. |
| 10 | 9 | Not visible | Visible method text names ASTM G99, equipment sliding-speed range 0.26–10 m/s, and 10 N/0.96 m/s for the described COF test. No symbolic COF or wear-rate equation is displayed in the visible method text. |
| 11 | 10 | Not visible | Figure 3 is captioned `Pin on Disc equipment`; the equipment image is visible. |
| 12 | 11 | Not visible | Narrative states COF ranged from 0.300 to 0.303 and visibly prints specific-wear-rate values with `mm³/Nm` and `×10⁻⁶`. These are paper-level values, not DOCX row observations. |
| 13 | 12 | Not visible | Text discusses Figure 5 as specific wear rate by sliding distances 100, 200, and 300 m and filler concentrations; this is a grouped result, not a sample-level table. |
| 14 | 13 | Not visible | Graph y-axis reads `SPECIFIC WEAR RATE`, without a unit on the axis. |
| 15 | 14 | Not visible | COF graph groups values by filler level and sliding distances 100, 200, and 300 m; plotted values are around 0.300–0.303. |
| 16 | 15 | Not visible | Figure 9 caption identifies TiO2 & SiO2; plotted COF values are around 0.300–0.303. |
| 17 | 16 | Not visible | Figure 10 caption identifies ZrSiO4 & TiO2; plotted COF values are around 0.300–0.303. |
| 18 | 17 | Not visible | Figure 11 is captioned as FeTiO3:SiO2 wear volume loss. Axis reads `WEAR VOLUME LOSS` with no unit; bars are grouped by filler and sliding distance. |
| 19 | 18 | Not visible | Figure 12 is captioned as TiO2:SiO2 wear volume loss. Axis reads `WEAR VOLUME LOSS` with no unit; bars are grouped by filler and sliding distance. |
| 20 | 19 | Not visible | Figure 13 is captioned as ZrSiO4:TiO2 wear volume loss. Axis reads `WEAR VOLUME LOSS` with no unit; bars are grouped by filler and sliding distance. |
| 25 | 24 | Not visible | Conclusion states specific wear rate `0.5 mm³/Nm`, COF `0.3`, and wear volume loss `1.5 mm³` at 300 m and 1 m/s. The scale/notation does not reconcile with p. 12. |

The flowchart discrepancy is now visually confirmed, not merely reported in
the prior audit. Paper results text/figures and the DOCX records identify
ZrSiO4:TiO2, but the flowchart says ZrSiO4:SiO2. This direct contradiction
requires author clarification.

The COF graphs visually corroborate the paper's narrow grouped range; they do
not reconcile it with the much wider DOCX row-level ranges. The graphs show
filler level and sliding distance, but no sample IDs or row-level table that
links plotted values to the 108 DOCX records. The original DOCX headings were
checked: FeTiO3 uses `Wear rate(Micron)(x10-6 m3/m)`, while the TiO2 and
ZrSiO4 records use `Wear rate (Micron)` and `Specific Wear rate (m3/Nm)`.
That separate specific-wear column is blank in the verified records. Paper
narrative notation is visually legible but does not establish which DOCX
column it represents. The paper's wear-volume plots are grouped summaries and
give no axis unit or row-level mapping.

## Paper claims and comparison with experimental records

Locations below use the PDF's 1-based viewer page number. Excerpts are from
the embedded text layer; spacing and formulas may be affected by PDF text
layout. `[unmapped glyph]` explicitly marks a character the extraction did not
reliably recover.

| Topic | Paper evidence | DOCX/raw-record evidence | Assessment |
|---|---|---|---|
| COF definition | The text-layer extraction records: “the coefficient of friction is derived by dividing the frictional force by the normal load.” Visual review located the method discussion on PDF viewer p. 10 (zero-based index 9); its visible text discusses test settings but shows no symbolic equation. | The DOCX tables have row-level COF columns. Numeric strings span 0.216–0.962 in FeTiO3:SiO2 (36 parseable rows), 0.161–0.821 in TiO2:SiO2 (36 rows), and 0.16–0.721 in ZrSiO4:TiO2 (34 parseable rows). `RAW-096`=`0. 29` and `RAW-105`=`0. 36` are preserved source strings that do not parse as decimals. | The paper gives a physical definition in prose, but its summary/figure claims do not reconcile with the row-level values or documented test conditions. |
| COF narrative/figures | p. 12: “the coefficient of friction ranged from 0.300 to 0.303.” pp. 13 and 15–17 also describe or plot values around 0.300–0.303 for the filler systems/sliding distances. | DOCX COF values are the row-level values above, including source-confirmed formatting anomalies. The prior Step 3 mapping compared every row to its own DOCX row; it did not reconcile this paper-level narrative. | **Unresolved.** The paper's prose/figure summary is not a substitute for DOCX observations. It is unclear whether the paper summaries describe the same runs, an aggregate, or a different dataset. |
| Wear-rate definition | The text-layer extraction describes wear rate as volume loss normalized over applied load and sliding distance. Visual review of the method on PDF viewer p. 10 (zero-based index 9) found no symbolic equation in the visible text. | FeTiO3 DOCX header: `Wear rate(Micron)(x10-6 m3/m)`. TiO2:SiO2 and ZrSiO4:TiO2 DOCX headers: `Wear rate (Micron)`. The CSV's `wear_rate_value_raw` contains 108 numeric source strings; it is not established that these are the paper's volume-loss-normalized wear rate. | **Unresolved.** The paper provides a prose definition but its relationship to the numeric DOCX `Wear rate` fields and inconsistent headings is not established. |
| Specific wear-rate units | Visual inspection of p. 12 shows narrative values with `mm³/Nm` and `×10⁻⁶`; p. 25 visibly says `0.5 mm³/Nm` without the same exponent. The p. 14 graph axis says `SPECIFIC WEAR RATE` but gives no unit. | The TiO2:SiO2 and ZrSiO4:TiO2 tables have a separate `Specific Wear rate (m3/Nm)` column, blank in all 72 rows. The FeTiO3 wear-test tables do not have a separate specific-wear-rate column. | **Unresolved.** Narrative unit notation is now legible, but its scale varies within the paper and does not establish a populated, row-level target or mapping to the DOCX columns. |
| Specific wear-rate values | p. 12 visually shows narrative values including `1×10⁻⁶ mm³/Nm`, `1.05×10⁻⁶ mm³/Nm`, and `0.98×10⁻⁶ mm³/Nm`. p. 25 conclusion states `0.5 mm³/Nm` without the same exponent. Other text-layer values are not used to repair or normalize these claims. | The table rows provide numeric values under “Wear rate”, not row-level specific-wear values. The separate specific-wear column is blank where present. | **Unresolved and internally unclear.** Do not infer exponents, reconcile the reported values, or transform `wear_rate_value_raw` into a specific-wear target. |
| Wear volume loss | Visual inspection of pp. 18–20 shows Figures 11–13 titled as wear-volume-loss plots. Their y-axes say `WEAR VOLUME LOSS` but show no units. The plots group values by filler level and sliding distance, without sample IDs or a row-level table. p. 25 conclusion states `1.5 mm³` at 300 m and 1 m/s. | No row-level wear-volume-loss column occurs in the DOCX wear-test tables. The FeTiO3 DOCX has separate `Before Weight`, `After Weight`, and `Weight Loss` tables for 36 samples, but those are not labeled volume loss and have no established conversion to it. | **Unresolved/unavailable at row level.** The paper provides group-level plotted/conclusion values, not traceable values for the 108 rows. Do not substitute weight loss or calculate volume. |
| Material identity | Text on pp. 1, 11, 14, 17, and 20 and captions for Figures 10 and 13 identify ZrSiO4:TiO2. Visual inspection of the p. 9 methodology flowchart confirms the conflicting label `ZrSiO4:SiO2`. | The third experimental-record filename and its preceding group labels identify ZrSiO4 and TiO2. All 36 corresponding CSV rows are labeled ZrSiO4:TiO2 and match their DOCX table rows. | **Author clarification required.** The conflict is directly visible in the paper; majority usage does not resolve which material pair was actually tested. |
| Test conditions / source relationship | Visual inspection of p. 10 shows method text referring to 10 N and 0.96 m/s for the described COF test; pp. 15–20 show grouped plots at 100, 200, and 300 m for filler levels, without row IDs. | The DOCX tables include loads of 10, 20, and 30 N; speeds including 0.5–2 m/s; and distances including 50–300 m. These table values were source-verified in Step 3. | **Author clarification required.** The paper's visible method/plot conditions do not establish the relationship between the plots and all DOCX rows. |
| Methodology text integrity | p. 2 includes a passage about aluminum metal-matrix composites and boron carbide/graphite. p. 10 mentions “both IPC and PC” and SiC abrasive paper while describing COF instability. These passages are present in the extracted PDF text. | They do not describe the three source DOCX table sets as named and require contextual checking against the intended study. | **Potential document contamination/copy-edit issue.** This observation does not by itself invalidate measurements, but it reduces confidence in uncorroborated narrative descriptions. |

The full issue-level evidence and status are in
[`SCIENTIFIC_AMBIGUITIES.csv`](../data/validation/SCIENTIFIC_AMBIGUITIES.csv).

## Confirmed facts

- The PDF contains extractable text and the title page matches the paper name
  already recorded in project documentation.
- Visual review confirmed the p. 9 methodology flowchart reads
  `ZrSiO4:SiO2`; it is not a text-extraction artifact.
- Paper results text and Figures 10/13 identify ZrSiO4:TiO2, as do the
  available ZrSiO4 DOCX and its 36 verified CSV rows. The source conflict
  remains unresolved.
- Paper p. 12 visibly states COF 0.300–0.303; the visual COF charts on pp.
  15–17 plot group-level values in the same narrow range. This is in conflict
  with much wider row-level COF values in the DOCX records.
- The visible paper method text on p. 10 has no symbolic equation; paper
  narrative on p. 12 prints specific-wear notation `mm³/Nm` with `×10⁻⁶`.
  The DOCX uses different `m3/Nm` heading text and has blank specific-wear
  cells where that column exists.
- Figures 11–13 visibly label the y-axis `WEAR VOLUME LOSS` but provide no
  unit and no row-level sample mapping. The conclusion reports group-level
  values, not measurements traceable to the 108 DOCX rows.
- The source DOCX tables' wear headings differ by material source. The
  separately labeled specific-wear field is blank in 72 rows where it exists;
  the FeTiO3 tables have no such column.
- Paper-level summary numbers are not equivalent evidence to individual DOCX
  table measurements.

## Unresolved / requires clarification

- Whether the paper's COF narrative and figures summarize the same experiments
  as the 108 DOCX rows; the paper states roughly 0.300–0.303, while source rows
  span substantially wider ranges.
- Whether the DOCX `Wear rate` numbers denote a common measurement across all
  material systems and how their headings/units map to the paper's prose
  `wear rate` and `specific wear rate`.
- The paper's specific-wear notation/scale across the paper: p. 12 visibly
  uses `×10⁻⁶ mm³/Nm`, while p. 25 states `0.5 mm³/Nm` without that exponent.
  The relation of either statement to the source table columns is unknown.
- Whether any row-level wear volume loss exists outside the inspected DOCX
  tables; the paper's abstract/figures do not provide a traceable row-level
  field in the available records.
- Which Zr filler pairing was actually used: the flowchart says
  ZrSiO4:SiO2, while results text/figures and DOCX records say ZrSiO4:TiO2.
- Whether the DOCX conditions extend the paper's described matrix or represent
  separate experiments.
- Whether unrelated-looking methodology passages in the PDF are intentional
  literature/context or document contamination.

## Decision for responsible ML use

| Variable / concept | Sufficiently defined for ML using this raw dataset? | Decision basis |
|---|---|---|
| COF | **No — blocked** | Physical definition is stated, but paper summary/figure values conflict with the row-level DOCX values and experiment conditions have not been reconciled. Preserve raw strings. |
| Wear rate | **No — blocked** | Paper definition is prose; source-table headings and apparent unit expressions conflict across the three records. |
| Specific wear rate | **No — blocked** | The paper's `mm³/Nm` notation is visually legible, but its scale varies across narrative claims and does not map to the blank/absent source-record fields. |
| Wear volume loss | **No — blocked** | Paper reports aggregate/figure claims, but the DOCX records do not contain row-level volume-loss values; weight-loss records are not interchangeable. |
| Material identity | **No — author clarification required** | The flowchart visually says ZrSiO4:SiO2, while results text/figures and the DOCX records identify ZrSiO4:TiO2. |

## Recommendation

Do not proceed to target cleaning or ML. Request the authors' original
measurement sheet or written clarification for: (1) the mapping and units of
the `Wear rate` and `Specific Wear rate` columns; (2) COF results and the
relationship between paper plots/narrative and DOCX records; (3) row-level
wear-volume-loss data and its measurement method; (4) the intended filler pair
in the flowchart and the FeTiO3:SiO2 component proportions; and (5) the
relationship between the paper's stated test matrix and the DOCX conditions.
The visual review has been completed for the cited pages; the remaining step
is author/source clarification. Do not proceed to Step 4 or ML until the
row-level target mappings/units, COF discrepancy, and material-pair conflict
are resolved with primary evidence.
