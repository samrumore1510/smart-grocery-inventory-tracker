import io
from datetime import datetime, date
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generate_inventory_pdf(products: List[Dict[str, Any]], user_full_name: str = "User") -> io.BytesIO:
    """Generates a professional PDF audit report of the grocery inventory."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.white
    )

    story = []

    # Title & Header
    story.append(Paragraph("Smart Grocery Inventory & Expiry Audit Report", title_style))
    now_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
    total_val = sum(p.get("total_value", 0) for p in products)
    story.append(Paragraph(f"Generated for: {user_full_name} &bull; Generated on: {now_str} &bull; Total Inventory Value: ₹{total_val:,.2f}", subtitle_style))
    story.append(Spacer(1, 10))

    # Table Header
    table_data = [
        [
            Paragraph("Item Name", header_cell_style),
            Paragraph("Category", header_cell_style),
            Paragraph("Stock", header_cell_style),
            Paragraph("Expiry Date", header_cell_style),
            Paragraph("Expiry Status", header_cell_style),
            Paragraph("Stock Status", header_cell_style),
            Paragraph("Value (₹)", header_cell_style),
        ]
    ]

    for p in products:
        # Determine status colors
        exp_status = p.get("expiry_status", "fresh")
        if exp_status == "expired":
            exp_text = f"<font color='#dc2626'><b>Expired</b></font>"
        elif exp_status == "critical":
            exp_text = f"<font color='#e11d48'><b>{p.get('days_until_expiry', 0)}d left</b></font>"
        elif exp_status == "warning":
            exp_text = f"<font color='#d97706'><b>{p.get('days_until_expiry', 0)}d left</b></font>"
        else:
            exp_text = f"<font color='#16a34a'>Fresh</font>"

        stock_status = p.get("stock_status", "available")
        if stock_status == "out_of_stock":
            stock_text = "<font color='#dc2626'>Out of Stock</font>"
        elif stock_status == "low_stock":
            stock_text = "<font color='#d97706'>Low Stock</font>"
        else:
            stock_text = "<font color='#16a34a'>In Stock</font>"

        exp_date_str = p['expiry_date'].strftime('%d-%b-%Y') if isinstance(p['expiry_date'], (date, datetime)) else str(p['expiry_date'])

        row = [
            Paragraph(p.get("name", "N/A"), cell_style),
            Paragraph(p.get("category_name", "General"), cell_style),
            Paragraph(f"{p.get('quantity', 0)} {p.get('unit', '')}", cell_style),
            Paragraph(exp_date_str, cell_style),
            Paragraph(exp_text, cell_style),
            Paragraph(stock_text, cell_style),
            Paragraph(f"₹{p.get('total_value', 0):,.2f}", cell_style),
        ]
        table_data.append(row)

    # Table styling
    col_widths = [130, 90, 60, 75, 75, 70, 60]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer
