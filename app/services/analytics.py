from datetime import date, datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session
from app import models
from app.services.expiry_service import enrich_product


def get_dashboard_metrics(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Computes real-time overview metrics matching user portfolio specifications:
    - Total Products
    - Expiring Soon (1-7 days)
    - Expired (< 0 days)
    - Low Stock (quantity <= min_quantity)
    - Monthly Spending (current calendar month sum from ExpenseLog and purchase logs)
    - Wastage Cost (monetary value of expired items)
    - Total Inventory Value (quantity * unit_price of all fresh/available items)
    """
    products = db.query(models.Product).filter(models.Product.user_id == user_id).all()
    today = date.today()

    enriched = [enrich_product(p, today) for p in products]
    
    total_products = len(enriched)
    expired_items = [p for p in enriched if p["expiry_status"] == "expired"]
    expiring_soon_items = [p for p in enriched if p["expiry_status"] in ("critical", "warning")]
    low_stock_items = [p for p in enriched if p["stock_status"] in ("low_stock", "out_of_stock")]

    # Calculate monetary values using Pandas
    if enriched:
        df_prod = pd.DataFrame(enriched)
        total_inventory_value = round(float(df_prod["total_value"].sum()), 2)
        expired_df = df_prod[df_prod["expiry_status"] == "expired"]
        wastage_cost = round(float(expired_df["total_value"].sum()), 2) if not expired_df.empty else 0.0
    else:
        total_inventory_value = 0.0
        wastage_cost = 0.0

    # Monthly spending from ExpenseLog
    first_day_of_month = date(today.year, today.month, 1)
    expenses = (
        db.query(models.ExpenseLog)
        .filter(
            models.ExpenseLog.user_id == user_id,
            models.ExpenseLog.expense_date >= first_day_of_month
        )
        .all()
    )

    if expenses:
        expense_records = [{"amount": e.amount} for e in expenses]
        df_exp = pd.DataFrame(expense_records)
        monthly_spending = round(float(df_exp["amount"].sum()), 2)
    else:
        # Fallback to sum of product purchase costs this month if expenses haven't been separately logged
        recent_purchases = [
            p for p in enriched 
            if p["purchase_date"] >= first_day_of_month
        ]
        monthly_spending = round(sum(p["total_value"] for p in recent_purchases), 2)

    return {
        "total_products": total_products,
        "expiring_soon": len(expiring_soon_items),
        "expired": len(expired_items),
        "low_stock": len(low_stock_items),
        "monthly_spending": monthly_spending,
        "total_inventory_value": total_inventory_value,
        "wastage_cost": wastage_cost,
    }


def get_expense_analysis(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Generates Pandas analytical summaries:
    - Daily spending trend (last 30 days)
    - Monthly spending history (last 6 months)
    - Category-wise spending breakdown
    - Payment method distribution
    - Top purchased items
    """
    expenses = (
        db.query(models.ExpenseLog, models.Category.name.label("cat_name"))
        .outerjoin(models.Category, models.ExpenseLog.category_id == models.Category.id)
        .filter(models.ExpenseLog.user_id == user_id)
        .all()
    )

    if not expenses:
        return {
            "daily_trend": {"labels": [], "values": []},
            "monthly_trend": {"labels": [], "values": []},
            "category_distribution": {"labels": [], "values": []},
            "payment_methods": {"labels": [], "values": []},
            "top_expenses": [],
            "total_expenses_all_time": 0.0
        }

    raw_data = []
    for exp, cat_name in expenses:
        raw_data.append({
            "id": exp.id,
            "product_name": exp.product_name,
            "category": cat_name or "General",
            "amount": float(exp.amount),
            "expense_date": pd.to_datetime(exp.expense_date),
            "payment_method": exp.payment_method or "UPI"
        })

    df = pd.DataFrame(raw_data)
    total_expenses_all_time = round(float(df["amount"].sum()), 2)

    # 1. Category Distribution
    cat_summary = df.groupby("category")["amount"].sum().reset_index()
    cat_summary = cat_summary.sort_values(by="amount", ascending=False)
    cat_labels = cat_summary["category"].tolist()
    cat_values = [round(v, 2) for v in cat_summary["amount"].tolist()]

    # 2. Daily Trend (last 30 days)
    today = pd.Timestamp.now().normalize()
    start_30d = today - pd.Timedelta(days=29)
    df_30d = df[df["expense_date"] >= start_30d].copy()
    
    # Create complete date range to ensure zero spending days are properly reflected
    date_range = pd.date_range(start=start_30d, end=today, freq="D")
    daily_grouped = df_30d.groupby(df_30d["expense_date"].dt.date)["amount"].sum()
    daily_series = daily_grouped.reindex(date_range.date, fill_value=0.0)

    daily_labels = [d.strftime("%d %b") for d in daily_series.index]
    daily_values = [round(float(v), 2) for v in daily_series.values]

    # 3. Monthly Trend (last 6 months)
    df["year_month"] = df["expense_date"].dt.to_period("M")
    monthly_grouped = df.groupby("year_month")["amount"].sum().sort_index()
    monthly_labels = [str(period) for period in monthly_grouped.index[-6:]]
    monthly_values = [round(float(v), 2) for v in monthly_grouped.values[-6:]]

    # 4. Payment Method breakdown
    pm_summary = df.groupby("payment_method")["amount"].sum().reset_index()
    pm_labels = pm_summary["payment_method"].tolist()
    pm_values = [round(v, 2) for v in pm_summary["amount"].tolist()]

    # 5. Top 5 highest expenses
    top_items = (
        df.groupby("product_name")["amount"]
        .sum()
        .reset_index()
        .sort_values(by="amount", ascending=False)
        .head(5)
        .to_dict(orient="records")
    )
    for item in top_items:
        item["amount"] = round(item["amount"], 2)

    return {
        "daily_trend": {"labels": daily_labels, "values": daily_values},
        "monthly_trend": {"labels": monthly_labels, "values": monthly_values},
        "category_distribution": {"labels": cat_labels, "values": cat_values},
        "payment_methods": {"labels": pm_labels, "values": pm_values},
        "top_expenses": top_items,
        "total_expenses_all_time": total_expenses_all_time
    }
