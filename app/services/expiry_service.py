from datetime import date
from typing import Dict, Any, Tuple
from app.config import EXPIRY_CRITICAL_DAYS, EXPIRY_WARNING_DAYS


def calculate_days_until_expiry(expiry_date: date, reference_date: date = None) -> int:
    """Calculate integer days from reference date (today) until product expiry date."""
    if reference_date is None:
        reference_date = date.today()
    return (expiry_date - reference_date).days


def classify_expiry(expiry_date: date, reference_date: date = None) -> Tuple[str, str]:
    """
    Classify product expiry status based on prompt specifications:
    - Expired ❌            (days < 0)
    - Expires in 1-3 days 🔴 (0 <= days <= 3)
    - Expires in 4-7 days 🟠 (4 <= days <= 7)
    - Fresh ✅               (days > 7)
    
    Returns:
        (status_code, badge_text)
    """
    days = calculate_days_until_expiry(expiry_date, reference_date)
    
    if days < 0:
        return "expired", f"Expired {abs(days)}d ago ❌"
    elif days == 0:
        return "critical", "Expires Today 🔴"
    elif 1 <= days <= EXPIRY_CRITICAL_DAYS:
        return "critical", f"Expires in {days} day{'s' if days > 1 else ''} 🔴"
    elif EXPIRY_CRITICAL_DAYS < days <= EXPIRY_WARNING_DAYS:
        return "warning", f"Expires in {days} days 🟠"
    else:
        return "fresh", f"Fresh ({days}d left) ✅"


def classify_stock(quantity: float, min_quantity: float) -> Tuple[str, str]:
    """
    Classify product inventory stock status:
    - Out of Stock ❌ (quantity <= 0)
    - Low Stock ⚠️    (0 < quantity <= min_quantity)
    - Available ✅    (quantity > min_quantity)
    
    Returns:
        (status_code, badge_text)
    """
    if quantity <= 0:
        return "out_of_stock", "Out of Stock ❌"
    elif quantity <= min_quantity:
        return "low_stock", "Low Stock ⚠️"
    else:
        return "available", "Available ✅"


def enrich_product(product: Any, reference_date: date = None) -> Dict[str, Any]:
    """Calculate and attach real-time dynamic properties to a product model or dict."""
    if reference_date is None:
        reference_date = date.today()

    days = calculate_days_until_expiry(product.expiry_date, reference_date)
    exp_status, exp_badge = classify_expiry(product.expiry_date, reference_date)
    stock_status, stock_badge = classify_stock(product.quantity, product.min_quantity)
    total_val = round(product.quantity * product.unit_price, 2)

    return {
        "id": product.id,
        "user_id": product.user_id,
        "name": product.name,
        "brand": product.brand,
        "category_id": product.category_id,
        "category_name": product.category.name if product.category else "General",
        "category_icon": product.category.icon if product.category else "📦",
        "quantity": product.quantity,
        "unit": product.unit,
        "min_quantity": product.min_quantity,
        "unit_price": product.unit_price,
        "purchase_date": product.purchase_date,
        "expiry_date": product.expiry_date,
        "barcode": product.barcode,
        "storage_location": product.storage_location,
        "notes": product.notes,
        "days_until_expiry": days,
        "expiry_status": exp_status,
        "expiry_badge_text": exp_badge,
        "stock_status": stock_status,
        "stock_badge_text": stock_badge,
        "total_value": total_val,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
