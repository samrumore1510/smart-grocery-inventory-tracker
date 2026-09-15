from typing import List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/shopping-list", tags=["Smart Shopping List"])


@router.get("", response_model=List[schemas.ShoppingItemResponse])
def get_shopping_list(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    items = (
        db.query(models.ShoppingItem)
        .filter(models.ShoppingItem.user_id == current_user.id)
        .order_by(models.ShoppingItem.is_purchased.asc(), models.ShoppingItem.id.desc())
        .all()
    )
    result = []
    for it in items:
        cat_name = it.category.name if it.category else "General"
        res_dict = {
            "id": it.id,
            "user_id": it.user_id,
            "product_id": it.product_id,
            "product_name": it.product_name,
            "category_id": it.category_id,
            "category_name": cat_name,
            "target_quantity": it.target_quantity,
            "unit": it.unit,
            "estimated_price": it.estimated_price,
            "is_purchased": it.is_purchased,
            "auto_added": it.auto_added,
            "created_at": it.created_at
        }
        result.append(res_dict)
    return result


@router.post("", response_model=schemas.ShoppingItemResponse, status_code=status.HTTP_201_CREATED)
def add_shopping_item(
    item_in: schemas.ShoppingItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = models.ShoppingItem(
        user_id=current_user.id,
        product_id=item_in.product_id,
        product_name=item_in.product_name.strip(),
        category_id=item_in.category_id,
        target_quantity=item_in.target_quantity,
        unit=item_in.unit,
        estimated_price=item_in.estimated_price,
        is_purchased=False,
        auto_added=False
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    cat_name = item.category.name if item.category else "General"
    return {
        "id": item.id,
        "user_id": item.user_id,
        "product_id": item.product_id,
        "product_name": item.product_name,
        "category_id": item.category_id,
        "category_name": cat_name,
        "target_quantity": item.target_quantity,
        "unit": item.unit,
        "estimated_price": item.estimated_price,
        "is_purchased": item.is_purchased,
        "auto_added": item.auto_added,
        "created_at": item.created_at
    }


@router.post("/auto-sync", status_code=status.HTTP_200_OK)
def sync_low_stock_to_shopping_list(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Scan all user products; add low stock and out-of-stock items to the shopping list."""
    products = db.query(models.Product).filter(models.Product.user_id == current_user.id).all()
    added_count = 0
    today = date.today()

    for p in products:
        if p.quantity <= p.min_quantity:
            # Check if active unpurchased item already exists
            existing = db.query(models.ShoppingItem).filter(
                models.ShoppingItem.user_id == current_user.id,
                models.ShoppingItem.product_name == p.name,
                models.ShoppingItem.is_purchased == False
            ).first()
            if not existing:
                needed = max(round(p.min_quantity * 2 - p.quantity, 2), 1.0)
                item = models.ShoppingItem(
                    user_id=current_user.id,
                    product_id=p.id,
                    product_name=p.name,
                    category_id=p.category_id,
                    target_quantity=needed,
                    unit=p.unit,
                    estimated_price=round(needed * p.unit_price, 2),
                    is_purchased=False,
                    auto_added=True
                )
                db.add(item)
                added_count += 1

    db.commit()
    return {"message": f"Synced {added_count} low-stock items into shopping list", "added_count": added_count}


@router.post("/{item_id}/mark-purchased")
def mark_item_as_purchased(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Marks item as purchased, restocks product in inventory, and creates an expense record.
    """
    item = db.query(models.ShoppingItem).filter(
        models.ShoppingItem.id == item_id,
        models.ShoppingItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Shopping item not found")

    item.is_purchased = True

    # If linked to an existing product, restock it
    if item.product_id:
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if prod:
            prod.quantity = round(prod.quantity + item.target_quantity, 2)
            prod.purchase_date = date.today()
            # Extend expiry by typical duration (e.g. 14 days if was expired or soon)
            if prod.expiry_date <= date.today():
                prod.expiry_date = date.today() + timedelta(days=30)
    else:
        # Check if matching by name exists
        prod = db.query(models.Product).filter(
            models.Product.user_id == current_user.id,
            models.Product.name.ilike(item.product_name)
        ).first()
        if prod:
            prod.quantity = round(prod.quantity + item.target_quantity, 2)
            prod.purchase_date = date.today()
            if prod.expiry_date <= date.today():
                prod.expiry_date = date.today() + timedelta(days=30)

    # Log Expense
    if item.estimated_price > 0:
        exp = models.ExpenseLog(
            user_id=current_user.id,
            product_id=item.product_id,
            product_name=item.product_name,
            category_id=item.category_id,
            amount=item.estimated_price,
            expense_date=date.today(),
            payment_method="UPI",
            notes=f"Purchased from smart shopping list: {item.target_quantity} {item.unit}"
        )
        db.add(exp)

    db.commit()
    return {"message": f"'{item.product_name}' marked as purchased and inventory updated!"}


@router.delete("/{item_id}")
def delete_shopping_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    item = db.query(models.ShoppingItem).filter(
        models.ShoppingItem.id == item_id,
        models.ShoppingItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Shopping item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted from shopping list"}


@router.delete("/clear/purchased")
def clear_purchased_items(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    count = db.query(models.ShoppingItem).filter(
        models.ShoppingItem.user_id == current_user.id,
        models.ShoppingItem.is_purchased == True
    ).delete()
    db.commit()
    return {"message": f"Cleared {count} purchased items"}
