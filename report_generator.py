
from io import BytesIO
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)


def generate_evidence_report(
    case_id,
    source,
    target_url,
    evidence_hash,
    collection_time,
    verification_status="Not verified",
    transaction_hash=None
):
    """Generate a forensic evidence summary PDF in memory."""

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=19,
        leading=24,
        textColor=colors.HexColor("#173A70"),
        alignment=TA_CENTER,
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        wordWrap="CJK"
    )

    story = []

    story.append(Paragraph("FORENSICVAULT", title_style))
    story.append(Paragraph(
        "Digital Forensic Evidence Preservation Report",
        styles["Heading2"]
    ))
    story.append(Spacer(1, 18))

    def safe(value):
        return escape(str(value)) if value is not None else "Not available"

    rows = [
        ["Field", "Details"],
        ["Case ID", safe(case_id)],
        ["Evidence Source", safe(source)],
        ["Target URL", safe(target_url)],
        ["SHA-256 Hash", safe(evidence_hash)],
        ["Collection Time", safe(collection_time)],
        ["Verification Status", safe(verification_status)],
        ["Blockchain Transaction", safe(transaction_hash)],
        [
            "Report Generated",
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        ],
    ]

    table_data = [
        [
            Paragraph(str(field), body_style),
            Paragraph(str(value), body_style)
        ]
        for field, value in rows
    ]

    table = Table(table_data, colWidths=[145, 355], repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173A70")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white, colors.HexColor("#F1F5FA")
        ]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(table)
    story.append(Spacer(1, 22))

    story.append(Paragraph("Forensic Integrity Note", styles["Heading3"]))
    story.append(Paragraph(
        "This report summarizes evidence metadata supplied by the "
        "ForensicVault application. SHA-256 verification checks whether "
        "a file matches a registered hash. A matching hash alone does "
        "not establish the authenticity of the original source, the "
        "identity of the collector, or a complete chain of custody.",
        body_style
    ))

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
