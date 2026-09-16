import io
import os
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta
from typing import Optional, List

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import bcrypt
from jose import JWTError, jwt
import uvicorn

from database import (
    users_col,
    categories_col,
    products_col,
    shopping_col,
    expenses_col,
    serialize_doc,
    init_db,
)
from services import (
    enrich_product,
    classify_expiry,
    classify_stock,
    get_dashboard_metrics,
    get_expense_analysis,
    generate_recommendations,
    generate_inventory_pdf,
    generate_inventory_excel,
)

# -----------------------------------------------------------------------------
# Configuration & Security
# -----------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "smart-grocery-secret-key-vibe-code-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Smart Grocery Inventory & Expiry Tracker",
    description="NoSQL MongoDB + FastAPI Vibe-Coded Architecture with Zero ORM",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract user from Bearer token or fallback to seeded user for frictionless demo."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id:
                try:
                    user = users_col.find_one({"_id": ObjectId(user_id)})
                except Exception:
                    user = users_col.find_one({"_id": user_id})
                if user:
                    return serialize_doc(user)
        except JWTError:
            pass

    # Seamless fallback: default to the active demo 'user' account
    demo_user = users_col.find_one({"username": "user"})
    if demo_user:
        return serialize_doc(demo_user)
    return {"id": "demo_user", "username": "user", "role": "user", "full_name": "Demo User"}


# -----------------------------------------------------------------------------
# Pydantic Request Models
# -----------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    role: str = "user"


class ProductCreate(BaseModel):
    name: str
    brand: Optional[str] = ""
    category_name: str
    quantity: float
    unit: str = "units"
    min_quantity: float = 1.0
    unit_price: float = 0.0
    purchase_date: str
    expiry_date: str
    storage_location: Optional[str] = "Pantry"


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    min_quantity: Optional[float] = None
    unit_price: Optional[float] = None
    purchase_date: Optional[str] = None
    expiry_date: Optional[str] = None
    storage_location: Optional[str] = None


class AdjustQuantity(BaseModel):
    delta: float


class ShoppingItemCreate(BaseModel):
    product_name: str
    category_name: str = "General"
    target_quantity: float = 1.0
    unit: str = "units"
    estimated_price: float = 0.0


class ExpenseCreate(BaseModel):
    product_name: str
    category_name: str
    amount: float
    quantity: float = 1.0
    unit: str = "units"
    expense_date: Optional[str] = None
    payment_method: str = "UPI"
    notes: Optional[str] = ""


# -----------------------------------------------------------------------------
# 1. Authentication Routes
# -----------------------------------------------------------------------------
@app.post("/api/auth/register")
def register(req: RegisterRequest):
    existing = users_col.find_one({"$or": [{"username": req.username}, {"email": req.email}]})
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed = get_password_hash(req.password)
    res = users_col.insert_one({
        "username": req.username,
        "email": req.email,
        "full_name": req.full_name,
        "hashed_password": hashed,
        "role": req.role,
        "created_at": datetime.utcnow()
    })
    token = create_access_token({"sub": str(res.inserted_id), "username": req.username, "role": req.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(res.inserted_id),
            "username": req.username,
            "full_name": req.full_name,
            "role": req.role
        }
    }


@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = users_col.find_one({"username": req.username})
    if not user or not verify_password(req.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": str(user["_id"]), "username": user["username"], "role": user.get("role", "user")})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "full_name": user.get("full_name", user["username"]),
            "role": user.get("role", "user")
        }
    }


@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return user


# -----------------------------------------------------------------------------
# 2. Categories Route
# -----------------------------------------------------------------------------
@app.get("/api/categories")
def get_categories():
    cats = list(categories_col.find().sort("name", 1))
    return [serialize_doc(c) for c in cats]


# -----------------------------------------------------------------------------
# 3. Dashboard Route
# -----------------------------------------------------------------------------
@app.get("/api/dashboard")
def get_dashboard(user: dict = Depends(get_current_user)):
    uid = user["id"]
    kpis = get_dashboard_metrics(uid)
    recs = generate_recommendations(uid)
    exp_analysis = get_expense_analysis(uid)

    raw_products = list(products_col.find({"user_id": uid}))
    today = date.today()
    enriched = [enrich_product(p, today) for p in raw_products]

    expiring_preview = [p for p in enriched if p["expiry_status"] in ("critical", "warning", "expired")]
    expiring_preview.sort(key=lambda x: x["days_until_expiry"])
    expiring_preview = expiring_preview[:5]

    low_stock_preview = [p for p in enriched if p["stock_status"] in ("low_stock", "out_of_stock")]
    low_stock_preview.sort(key=lambda x: x["quantity"])
    low_stock_preview = low_stock_preview[:5]

    return {
        "kpis": kpis,
        "recommendations": recs,
        "expense_analysis": exp_analysis,
        "expiring_preview": expiring_preview,
        "low_stock_preview": low_stock_preview,
    }


