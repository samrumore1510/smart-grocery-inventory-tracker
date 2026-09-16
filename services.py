import io
from datetime import date, datetime, timedelta
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from database import products_col, expenses_col, categories_col, serialize_doc


# -----------------------------------------------------------------------------
# 1. Expiry & Stock Classifiers
# -----------------------------------------------------------------------------
def parse_date(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()


def classify_expiry(expiry_date, ref_date=None):
    if ref_date is None:
        ref_date = date.today()
    exp = parse_date(expiry_date)
    days = (exp - ref_date).days

    if days < 0:
        return "expired", f"Expired {abs(days)}d ago ❌", days
    elif days == 0:
        return "critical", "Expires Today 🔴", days
    elif 1 <= days <= 3:
        return "critical", f"Expires in {days} day{'s' if days > 1 else ''} 🔴", days
    elif 4 <= days <= 7:
        return "warning", f"Expires in {days} days 🟠", days
    else:
        return "fresh", f"Fresh ({days}d left) ✅", days


def classify_stock(quantity, min_quantity):
    q = float(quantity)
    min_q = float(min_quantity)
    if q <= 0:
        return "out_of_stock", "Out of Stock ❌"
    elif q <= min_q:
        return "low_stock", "Low Stock ⚠️"
    else:
        return "available", "Available ✅"


def enrich_product(doc, ref_date=None):
    p = serialize_doc(doc)
    status, badge, days = classify_expiry(p["expiry_date"], ref_date)
    stock_status, stock_badge = classify_stock(p["quantity"], p.get("min_quantity", 1.0))
    total_val = round(float(p["quantity"]) * float(p.get("unit_price", 0.0)), 2)

    p["days_until_expiry"] = days
    p["expiry_status"] = status
    p["expiry_badge_text"] = badge
    p["stock_status"] = stock_status
    p["stock_badge_text"] = stock_badge
    p["total_value"] = total_val
    return p


# -----------------------------------------------------------------------------
# 2. Pandas Analytics Engine
# -----------------------------------------------------------------------------
def get_dashboard_metrics(user_id):
    docs = list(products_col.find({"user_id": str(user_id)}))
    today = date.today()
    enriched = [enrich_product(d, today) for d in docs]

    total_products = len(enriched)
    expired = [p for p in enriched if p["expiry_status"] == "expired"]
    expiring_soon = [p for p in enriched if p["expiry_status"] in ("critical", "warning")]
    low_stock = [p for p in enriched if p["stock_status"] in ("low_stock", "out_of_stock")]

    # Calculate monetary metrics using Pandas
    if enriched:
        df_p = pd.DataFrame(enriched)
        total_value = round(float(df_p["total_value"].sum()), 2)
        expired_df = df_p[df_p["expiry_status"] == "expired"]
        wastage_cost = round(float(expired_df["total_value"].sum()), 2) if not expired_df.empty else 0.0
    else:
        total_value = 0.0
        wastage_cost = 0.0

    # Monthly spending from MongoDB expense logs
    first_of_month = date(today.year, today.month, 1).strftime("%Y-%m-%d")
    expenses = list(expenses_col.find({
        "user_id": str(user_id),
        "expense_date": {"$gte": first_of_month}
    }))

    if expenses:
        df_exp = pd.DataFrame(expenses)
        monthly_spending = round(float(df_exp["amount"].sum()), 2)
    else:
        monthly_spending = 0.0

    return {
        "total_products": total_products,
        "expiring_soon": len(expiring_soon),
        "expired": len(expired),
        "low_stock": len(low_stock),
        "monthly_spending": monthly_spending,
        "total_inventory_value": total_value,
        "wastage_cost": wastage_cost,
    }


def get_expense_analysis(user_id):
    expenses = list(expenses_col.find({"user_id": str(user_id)}))
    if not expenses:
        return {
            "daily_trend": {"labels": [], "values": []},
            "monthly_trend": {"labels": [], "values": []},
            "category_distribution": {"labels": [], "values": []},
            "payment_methods": {"labels": [], "values": []},
            "top_expenses": [],
            "total_expenses_all_time": 0.0
        }

    df = pd.DataFrame(expenses)
    df["amount"] = df["amount"].astype(float)
    df["dt"] = pd.to_datetime(df["expense_date"])
    total_spent = round(float(df["amount"].sum()), 2)

    # 1. Category Distribution
    cat_grp = df.groupby("category_name")["amount"].sum().sort_values(ascending=False)
    cat_labels = cat_grp.index.tolist()
    cat_values = [round(float(v), 2) for v in cat_grp.values]

    # 2. Daily Trend (30 days continuous)
    today = pd.Timestamp.now().normalize()
    start_30d = today - pd.Timedelta(days=29)
    df_30d = df[df["dt"] >= start_30d]
    date_range = pd.date_range(start=start_30d, end=today, freq="D")
    daily_s = df_30d.groupby(df_30d["dt"].dt.date)["amount"].sum().reindex(date_range.date, fill_value=0.0)

    daily_labels = [d.strftime("%d %b") for d in daily_s.index]
    daily_values = [round(float(v), 2) for v in daily_s.values]

    # 3. Monthly Trend (6 months)
    df["month_period"] = df["dt"].dt.to_period("M")
    m_grp = df.groupby("month_period")["amount"].sum().sort_index()
    monthly_labels = [str(p) for p in m_grp.index[-6:]]
    monthly_values = [round(float(v), 2) for v in m_grp.values[-6:]]

    # 4. Payment Methods
    pm_grp = df.groupby("payment_method")["amount"].sum()
    pm_labels = pm_grp.index.tolist()
    pm_values = [round(float(v), 2) for v in pm_grp.values]

    # 5. Top 5 Expenses
    top_items = (
        df.groupby("product_name")["amount"]
        .sum()
        .reset_index()
        .sort_values(by="amount", ascending=False)
        .head(5)
        .to_dict(orient="records")
    )
    for it in top_items:
        it["amount"] = round(it["amount"], 2)

    return {
        "daily_trend": {"labels": daily_labels, "values": daily_values},
        "monthly_trend": {"labels": monthly_labels, "values": monthly_values},
        "category_distribution": {"labels": cat_labels, "values": cat_values},
        "payment_methods": {"labels": pm_labels, "values": pm_values},
        "top_expenses": top_items,
        "total_expenses_all_time": total_spent
    }


# -----------------------------------------------------------------------------
# 3. Smart Contextual Recommendations
# -----------------------------------------------------------------------------
def generate_recommendations(user_id):
    docs = list(products_col.find({"user_id": str(user_id)}))
    if not docs:
        return [{
            "type": "info",
            "title": "Welcome to Smart Grocery Tracker",
            "message": "Add your first product to activate intelligent expiry tracking and predictions!",
            "icon": "✨",
            "severity": "info"
        }]

    today = date.today()
    enriched = [enrich_product(d, today) for d in docs]
    recs = []

    # 1. Urgent Expiry
    critical = [p for p in enriched if p["expiry_status"] == "critical"]
    critical.sort(key=lambda x: x["days_until_expiry"])
    for item in critical[:3]:
        days = item["days_until_expiry"]
        msg = f"{item['name']} expires tomorrow. Consider using it first." if days == 1 else f"{item['name']} expires in {days} days. Plan meals around it."
        recs.append({
            "type": "expiry_urgent",
            "title": f"Urgent: {item['name']}",
            "message": msg,
            "icon": "⏰",
            "severity": "critical"
        })

    # 2. Recipe Pairing Ideas
    expiring_names = [p["name"].lower() for p in enriched if p["days_until_expiry"] <= 4 and p["quantity"] > 0]
    if any(n in ["tomato", "tomatoes", "spinach", "paneer", "vegetables"] for n in expiring_names):
        recs.append({
            "type": "recipe",
            "title": "Smart Recipe Idea",
            "message": "You have vegetables and dairy expiring soon! A mixed vegetable curry or paneer bhurji will use them up perfectly.",
            "icon": "🍳",
            "severity": "info"
        })

    # 3. 30-Day Predictive Replenishment
    targets = ["cooking oil", "sunflower oil", "rice", "atta", "sugar", "tea"]
    for p in enriched:
        if any(t in p["name"].lower() for t in targets):
            qty = float(p["quantity"])
            min_q = float(p.get("min_quantity", 1.0))
            if qty <= min_q * 1.5:
                est_days = max(int((qty / max(min_q, 1.0)) * 5), 1)
                recs.append({
                    "type": "prediction",
                    "title": f"Predictive Restock: {p['name']}",
                    "message": f"You usually purchase {p['name']} every 30 days. Your current stock ({qty} {p['unit']}) may last only ~{est_days} days.",
                    "icon": "📈",
                    "severity": "warning"
                })
                break

    # 4. Low Stock Alert
    lows = [p for p in enriched if p["stock_status"] in ("low_stock", "out_of_stock")]
    if lows:
        first_low = lows[0]
        desc = "is out of stock" if first_low["quantity"] <= 0 else f"is running low ({first_low['quantity']} {first_low['unit']})"
        recs.append({
            "type": "low_stock",
            "title": "Inventory Restock Needed",
            "message": f"{first_low['name']} {desc}. Automatically queued for your shopping list.",
            "icon": "🛒",
            "severity": "warning"
        })

    # 5. Financial Waste Alert
    at_risk = sum(p["total_value"] for p in enriched if 0 <= p["days_until_expiry"] <= 7)
    if at_risk > 100:
        recs.append({
            "type": "saving",
            "title": "Savings Opportunity",
            "message": f"You have Rs.{round(at_risk, 2)} worth of groceries expiring within 7 days. Using them now prevents financial loss.",
            "icon": "💡",
            "severity": "success"
        })

    return recs


# -----------------------------------------------------------------------------
# 4. PDF & Excel Exporters
# -----------------------------------------------------------------------------
def generate_inventory_pdf(products, user_full_name="User"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#0f172a"))
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#64748b"), spaceAfter=12)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8)
    head_style = ParagraphStyle("Head", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=colors.white)

    story = [
        Paragraph("Smart Grocery Inventory & Expiry Audit Report", title_style),
        Paragraph(f"Generated for: {user_full_name} &bull; Date: {datetime.now().strftime('%d %b %Y')} &bull; Database: MongoDB", sub_style),
        Spacer(1, 8)
    ]

    data = [[
        Paragraph("Item Name", head_style),
        Paragraph("Category", head_style),
        Paragraph("Stock", head_style),
        Paragraph("Expiry Date", head_style),
        Paragraph("Status", head_style),
        Paragraph("Value (Rs.)", head_style),
    ]]

    for p in products:
        data.append([
            Paragraph(p["name"], cell_style),
            Paragraph(p.get("category_name", "General"), cell_style),
            Paragraph(f"{p['quantity']} {p['unit']}", cell_style),
            Paragraph(str(p["expiry_date"]), cell_style),
            Paragraph(p["expiry_badge_text"], cell_style),
            Paragraph(f"Rs.{p['total_value']:.2f}", cell_style),
        ])

    t = Table(data, colWidths=[150, 110, 70, 80, 80, 50], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_inventory_excel(products):
    buffer = io.BytesIO()
    df = pd.DataFrame(products)
    cols = ["name", "category_name", "quantity", "unit", "min_quantity", "unit_price", "total_value", "expiry_date", "expiry_status", "stock_status"]
    available_cols = [c for c in cols if c in df.columns]
    df[available_cols].to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer
