import io
from datetime import date
import pandas as pd
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
from app.services.analytics import get_dashboard_metrics, get_expense_analysis
from app.services.recommender import generate_smart_recommendations
from app.services.expiry_service import enrich_product
from app.services.pdf_service import generate_inventory_pdf

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Reports"])


@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    metrics = get_dashboard_metrics(db, current_user.id)
    recommendations = generate_smart_recommendations(db, current_user.id)
    return {
        "metrics": metrics,
        "recommendations": recommendations,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name or current_user.username,
            "role": current_user.role
        }
    }


@router.get("/expenses")
def get_expense_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return get_expense_analysis(db, current_user.id)


@router.post("/expenses", status_code=201)
def log_expense(
    exp_in: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    exp = models.ExpenseLog(
        user_id=current_user.id,
        product_id=exp_in.product_id,
        product_name=exp_in.product_name.strip(),
        category_id=exp_in.category_id,
        amount=exp_in.amount,
        expense_date=exp_in.expense_date,
        payment_method=exp_in.payment_method or "UPI",
        notes=exp_in.notes
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return {"message": "Expense recorded successfully", "id": exp.id}


@router.get("/reports/pdf")
def download_pdf_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    products = db.query(models.Product).filter(models.Product.user_id == current_user.id).all()
    today = date.today()
    enriched = [enrich_product(p, today) for p in products]

    pdf_buffer = generate_inventory_pdf(enriched, current_user.full_name or current_user.username)
    filename = f"grocery_inventory_report_{today.strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/excel")
def download_excel_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    products = db.query(models.Product).filter(models.Product.user_id == current_user.id).all()
    today = date.today()
    enriched = [enrich_product(p, today) for p in products]

    flat_data = []
    for p in enriched:
        flat_data.append({
            "Item Name": p["name"],
            "Brand": p.get("brand") or "",
            "Category": p["category_name"],
            "Stock Quantity": p["quantity"],
            "Unit": p["unit"],
            "Min Threshold": p["min_quantity"],
            "Unit Price (₹)": p["unit_price"],
            "Total Value (₹)": p["total_value"],
            "Purchase Date": p["purchase_date"],
            "Expiry Date": p["expiry_date"],
            "Days Left": p["days_until_expiry"],
            "Expiry Status": p["expiry_status"].title(),
            "Stock Status": p["stock_status"].replace("_", " ").title(),
            "Storage": p["storage_location"],
            "Barcode": p.get("barcode") or ""
        })

    df = pd.DataFrame(flat_data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventory")
    buffer.seek(0)

    filename = f"grocery_inventory_{today.strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
