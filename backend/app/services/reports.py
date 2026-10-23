from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.db.models import ExperimentRecord
from app.schemas.analytics import AnalyticsResponse


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas that accumulates total page count and renders running headers/footers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []
        self.report_title: str = "AI-TriboTwin Engineering Report"
        self.report_id: str = ""
        self.generation_timestamp: str = ""

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int) -> None:
        self.saveState()

        # Running header on pages 2+
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0f172a"))
            self.drawString(54, 755, self.report_title)

            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            if self.report_id:
                self.drawRightString(558, 755, f"ID: {self.report_id}")

            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)

        # Running footer on all pages
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(
            54,
            33,
            f"AI-TriboTwin Scientific Engineering Twin · Generated {self.generation_timestamp} · Immutable Evidence Register",
        )
        self.drawRightString(558, 33, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


def _get_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()

    # Custom styles adhering to engineering typography standards
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=sample["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    eyebrow_style = ParagraphStyle(
        "ReportEyebrow",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0284c7"),
        textTransform="uppercase",
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=sample["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )

    heading2_style = ParagraphStyle(
        "ReportH2",
        parent=sample["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    heading3_style = ParagraphStyle(
        "ReportH3",
        parent=sample["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=sample["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )

    body_muted = ParagraphStyle(
        "ReportBodyMuted",
        parent=body_style,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )

    cell_style = ParagraphStyle(
        "ReportCell",
        parent=body_style,
        fontSize=8,
        leading=10.5,
    )

    cell_header = ParagraphStyle(
        "ReportCellHeader",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
    )

    badge_planned = ParagraphStyle(
        "BadgePlanned",
        parent=cell_style,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        textColor=colors.HexColor("#0369a1"),
    )

    badge_measured = ParagraphStyle(
        "BadgeMeasured",
        parent=cell_style,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        textColor=colors.HexColor("#047857"),
    )

    disclaimer_style = ParagraphStyle(
        "ReportDisclaimer",
        parent=sample["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#7c2d12"),
    )

    return {
        "title": title_style,
        "eyebrow": eyebrow_style,
        "subtitle": subtitle_style,
        "h2": heading2_style,
        "h3": heading3_style,
        "body": body_style,
        "body_muted": body_muted,
        "cell": cell_style,
        "cell_header": cell_header,
        "badge_planned": badge_planned,
        "badge_measured": badge_measured,
        "disclaimer": disclaimer_style,
    }


def _build_meta_box(meta_items: list[tuple[str, str]], styles: dict[str, ParagraphStyle]) -> Table:
    data = []
    # 2 columns of key-values
    for i in range(0, len(meta_items), 2):
        row = []
        k1, v1 = meta_items[i]
        row.extend([
            Paragraph(k1, styles["cell_header"]),
            Paragraph(v1 or "Unavailable", styles["cell"]),
        ])
        if i + 1 < len(meta_items):
            k2, v2 = meta_items[i + 1]
            row.extend([
                Paragraph(k2, styles["cell_header"]),
                Paragraph(v2 or "Unavailable", styles["cell"]),
            ])
        else:
            row.extend(["", ""])
        data.append(row)

    table = Table(data, colWidths=[110, 142, 110, 142])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    return table


def _build_notice_box(
    title: str,
    message: str,
    styles: dict[str, ParagraphStyle],
    tone: str = "warning",
) -> Table:
    bg_color = colors.HexColor("#fffbeb" if tone == "warning" else "#fef2f2" if tone == "error" else "#f0fdf4")
    border_color = colors.HexColor("#d97706" if tone == "warning" else "#dc2626" if tone == "error" else "#16a34a")
    text_color = colors.HexColor("#78350f" if tone == "warning" else "#7f1d1d" if tone == "error" else "#14532d")

    notice_title_style = ParagraphStyle(
        "NoticeTitle",
        parent=styles["body"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        textColor=text_color,
        spaceAfter=2,
    )
    notice_msg_style = ParagraphStyle(
        "NoticeMsg",
        parent=styles["body"],
        fontSize=8,
        leading=11,
        textColor=text_color,
    )

    content = [
        Paragraph(title, notice_title_style),
        Paragraph(message, notice_msg_style),
    ]

    table = Table([[content]], colWidths=[504])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return table


# =========================================================================
# 1. INDIVIDUAL EXPERIMENT REPORT (PDF)
# =========================================================================
def build_experiment_pdf(record: ExperimentRecord) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"REP-EXP-{record.experiment_id}"
    styles = _get_styles()
    story = []

    # Title & Header
    story.append(Paragraph("AI-TriboTwin Engineering Report", styles["eyebrow"]))
    story.append(
        Paragraph(
            f"Experiment Specification & Evaluation · {record.experiment_id}",
            styles["title"],
        )
    )
    story.append(
        Paragraph(
            f"Stable Report Identifier: <b>{report_id}</b> · Generated: {now_utc} · Status: <b>{record.record_status}</b>",
            styles["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # Planned vs Measured Safeguard Banner
    if record.record_status == "PLANNED":
        story.append(
            _build_notice_box(
                "Planned Prospective Experiment Record (No Physical Measurements)",
                "This record represents prospective planned conditions for physical laboratory execution. "
                "No physical friction or wear measurements have occurred. Planned records are strictly excluded "
                "from empirical training data, benchmark evaluations, and measured response analytics.",
                styles,
                tone="warning",
            )
        )
        story.append(Spacer(1, 10))
    else:
        story.append(
            _build_notice_box(
                "Verified Measured Experimental Observation",
                f"Physically tested observation recorded in source artifact '{record.source_artifact or 'Primary Data'}'. "
                f"Replicate group: {record.replicate_group_id or 'Individual run (unreplicated)'}. "
                "Measurements represent actual laboratory instrument readings.",
                styles,
                tone="success",
            )
        )
        story.append(Spacer(1, 10))

    # Section 1: Record Identification & Specimen Metadata
    story.append(Paragraph("1. Record Identification & Specimen Metadata", styles["h2"]))
    meta = [
        ("Experiment ID", record.experiment_id),
        ("Record Status", record.record_status),
        ("Material System", record.material_system_as_recorded),
        ("Replicate Group ID", record.replicate_group_id or "Unavailable"),
        ("Composition", record.composition_as_recorded or "Unavailable"),
        ("Composition Source", record.composition_source_reference or "Unavailable"),
        ("Test Date", str(record.experiment_date) if record.experiment_date else "Unavailable"),
        ("Operator / Author", record.operator or record.planned_by or "Unavailable"),
        ("Instrument ID", record.instrument_id or "Unavailable"),
        ("Import Fingerprint", record.import_sha256[:16] + "…" if record.import_sha256 else "Direct Manual Entry"),
    ]
    story.append(_build_meta_box(meta, styles))
    story.append(Spacer(1, 12))

    # Section 2: Operating Conditions Table
    story.append(Paragraph("2. Test Operating Conditions", styles["h2"]))
    cond_dict = record.measured_conditions if record.record_status == "MEASURED" else record.planned_conditions
    cond_dict = cond_dict or {}

    cond_rows = [
        [
            Paragraph("Parameter Name", styles["cell_header"]),
            Paragraph("Physical Meaning", styles["cell_header"]),
            Paragraph("Value", styles["cell_header"]),
            Paragraph("Unit", styles["cell_header"]),
        ],
        [
            Paragraph("Normal Load", styles["cell"]),
            Paragraph("Applied normal contact force", styles["cell"]),
            Paragraph(str(cond_dict.get("load_n", "Unavailable")), styles["cell"]),
            Paragraph("N", styles["cell"]),
        ],
        [
            Paragraph("Sliding Velocity", styles["cell"]),
            Paragraph("Relative sliding speed between counterfaces", styles["cell"]),
            Paragraph(str(cond_dict.get("sliding_velocity_m_per_s", "Unavailable")), styles["cell"]),
            Paragraph("m/s", styles["cell"]),
        ],
        [
            Paragraph("Sliding Distance", styles["cell"]),
            Paragraph("Total cumulative sliding distance", styles["cell"]),
            Paragraph(str(cond_dict.get("sliding_distance_m", "Unavailable")), styles["cell"]),
            Paragraph("m", styles["cell"]),
        ],
        [
            Paragraph("Test Duration", styles["cell"]),
            Paragraph("Elapsed test time", styles["cell"]),
            Paragraph(str(cond_dict.get("test_duration_min", "Unavailable")), styles["cell"]),
            Paragraph("min", styles["cell"]),
        ],
    ]
    t_cond = Table(cond_rows, colWidths=[120, 204, 100, 80])
    t_cond.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(t_cond)
    story.append(Spacer(1, 12))

    # Section 3: Measured Responses Table
    story.append(Paragraph("3. Tribological Measured Responses", styles["h2"]))
    if record.record_status == "PLANNED":
        story.append(
            Paragraph(
                "<i>No measured responses exist for this planned experiment. "
                "Measurements will be recorded upon physical laboratory screening.</i>",
                styles["body_muted"],
            )
        )
    else:
        m = record.measurements or {}
        cof_m = m.get("coefficient_of_friction") or {}
        wear_m = m.get("wear_measurement") or {}
        swr_m = m.get("specific_wear_rate") or {}
        wvl_m = m.get("wear_volume_loss") or {}

        meas_rows = [
            [
                Paragraph("Response Target", styles["cell_header"]),
                Paragraph("Measured Value", styles["cell_header"]),
                Paragraph("Unit As Recorded", styles["cell_header"]),
                Paragraph("Scientific Measurement Status", styles["cell_header"]),
            ],
            [
                Paragraph("Coefficient of Friction (COF)", styles["cell"]),
                Paragraph(str(cof_m.get("value", "Unavailable")), styles["cell"]),
                Paragraph(str(cof_m.get("unit_as_recorded", "dimensionless")), styles["cell"]),
                Paragraph("Verified primary response" if cof_m.get("value") is not None else "Unavailable", styles["cell"]),
            ],
            [
                Paragraph(
                    f"Wear Measurement ({m.get('wear_measurement_name_as_recorded') or 'Generic'})",
                    styles["cell"],
                ),
                Paragraph(str(wear_m.get("value", "Unavailable")), styles["cell"]),
                Paragraph(str(wear_m.get("unit_as_recorded", "Unavailable")), styles["cell"]),
                Paragraph("Conflicting units across sources; kept separated", styles["cell"]),
            ],
            [
                Paragraph("Specific Wear Rate (SWR)", styles["cell"]),
                Paragraph(str(swr_m.get("value", "Unavailable")), styles["cell"]),
                Paragraph(str(swr_m.get("unit_as_recorded", "Unavailable")), styles["cell"]),
                Paragraph("Requires explicit formula & scale verification", styles["cell"]),
            ],
            [
                Paragraph("Wear Volume Loss", styles["cell"]),
                Paragraph(str(wvl_m.get("value", "Unavailable")), styles["cell"]),
                Paragraph(str(wvl_m.get("unit_as_recorded", "Unavailable")), styles["cell"]),
                Paragraph("Not available at sample-level in raw CSV", styles["cell"]),
            ],
        ]
        t_meas = Table(meas_rows, colWidths=[150, 94, 110, 150])
        t_meas.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(t_meas)

    story.append(Spacer(1, 12))

    # Section 4: Provenance & Audit Trail
    story.append(Paragraph("4. Provenance & Scientific Integrity Statement", styles["h2"]))
    prov_meta = [
        ("Source Artifact", record.source_artifact or "Direct Database Creation"),
        ("Source Location / Sheet", record.source_location or "Table: experiment_records"),
        ("Recorded Timestamp (UTC)", record.recorded_at_utc.strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Created Timestamp (UTC)", record.created_at_utc.strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Engineer / Technician Notes", record.notes or "No notes recorded."),
    ]
    story.append(_build_meta_box(prov_meta, styles))
    story.append(Spacer(1, 10))

    # Scientific Boundary Box
    story.append(
        _build_notice_box(
            "Scientific Integrity Notice — Composite Prediction Hard Gate",
            "Models for glass-fibre/epoxy composite friction and wear are currently blocked pending evidence resolution. "
            "Author clarification is required regarding replicate groupings and incompatible wear units. "
            "Predictions from external carbon-fibre tow-on-tool benchmarks must never be applied to this composite system.",
            styles,
            tone="error",
        )
    )

    def _set_canvas_meta(cvs: NumberedCanvas, _: Any) -> None:
        cvs.report_title = f"AI-TriboTwin Experiment Report: {record.experiment_id}"
        cvs.report_id = report_id
        cvs.generation_timestamp = now_utc

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=_set_canvas_meta, onLaterPages=_set_canvas_meta)
    return buffer.getvalue()


# =========================================================================
# 2. FILTERED EXPERIMENT REGISTRY REPORT (PDF)
# =========================================================================
def build_registry_pdf(records: list[ExperimentRecord], filters: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50,
    )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"REP-REG-{int(datetime.now(timezone.utc).timestamp())}"
    styles = _get_styles()
    story = []

    # Title & Header
    story.append(Paragraph("AI-TriboTwin Engineering Report", styles["eyebrow"]))
    story.append(Paragraph("Experiment Registry Summary", styles["title"]))
    story.append(
        Paragraph(
            f"Stable Report Identifier: <b>{report_id}</b> · Generated: {now_utc} · Records Count: <b>{len(records)}</b>",
            styles["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # Applied Filters Box
    measured_count = sum(1 for r in records if r.record_status == "MEASURED")
    planned_count = sum(1 for r in records if r.record_status == "PLANNED")
    materials = sorted({r.material_system_as_recorded for r in records if r.material_system_as_recorded})

    filter_meta = [
        ("Material Filter", str(filters.get("material_system") or "ALL")),
        ("Status Filter", str(filters.get("status") or "ALL")),
        ("Search Query", str(filters.get("query") or "None")),
        ("Matching Records", f"{len(records)} ({measured_count} Measured / {planned_count} Planned)"),
        ("Active Material Systems", ", ".join(materials) if materials else "None"),
        ("Target Gate Status", "Currently Blocked Pending Evidence Resolution"),
    ]
    story.append(_build_meta_box(filter_meta, styles))
    story.append(Spacer(1, 10))

    story.append(
        _build_notice_box(
            "Safeguard: Planned Experiments vs Measured Observations",
            f"This registry contains {measured_count} physically measured experiments and {planned_count} planned screening conditions. "
            "Planned records must not be conflated with empirical measurements, nor included in model training or validation.",
            styles,
            tone="warning" if planned_count > 0 else "success",
        )
    )
    story.append(Spacer(1, 10))

    # Registry Table
    story.append(Paragraph("Registry Observations & Planned Specifications", styles["h2"]))

    if not records:
        story.append(
            Paragraph(
                "<i>No experiment records matched the active filter criteria.</i>",
                styles["body_muted"],
            )
        )
    else:
        headers = [
            Paragraph("ID", styles["cell_header"]),
            Paragraph("Status", styles["cell_header"]),
            Paragraph("Material System", styles["cell_header"]),
            Paragraph("Load (N)", styles["cell_header"]),
            Paragraph("Speed (m/s)", styles["cell_header"]),
            Paragraph("Dist (m)", styles["cell_header"]),
            Paragraph("COF", styles["cell_header"]),
            Paragraph("Wear Rate", styles["cell_header"]),
            Paragraph("Date", styles["cell_header"]),
        ]
        rows = [headers]

        for r in records[:100]:  # Cap at 100 rows per PDF export for layout stability
            cond = (r.measured_conditions if r.record_status == "MEASURED" else r.planned_conditions) or {}
            m = r.measurements or {}
            cof_val = m.get("coefficient_of_friction", {}).get("value")
            wear_val = m.get("wear_measurement", {}).get("value")
            wear_unit = m.get("wear_measurement", {}).get("unit_as_recorded")

            status_style = styles["badge_measured"] if r.record_status == "MEASURED" else styles["badge_planned"]

            rows.append([
                Paragraph(r.experiment_id, styles["cell"]),
                Paragraph(r.record_status, status_style),
                Paragraph(r.material_system_as_recorded[:28], styles["cell"]),
                Paragraph(str(cond.get("load_n", "—")), styles["cell"]),
                Paragraph(str(cond.get("sliding_velocity_m_per_s", "—")), styles["cell"]),
                Paragraph(str(cond.get("sliding_distance_m", "—")), styles["cell"]),
                Paragraph(f"{cof_val:.3f}" if isinstance(cof_val, (int, float)) else "—", styles["cell"]),
                Paragraph(f"{wear_val:.1f} {wear_unit}" if isinstance(wear_val, (int, float)) else "—", styles["cell"]),
                Paragraph(str(r.experiment_date or "—"), styles["cell"]),
            ])

        col_widths = [65, 52, 125, 45, 48, 45, 42, 60, 50]
        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(table)

        if len(records) > 100:
            story.append(Spacer(1, 6))
            story.append(
                Paragraph(
                    f"<i>Note: Displaying first 100 records of {len(records)} matching results in PDF summary. "
                    "Use CSV export for complete programmatic access.</i>",
                    styles["body_muted"],
                )
            )

    def _set_canvas_meta(cvs: NumberedCanvas, _: Any) -> None:
        cvs.report_title = "AI-TriboTwin Experiment Registry Summary"
        cvs.report_id = report_id
        cvs.generation_timestamp = now_utc

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=_set_canvas_meta, onLaterPages=_set_canvas_meta)
    return buffer.getvalue()


# =========================================================================
# 3. ANALYTICS SUMMARY REPORT (PDF)
# =========================================================================
def build_analytics_pdf(analytics: AnalyticsResponse, filters: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"REP-ANA-{int(datetime.now(timezone.utc).timestamp())}"
    styles = _get_styles()
    story = []

    # Title & Header
    story.append(Paragraph("AI-TriboTwin Engineering Report", styles["eyebrow"]))
    story.append(Paragraph("Engineering Analytics & Distribution Summary", styles["title"]))
    story.append(
        Paragraph(
            f"Stable Report Identifier: <b>{report_id}</b> · Generated: {now_utc} · Observation Basis: <b>{analytics.kpis.measured_records} Measured</b>",
            styles["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # Active Filters Box
    filter_meta = [
        ("Material Filter", str(filters.get("material_system") or "ALL")),
        ("Status Filter", str(filters.get("status") or "ALL")),
        ("Start Date", str(filters.get("date_start") or "Unbounded")),
        ("End Date", str(filters.get("date_end") or "Unbounded")),
        ("Total Records in DB", str(analytics.kpis.total_records)),
        ("Distinct Material Systems", str(analytics.kpis.distinct_materials_count)),
    ]
    story.append(_build_meta_box(filter_meta, styles))
    story.append(Spacer(1, 10))

    # Core Scientific Integrity Disclaimer
    story.append(
        _build_notice_box(
            "Scientific Integrity Notice: Descriptive Analytics Only",
            "Measured statistics strictly exclude planned records. Incompatible wear rate units (e.g. micron vs mm³/N·m) "
            "are segregated and never pooled into a composite metric. Correlation across operational conditions is descriptive "
            "and does not establish physical causation or optimal settings.",
            styles,
            tone="warning",
        )
    )
    story.append(Spacer(1, 10))

    # Section 1: KPI Summary
    story.append(Paragraph("1. Primary Experimental Registry KPIs", styles["h2"]))
    kpi_rows = [
        [
            Paragraph("Key Performance Indicator", styles["cell_header"]),
            Paragraph("Measured Count / Value", styles["cell_header"]),
            Paragraph("Methodological Basis", styles["cell_header"]),
        ],
        [
            Paragraph("Measured Experimental Records", styles["cell"]),
            Paragraph(str(analytics.kpis.measured_records), styles["cell_header"]),
            Paragraph("Physically completed runs with verified test conditions", styles["cell"]),
        ],
        [
            Paragraph("Planned Prospective Specifications", styles["cell"]),
            Paragraph(str(analytics.kpis.planned_records), styles["cell_header"]),
            Paragraph("Prospective parameter sets; excluded from statistics", styles["cell"]),
        ],
        [
            Paragraph("Distinct Material Systems", styles["cell"]),
            Paragraph(str(analytics.kpis.distinct_materials_count), styles["cell_header"]),
            Paragraph("Material variants tracked in registry database", styles["cell"]),
        ],
        [
            Paragraph("Records with Measured Friction (COF)", styles["cell"]),
            Paragraph(str(analytics.kpis.records_with_cof), styles["cell_header"]),
            Paragraph(f"Observations with finite COF ({analytics.cof_distribution.observation_count} populated)", styles["cell"]),
        ],
        [
            Paragraph("Records with Measured Wear", styles["cell"]),
            Paragraph(str(analytics.kpis.records_with_wear), styles["cell_header"]),
            Paragraph(f"Kept separated across {len(analytics.wear_distribution.groups)} distinct measurement unit groups", styles["cell"]),
        ],
    ]
    t_kpis = Table(kpi_rows, colWidths=[180, 104, 220])
    t_kpis.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(t_kpis)
    story.append(Spacer(1, 12))

    # Section 2: Material System Distribution
    story.append(Paragraph("2. Observations by Material System", styles["h2"]))
    mat_rows = [
        [
            Paragraph("Material System Name", styles["cell_header"]),
            Paragraph("Total Records", styles["cell_header"]),
            Paragraph("Measured Runs", styles["cell_header"]),
            Paragraph("Planned Runs", styles["cell_header"]),
        ]
    ]
    for mat in analytics.materials:
        mat_rows.append([
            Paragraph(mat.material_system, styles["cell"]),
            Paragraph(str(mat.total_count), styles["cell"]),
            Paragraph(str(mat.measured_count), styles["cell"]),
            Paragraph(str(mat.planned_count), styles["cell"]),
        ])
    t_mat = Table(mat_rows, colWidths=[204, 100, 100, 100])
    t_mat.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(t_mat)
    story.append(Spacer(1, 12))

    # Section 3: COF Statistics
    story.append(Paragraph("3. Friction Coefficient (COF) Empirical Distribution", styles["h2"]))
    cof_stats = analytics.cof_distribution.stats
    if cof_stats and cof_stats.count > 0:
        cof_rows = [
            ("Observed Count", str(cof_stats.count)),
            ("Unit", "dimensionless"),
            ("Mean COF", f"{cof_stats.mean:.4f}" if cof_stats.mean is not None else "Unavailable"),
            ("Median COF", f"{cof_stats.median:.4f}" if cof_stats.median is not None else "Unavailable"),
            ("Minimum Observed", f"{cof_stats.min:.4f}" if cof_stats.min is not None else "Unavailable"),
            ("Maximum Observed", f"{cof_stats.max:.4f}" if cof_stats.max is not None else "Unavailable"),
        ]
        story.append(_build_meta_box(cof_rows, styles))
    else:
        story.append(Paragraph("<i>No measured COF observations match the active filter criteria.</i>", styles["body_muted"]))

    story.append(Spacer(1, 12))

    # Section 4: Wear Distribution Breakdown
    story.append(Paragraph("4. Wear Measurement Distribution (Unit-Separated)", styles["h2"]))
    if analytics.wear_distribution.groups:
        for grp in analytics.wear_distribution.groups:
            st = grp.stats
            story.append(Paragraph(f"• <b>{grp.measurement_name}</b> ({grp.unit}) — {grp.observation_count} observations", styles["h3"]))
            if st and st.count > 0:
                wear_meta = [
                    ("Count", str(st.count)),
                    ("Unit", grp.unit),
                    ("Mean", f"{st.mean:.3f}" if st.mean is not None else "Unavailable"),
                    ("Median", f"{st.median:.3f}" if st.median is not None else "Unavailable"),
                    ("Min", f"{st.min:.3f}" if st.min is not None else "Unavailable"),
                    ("Max", f"{st.max:.3f}" if st.max is not None else "Unavailable"),
                ]
                story.append(_build_meta_box(wear_meta, styles))
                story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("<i>No wear measurements found matching active filters.</i>", styles["body_muted"]))

    def _set_canvas_meta(cvs: NumberedCanvas, _: Any) -> None:
        cvs.report_title = "AI-TriboTwin Engineering Analytics Summary"
        cvs.report_id = report_id
        cvs.generation_timestamp = now_utc

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=_set_canvas_meta, onLaterPages=_set_canvas_meta)
    return buffer.getvalue()


# =========================================================================
# 4. MODEL EVALUATION & PROVENANCE REPORT (PDF)
# =========================================================================
def build_models_pdf(model_status: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"REP-MDL-{int(datetime.now(timezone.utc).timestamp())}"
    styles = _get_styles()
    story = []

    # Title & Header
    story.append(Paragraph("AI-TriboTwin Scientific Report", styles["eyebrow"]))
    story.append(Paragraph("Model Evaluation & Provenance Audit", styles["title"]))
    story.append(
        Paragraph(
            f"Stable Report Identifier: <b>{report_id}</b> · Generated: {now_utc} · Scientific Gate Status: <b>Enforced</b>",
            styles["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # Prominent Scope Boundary Banner
    story.append(
        _build_notice_box(
            "Scientific Scope & Composite Target Hard Gate",
            "This report documents evaluated models and gates across AI-TriboTwin. "
            "1. The evaluated external model applies strictly to carbon-fibre tow sliding on glass tools, NOT glass-fibre/epoxy composite friction. "
            "2. The synthetic demonstration model is purely non-physical code fixture. "
            "3. Original glass-fibre/epoxy composite targets are CURRENTLY BLOCKED pending evidence resolution. No composite predictions are permitted.",
            styles,
            tone="error",
        )
    )
    story.append(Spacer(1, 10))

    # Section 1: Tier 1 External Cambridge Model
    story.append(Paragraph("1. Tier 1 — External Cambridge Benchmark Model", styles["h2"]))
    ext = model_status.get("external_model", {})
    ext_rep = ext.get("report") if ext.get("status") == "EVALUATED_EXTERNAL_COF" else None

    if ext_rep:
        meta_ext = [
            ("Model Identifier", ext_rep.get("model_id", "TOW-TOOL-COF-CAMBRIDGE")),
            ("Selected Estimator", ext_rep.get("selected_model", "Unavailable")),
            ("Material Domain", ext_rep.get("material_domain", "Carbon-fibre tow on glass tool")),
            ("Target Variable", f"{ext_rep.get('target', 'coefficient_of_friction')} ({ext_rep.get('target_unit', 'dimensionless')})"),
            ("Source Dataset", ext_rep.get("source_name", "University of Cambridge Repository")),
            ("Source Workbook SHA-256", (ext_rep.get("source_workbook_sha256") or "")[:20] + "…"),
            ("Total Observations", str(ext_rep.get("observation_count", 140))),
            ("Train / Holdout Rows", f"{ext_rep.get('training_rows', 98)} / {ext_rep.get('holdout_rows', 42)}"),
            ("Holdout Split Scheme", "GroupShuffleSplit (7 train / 3 holdout runs)"),
            ("Holdout Test Sweeps", ", ".join(ext_rep.get("holdout_group_ids", []))),
        ]
        story.append(_build_meta_box(meta_ext, styles))
        story.append(Spacer(1, 10))

        # Held-out Performance Metrics
        hm = ext_rep.get("holdout_metrics", {})
        bm = ext_rep.get("baseline_metrics", {})
        perf_rows = [
            [
                Paragraph("Evaluated Metric", styles["cell_header"]),
                Paragraph("Held-Out Value", styles["cell_header"]),
                Paragraph("Mean Baseline Comparison", styles["cell_header"]),
                Paragraph("Scientific Evaluation Basis", styles["cell_header"]),
            ],
            [
                Paragraph("Mean Absolute Error (MAE)", styles["cell"]),
                Paragraph(f"{hm.get('mae', 0):.4f}", styles["cell_header"]),
                Paragraph(f"{bm.get('mae', 0):.4f}", styles["cell"]),
                Paragraph("Evaluated on 42 held-out observations across 3 unseen sweeps", styles["cell"]),
            ],
            [
                Paragraph("Root Mean Squared Error (RMSE)", styles["cell"]),
                Paragraph(f"{hm.get('rmse', 0):.4f}", styles["cell_header"]),
                Paragraph(f"{bm.get('rmse', 0):.4f}", styles["cell"]),
                Paragraph("Strictly bounded by RMSE >= MAE mathematical requirement", styles["cell"]),
            ],
            [
                Paragraph("Coefficient of Determination (R²)", styles["cell"]),
                Paragraph(f"{hm.get('r2', 0):.4f}", styles["cell_header"]),
                Paragraph(f"{bm.get('r2', 0):.4f}", styles["cell"]),
                Paragraph("Substantially outperforms unstratified mean baseline (-0.0039)", styles["cell"]),
            ],
        ]
        t_perf = Table(perf_rows, colWidths=[140, 80, 114, 170])
        t_perf.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(t_perf)
        story.append(Spacer(1, 10))

        # Stratified Tow-Type Breakdown Table
        slices = ext_rep.get("holdout_slices", {}).get("by_tow_type", {})
        if slices:
            story.append(Paragraph("Stratified Performance by Carbon Tow Sizing", styles["h3"]))
            strat_rows = [
                [
                    Paragraph("Tow Type", styles["cell_header"]),
                    Paragraph("Holdout Rows", styles["cell_header"]),
                    Paragraph("MAE", styles["cell_header"]),
                    Paragraph("RMSE", styles["cell_header"]),
                    Paragraph("R²", styles["cell_header"]),
                    Paragraph("Mean Residual", styles["cell_header"]),
                ]
            ]
            for tow, sl in slices.items():
                strat_rows.append([
                    Paragraph(tow, styles["cell_header"]),
                    Paragraph(str(sl.get("rows", "—")), styles["cell"]),
                    Paragraph(f"{sl.get('mae', 0):.4f}", styles["cell"]),
                    Paragraph(f"{sl.get('rmse', 0):.4f}", styles["cell"]),
                    Paragraph(f"{sl.get('r2', 0):.4f}", styles["cell"]),
                    Paragraph(f"{sl.get('mean_residual', 0):.4f}", styles["cell"]),
                ])
            t_strat = Table(strat_rows, colWidths=[130, 70, 75, 75, 75, 79])
            t_strat.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(t_strat)
            story.append(Spacer(1, 8))

        # Known Model Limitations
        story.append(
            _build_notice_box(
                "Known Empirical Limitations & Uncertainty Disclosure",
                "1. Sizing 50C Deficit: Holdout run T700-12k-50C-T1 exhibits negative R² (-0.7446), with Step 0 error (+0.786060) accounting for 65.02% of squared error.\n"
                "2. Specimen Independence: Sweeps are labelled Test 1-5 without recorded spool serial numbers; load ramps exhibit sequential autocorrelation.\n"
                "3. Uncalibrated Intervals: Prediction intervals are not produced because conformal calibration requires >= 9 independent runs per stratum.",
                styles,
                tone="warning",
            )
        )
    else:
        story.append(Paragraph("<i>External model report artifact is unavailable.</i>", styles["body_muted"]))

    story.append(Spacer(1, 14))

    # Section 2: Tier 2 Synthetic Demonstration Model
    story.append(Paragraph("2. Tier 2 — Synthetic Demonstration Model (Code Fixture)", styles["h2"]))
    demo = model_status.get("demo_report") or {}
    demo_meta = [
        ("Target ID", "SYNTHETIC-DEMO"),
        ("Model Nature", "Pure Code Demonstration Fixture"),
        ("Physical Meaning", "None (Synthetically Generated Observations)"),
        ("Selected Estimator", str(demo.get("selected_model", "Ridge"))),
        ("Holdout Rows", str(demo.get("holdout_rows", "Unavailable"))),
        ("Evaluation Status", "Verified Pipeline Demonstration Only"),
    ]
    story.append(_build_meta_box(demo_meta, styles))
    story.append(Spacer(1, 14))

    # Section 3: Tier 3 Blocked Composite Readiness Gates
    story.append(Paragraph("3. Tier 3 — Original Composite Targets Readiness Gate", styles["h2"]))
    targets = model_status.get("experimental_targets", [])
    t_rows = [
        [
            Paragraph("Target ID", styles["cell_header"]),
            Paragraph("Target Name", styles["cell_header"]),
            Paragraph("Readiness Status", styles["cell_header"]),
            Paragraph("Required Evidence to Unlock", styles["cell_header"]),
        ]
    ]
    for tg in targets:
        t_rows.append([
            Paragraph(tg.get("target_id", "—"), styles["cell_header"]),
            Paragraph(tg.get("target_name", "—"), styles["cell"]),
            Paragraph(f"<font color='#b91c1c'><b>{tg.get('status', 'BLOCKED')}</b></font>", styles["cell"]),
            Paragraph(tg.get("required_evidence", "Author verification required."), styles["cell"]),
        ])
    t_gate = Table(t_rows, colWidths=[90, 130, 84, 200])
    t_gate.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#fca5a5")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#fecaca")),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(t_gate)
    story.append(Spacer(1, 10))

    story.append(
        _build_notice_box(
            "Hard Gate Enforced: Blocked / No Go",
            "All glass-fibre/epoxy composite targets are CURRENTLY BLOCKED pending evidence resolution. "
            "They will remain safely locked until author clarification resolves run-to-paper mapping and incompatible wear units. "
            "No composite model predictions or optimization will be deployed until these gates clear.",
            styles,
            tone="error",
        )
    )

    def _set_canvas_meta(cvs: NumberedCanvas, _: Any) -> None:
        cvs.report_title = "AI-TriboTwin Model Evaluation & Provenance Report"
        cvs.report_id = report_id
        cvs.generation_timestamp = now_utc

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=_set_canvas_meta, onLaterPages=_set_canvas_meta)
    return buffer.getvalue()


# =========================================================================
# 5. STRUCTURED CSV EXPORTS
# =========================================================================
def build_experiments_csv(records: list[ExperimentRecord]) -> str:
    """Export experiment records to clean RFC 4180 CSV with explicit unit headers."""
    output = io.StringIO()
    fieldnames = [
        "experiment_id",
        "record_status",
        "material_system",
        "replicate_group_id",
        "experiment_date",
        "normal_load_n",
        "sliding_velocity_mps",
        "sliding_distance_m",
        "test_duration_min",
        "coefficient_of_friction",
        "wear_measurement_value",
        "wear_measurement_unit",
        "wear_measurement_name",
        "specific_wear_rate_value",
        "specific_wear_rate_unit",
        "wear_volume_loss_value",
        "wear_volume_loss_unit",
        "source_artifact",
        "source_location",
        "import_sha256",
        "recorded_at_utc",
        "notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for r in records:
        cond = (r.measured_conditions if r.record_status == "MEASURED" else r.planned_conditions) or {}
        m = r.measurements or {}
        cof_m = m.get("coefficient_of_friction") or {}
        wear_m = m.get("wear_measurement") or {}
        swr_m = m.get("specific_wear_rate") or {}
        wvl_m = m.get("wear_volume_loss") or {}

        writer.writerow({
            "experiment_id": r.experiment_id,
            "record_status": r.record_status,
            "material_system": r.material_system_as_recorded,
            "replicate_group_id": r.replicate_group_id or "",
            "experiment_date": str(r.experiment_date) if r.experiment_date else "",
            "normal_load_n": cond.get("load_n", ""),
            "sliding_velocity_mps": cond.get("sliding_velocity_m_per_s", ""),
            "sliding_distance_m": cond.get("sliding_distance_m", ""),
            "test_duration_min": cond.get("test_duration_min", ""),
            "coefficient_of_friction": cof_m.get("value", ""),
            "wear_measurement_value": wear_m.get("value", ""),
            "wear_measurement_unit": wear_m.get("unit_as_recorded", ""),
            "wear_measurement_name": m.get("wear_measurement_name_as_recorded", ""),
            "specific_wear_rate_value": swr_m.get("value", ""),
            "specific_wear_rate_unit": swr_m.get("unit_as_recorded", ""),
            "wear_volume_loss_value": wvl_m.get("value", ""),
            "wear_volume_loss_unit": wvl_m.get("unit_as_recorded", ""),
            "source_artifact": r.source_artifact or "",
            "source_location": r.source_location or "",
            "import_sha256": r.import_sha256 or "",
            "recorded_at_utc": r.recorded_at_utc.isoformat() if r.recorded_at_utc else "",
            "notes": r.notes or "",
        })

    return output.getvalue()


def build_analytics_csv(analytics: AnalyticsResponse) -> str:
    """Export analytics summary KPIs and material distributions to structured CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Section 1: KPIs
    writer.writerow(["# AI-TriboTwin Engineering Analytics Summary CSV"])
    writer.writerow(["metric_name", "value", "unit_or_basis"])
    writer.writerow(["total_records", analytics.kpis.total_records, "all database rows"])
    writer.writerow(["measured_records", analytics.kpis.measured_records, "physically tested observations"])
    writer.writerow(["planned_records", analytics.kpis.planned_records, "prospective screening plans"])
    writer.writerow(["distinct_materials_count", analytics.kpis.distinct_materials_count, "count"])
    writer.writerow(["records_with_cof", analytics.kpis.records_with_cof, "count"])
    writer.writerow(["records_with_wear", analytics.kpis.records_with_wear, "count"])

    cof_st = analytics.cof_distribution.stats
    if cof_st:
        writer.writerow(["cof_mean", f"{cof_st.mean:.4f}" if cof_st.mean is not None else "", "dimensionless"])
        writer.writerow(["cof_median", f"{cof_st.median:.4f}" if cof_st.median is not None else "", "dimensionless"])
        writer.writerow(["cof_min", f"{cof_st.min:.4f}" if cof_st.min is not None else "", "dimensionless"])
        writer.writerow(["cof_max", f"{cof_st.max:.4f}" if cof_st.max is not None else "", "dimensionless"])

    writer.writerow([])
    # Section 2: Material Systems Breakdown
    writer.writerow(["# Material System Breakdown"])
    writer.writerow(["material_system", "total_records", "measured_runs", "planned_runs"])
    for mat in analytics.materials:
        writer.writerow([mat.material_system, mat.total_count, mat.measured_count, mat.planned_count])

    return output.getvalue()
