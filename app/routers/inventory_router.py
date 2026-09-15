from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
from app.services.expiry_service import enrich_product

router = APIRouter(prefix="/api/inventory", tags=["Grocery Inventory"])


@router.get("", response_model=List[schemas.ProductWithStatus])
def list_inventory(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    expiry_filter: Optional[str] = Query(None, description="all, expired, critical, warning, fresh, expiring"),
    stock_filter: Optional[str] = Query(None, description="all, low_stock, out_of_stock, available"),
    sort_by: Optional[str] = Query("expiry_asc", description="expiry_asc, expiry_desc, name_asc, qty_asc, qty_desc"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Product).filter(models.Product.user_id == current_user.id)

    if category_id:
        query = query.filter(models.Product.category_id == category_id)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (models.Product.name.ilike(search_pattern)) | 
            (models.Product.brand.ilike(search_pattern)) |
            (models.Product.barcode.ilike(search_pattern))
        )

    products = query.all()
    today = date.today()
    enriched_products = [enrich_product(p, today) for p in products]

    # Filter by Expiry Status in memory
    if expiry_filter and expiry_filter != "all":
        if expiry_filter == "expiring":
            enriched_products = [p for p in enriched_products if p["expiry_status"] in ("critical", "warning")]
        else:
            enriched_products = [p for p in enriched_products if p["expiry_status"] == expiry_filter]

    # Filter by Stock Status in memory
    if stock_filter and stock_filter != "all":
        enriched_products = [p for p in enriched_products if p["stock_status"] == stock_filter]

    # Sorting
    if sort_by == "expiry_asc":
        enriched_products.sort(key=lambda x: x["expiry_date"])
    elif sort_by == "expiry_desc":
        enriched_products.sort(key=lambda x: x["expiry_date"], reverse=True)
    elif sort_by == "name_asc":
        enriched_products.sort(key=lambda x: x["name"].lower())
    elif sort_by == "qty_asc":
        enriched_products.sort(key=lambda x: x["quantity"])
    elif sort_by == "qty_desc":
        enriched_products.sort(key=lambda x: x["quantity"], reverse=True)

    return enriched_products


@router.post("", response_model=schemas.ProductWithStatus, status_code=status.HTTP_201_CREATED)
def add_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify category exists
    cat = db.query(models.Category).filter(models.Category.id == product_in.category_id).first()
    if not cat:
        raise HTTPException(status_code=400, detail="Invalid category ID")

    new_prod = models.Product(
        user_id=current_user.id,
        name=product_in.name.strip(),
        brand=product_in.brand.strip() if product_in.brand else None,
        category_id=product_in.category_id,
        quantity=product_in.quantity,
        unit=product_in.unit,
        min_quantity=product_in.min_quantity,
        unit_price=product_in.unit_price,
        purchase_date=product_in.purchase_date,
        expiry_date=product_in.expiry_date,
        barcode=product_in.barcode.strip() if product_in.barcode else None,
        storage_location=product_in.storage_location or "Pantry",
        notes=product_in.notes
    )
    db.add(new_prod)
    db.flush()  # to get new_prod.id

    # Automatically log initial purchase expense if unit_price > 0
    total_cost = round(new_prod.quantity * new_prod.unit_price, 2)
    if total_cost > 0:
        exp_log = models.ExpenseLog(
            user_id=current_user.id,
            product_id=new_prod.id,
            product_name=new_prod.name,
            category_id=new_prod.category_id,
            amount=total_cost,
            expense_date=new_prod.purchase_date,
            payment_method="UPI",
            notes=f"Initial purchase of {new_prod.quantity} {new_prod.unit}"
        )
        db.add(exp_log)

    # If added with quantity <= min_quantity, automatically flag into shopping items
    if new_prod.quantity <= new_prod.min_quantity:
        existing_item = db.query(models.ShoppingItem).filter(
            models.ShoppingItem.user_id == current_user.id,
            models.ShoppingItem.product_name == new_prod.name,
            models.ShoppingItem.is_purchased == False
        ).first()
        if not existing_item:
            needed_qty = max(new_prod.min_quantity * 2 - new_prod.quantity, 1.0)
            shop_item = models.ShoppingItem(
                user_id=current_user.id,
                product_id=new_prod.id,
                product_name=new_prod.name,
                category_id=new_prod.category_id,
                target_quantity=needed_qty,
                unit=new_prod.unit,
                estimated_price=round(needed_qty * new_prod.unit_price, 2),
                is_purchased=False,
                auto_added=True
            )
            db.add(shop_item)

    db.commit()
    db.refresh(new_prod)
    return enrich_product(new_prod, date.today())


@router.get("/{product_id}", response_model=schemas.ProductWithStatus)
def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prod = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id
    ).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return enrich_product(prod, date.today())


@router.put("/{product_id}", response_model=schemas.ProductWithStatus)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prod = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id
    ).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prod, key, value)

    # Check if stock dropped below minimum
    if prod.quantity <= prod.min_quantity:
        existing_item = db.query(models.ShoppingItem).filter(
            models.ShoppingItem.user_id == current_user.id,
            models.ShoppingItem.product_name == prod.name,
            models.ShoppingItem.is_purchased == False
        ).first()
        if not existing_item:
            needed_qty = max(prod.min_quantity * 2 - prod.quantity, 1.0)
            shop_item = models.ShoppingItem(
                user_id=current_user.id,
                product_id=prod.id,
                product_name=prod.name,
                category_id=prod.category_id,
                target_quantity=needed_qty,
                unit=prod.unit,
                estimated_price=round(needed_qty * prod.unit_price, 2),
                is_purchased=False,
                auto_added=True
            )
            db.add(shop_item)

    db.commit()
    db.refresh(prod)
    return enrich_product(prod, date.today())


@router.patch("/{product_id}/adjust", response_model=schemas.ProductWithStatus)
def adjust_product_quantity(
    product_id: int,
    delta: float = Query(..., description="Positive or negative number to adjust stock"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prod = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id
    ).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    new_qty = max(round(prod.quantity + delta, 2), 0.0)
    prod.quantity = new_qty

    # Check if low stock triggered
    if prod.quantity <= prod.min_quantity:
        existing_item = db.query(models.ShoppingItem).filter(
            models.ShoppingItem.user_id == current_user.id,
            models.ShoppingItem.product_name == prod.name,
            models.ShoppingItem.is_purchased == False
        ).first()
        if not existing_item:
            needed = max(prod.min_quantity * 2 - prod.quantity, 1.0)
            shop_item = models.ShoppingItem(
                user_id=current_user.id,
                product_id=prod.id,
                product_name=prod.name,
                category_id=prod.category_id,
                target_quantity=needed,
                unit=prod.unit,
                estimated_price=round(needed * prod.unit_price, 2),
                is_purchased=False,
                auto_added=True
            )
            db.add(shop_item)

    db.commit()
    db.refresh(prod)
    return enrich_product(prod, date.today())


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prod = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id
    ).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(prod)
    db.commit()
    return {"message": f"Product '{prod.name}' deleted successfully", "id": product_id}


@router.get("/categories/all", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Category).order_by(models.Category.id).all()
    return categories