# -----------------------------------------------------------------------------
# 4. Inventory CRUD Routes
# -----------------------------------------------------------------------------
@app.get("/api/inventory")
def list_inventory(
    search: Optional[str] = None,
    category: Optional[str] = None,
    expiry_status: Optional[str] = None,
    stock_status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    uid = user["id"]
    query = {"user_id": uid}
    if category and category != "all":
        query["category_name"] = category

    docs = list(products_col.find(query))
    today = date.today()
    enriched = [enrich_product(d, today) for d in docs]

    if search:
        s = search.lower()
        enriched = [p for p in enriched if s in p["name"].lower() or s in p.get("brand", "").lower() or s in p.get("category_name", "").lower()]

    if expiry_status and expiry_status != "all":
        enriched = [p for p in enriched if p["expiry_status"] == expiry_status]

    if stock_status and stock_status != "all":
        enriched = [p for p in enriched if p["stock_status"] == stock_status]

    enriched.sort(key=lambda x: x["days_until_expiry"])
    return enriched


@app.post("/api/inventory")
def create_product(data: ProductCreate, user: dict = Depends(get_current_user)):
    uid = user["id"]
    doc = data.dict()
    doc["user_id"] = uid
    res = products_col.insert_one(doc)
    doc["_id"] = res.inserted_id

    if doc.get("unit_price", 0) > 0 and doc.get("quantity", 0) > 0:
        total_spent = round(float(doc["quantity"]) * float(doc["unit_price"]), 2)
        expenses_col.insert_one({
            "user_id": uid,
            "product_id": str(res.inserted_id),
            "product_name": doc["name"],
            "category_name": doc.get("category_name", "General"),
            "amount": total_spent,
            "quantity": doc["quantity"],
            "unit": doc["unit"],
            "expense_date": doc.get("purchase_date") or str(date.today()),
            "payment_method": "UPI",
            "notes": "Inventory addition"
        })

    if doc["quantity"] <= doc["min_quantity"]:
        sync_single_product_to_shopping(uid, doc)

    return enrich_product(doc)


@app.get("/api/inventory/{product_id}")
def get_product(product_id: str, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(product_id)
        doc = products_col.find_one({"_id": oid, "user_id": user["id"]})
    except Exception:
        doc = products_col.find_one({"_id": product_id, "user_id": user["id"]})

    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return enrich_product(doc)


@app.put("/api/inventory/{product_id}")
def update_product(product_id: str, data: ProductUpdate, user: dict = Depends(get_current_user)):
    uid = user["id"]
    update_fields = {k: v for k, v in data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        oid = ObjectId(product_id)
        filter_q = {"_id": oid, "user_id": uid}
    except Exception:
        filter_q = {"_id": product_id, "user_id": uid}

    products_col.update_one(filter_q, {"$set": update_fields})
    updated = products_col.find_one(filter_q)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")

    if updated.get("quantity", 0) <= updated.get("min_quantity", 1):
        sync_single_product_to_shopping(uid, updated)

    return enrich_product(updated)


@app.delete("/api/inventory/{product_id}")
def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(product_id)
        res = products_col.delete_one({"_id": oid, "user_id": user["id"]})
    except Exception:
        res = products_col.delete_one({"_id": product_id, "user_id": user["id"]})

    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "success", "message": "Product deleted"}


@app.patch("/api/inventory/{product_id}/adjust")
def adjust_quantity(product_id: str, payload: AdjustQuantity, user: dict = Depends(get_current_user)):
    uid = user["id"]
    try:
        oid = ObjectId(product_id)
        filter_q = {"_id": oid, "user_id": uid}
    except Exception:
        filter_q = {"_id": product_id, "user_id": uid}

    doc = products_col.find_one(filter_q)
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")

    new_qty = max(0.0, round(float(doc.get("quantity", 0)) + float(payload.delta), 2))
    products_col.update_one(filter_q, {"$set": {"quantity": new_qty}})
    doc["quantity"] = new_qty

    if new_qty <= doc.get("min_quantity", 1.0):
        sync_single_product_to_shopping(uid, doc)

    return enrich_product(doc)


def sync_single_product_to_shopping(user_id: str, product: dict):
    pid = str(product["_id"])
    existing = shopping_col.find_one({"user_id": user_id, "product_id": pid, "is_purchased": False})
    needed = max(round(product.get("min_quantity", 1.0) * 2 - product.get("quantity", 0.0), 1), 1.0)
    if not existing:
        shopping_col.insert_one({
            "user_id": user_id,
            "product_id": pid,
            "product_name": product["name"],
            "category_name": product.get("category_name", "General"),
            "target_quantity": needed,
            "unit": product.get("unit", "units"),
            "estimated_price": round(needed * float(product.get("unit_price", 0.0)), 2),
            "is_purchased": False,
            "auto_added": True
        })


# -----------------------------------------------------------------------------
# 5. Shopping List Routes
# -----------------------------------------------------------------------------
@app.get("/api/shopping")
def list_shopping_items(user: dict = Depends(get_current_user)):
    items = list(shopping_col.find({"user_id": user["id"]}))
    total_est = sum(i.get("estimated_price", 0.0) for i in items if not i.get("is_purchased"))
    return {
        "items": [serialize_doc(i) for i in items],
        "total_estimated_cost": round(total_est, 2),
        "pending_count": sum(1 for i in items if not i.get("is_purchased")),
    }


@app.post("/api/shopping")
def add_shopping_item(data: ShoppingItemCreate, user: dict = Depends(get_current_user)):
    uid = user["id"]
    doc = data.dict()
    doc["user_id"] = uid
    doc["is_purchased"] = False
    doc["auto_added"] = False
    res = shopping_col.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return serialize_doc(doc)


@app.post("/api/shopping/sync")
def sync_low_stock_items(user: dict = Depends(get_current_user)):
    uid = user["id"]
    products = list(products_col.find({"user_id": uid}))
    added_count = 0
    for p in products:
        if float(p.get("quantity", 0)) <= float(p.get("min_quantity", 1.0)):
            pid = str(p["_id"])
            existing = shopping_col.find_one({"user_id": uid, "product_id": pid, "is_purchased": False})
            if not existing:
                sync_single_product_to_shopping(uid, p)
                added_count += 1
    return {"status": "success", "synced_items": added_count}


@app.patch("/api/shopping/{item_id}/toggle")
def toggle_shopping_item(item_id: str, user: dict = Depends(get_current_user)):
    uid = user["id"]
    try:
        oid = ObjectId(item_id)
        filter_q = {"_id": oid, "user_id": uid}
    except Exception:
        filter_q = {"_id": item_id, "user_id": uid}

    item = shopping_col.find_one(filter_q)
    if not item:
        raise HTTPException(status_code=404, detail="Shopping item not found")

    new_status = not item.get("is_purchased", False)
    shopping_col.update_one(filter_q, {"$set": {"is_purchased": new_status}})

    if new_status and item.get("product_id"):
        try:
            pid = ObjectId(item["product_id"])
        except Exception:
            pid = item["product_id"]
        p = products_col.find_one({"_id": pid})
        if p:
            restocked_qty = p.get("quantity", 0) + item.get("target_quantity", 1.0)
            products_col.update_one({"_id": pid}, {"$set": {"quantity": restocked_qty}})

    return {"status": "success", "is_purchased": new_status}


@app.delete("/api/shopping/{item_id}")
def delete_shopping_item(item_id: str, user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(item_id)
        res = shopping_col.delete_one({"_id": oid, "user_id": user["id"]})
    except Exception:
        res = shopping_col.delete_one({"_id": item_id, "user_id": user["id"]})

    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "success", "message": "Shopping item removed"}


@app.delete("/api/shopping/clear-purchased")
def clear_purchased_shopping(user: dict = Depends(get_current_user)):
    res = shopping_col.delete_many({"user_id": user["id"], "is_purchased": True})
    return {"status": "success", "deleted_count": res.deleted_count}


# -----------------------------------------------------------------------------
# 6. Expenses Routes
# -----------------------------------------------------------------------------
@app.get("/api/expenses")
def list_expenses(user: dict = Depends(get_current_user)):
    uid = user["id"]
    items = list(expenses_col.find({"user_id": uid}).sort("expense_date", -1))
    analysis = get_expense_analysis(uid)
    return {
        "expenses": [serialize_doc(e) for e in items],
        "analysis": analysis
    }


@app.post("/api/expenses")
def add_expense(data: ExpenseCreate, user: dict = Depends(get_current_user)):
    uid = user["id"]
    doc = data.dict()
    doc["user_id"] = uid
    if not doc.get("expense_date"):
        doc["expense_date"] = str(date.today())
    res = expenses_col.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return serialize_doc(doc)


@app.get("/api/expenses/analysis")
def expense_analytics(user: dict = Depends(get_current_user)):
    return get_expense_analysis(user["id"])


# -----------------------------------------------------------------------------
# 7. Reports Routes (PDF & Excel)
# -----------------------------------------------------------------------------
@app.get("/api/reports/pdf")
def download_pdf(user: dict = Depends(get_current_user)):
    uid = user["id"]
    raw = list(products_col.find({"user_id": uid}))
    enriched = [enrich_product(p) for p in raw]
    pdf_io = generate_inventory_pdf(enriched, user_full_name=user.get("full_name", "User"))
    pdf_io.seek(0)
    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=SmartGrocery_Inventory_Report.pdf"}
    )


@app.get("/api/reports/excel")
def download_excel(user: dict = Depends(get_current_user)):
    uid = user["id"]
    raw = list(products_col.find({"user_id": uid}))
    enriched = [enrich_product(p) for p in raw]
    excel_io = generate_inventory_excel(enriched)
    excel_io.seek(0)
    return StreamingResponse(
        excel_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=SmartGrocery_Inventory.xlsx"}
    )


# -----------------------------------------------------------------------------
# 8. Static Web App Mounting
# -----------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Smart Grocery Inventory Tracker API is active. Open /docs for API schema."}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
