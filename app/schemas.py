from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[str] = "user"


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# Category Schemas
class CategoryBase(BaseModel):
    name: str
    icon: Optional[str] = "📦"
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category_id: int
    brand: Optional[str] = None
    quantity: float = Field(..., ge=0)
    unit: str = "kg"
    min_quantity: float = Field(default=1.0, ge=0)
    unit_price: float = Field(default=0.0, ge=0)
    purchase_date: date = Field(default_factory=date.today)
    expiry_date: date
    barcode: Optional[str] = None
    storage_location: Optional[str] = "Pantry"
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    min_quantity: Optional[float] = None
    unit_price: Optional[float] = None
    purchase_date: Optional[date] = None
    expiry_date: Optional[date] = None
    barcode: Optional[str] = None
    storage_location: Optional[str] = None
    notes: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductWithStatus(ProductResponse):
    days_until_expiry: int
    expiry_status: str       # "expired", "critical", "warning", "fresh"
    expiry_badge_text: str   # "Expired ❌", "Expires in 1-3 days 🔴", etc.
    stock_status: str        # "out_of_stock", "low_stock", "available"
    stock_badge_text: str    # "Out of Stock ❌", "Low Stock ⚠️", "Available ✅"
    total_value: float       # quantity * unit_price
    category_name: Optional[str] = None
    category_icon: Optional[str] = None


# Shopping Item Schemas
class ShoppingItemBase(BaseModel):
    product_name: str
    category_id: Optional[int] = None
    target_quantity: float = 1.0
    unit: str = "kg"
    estimated_price: float = 0.0
    product_id: Optional[int] = None


class ShoppingItemCreate(ShoppingItemBase):
    pass


class ShoppingItemUpdate(BaseModel):
    target_quantity: Optional[float] = None
    unit: Optional[str] = None
    estimated_price: Optional[float] = None
    is_purchased: Optional[bool] = None


class ShoppingItemResponse(ShoppingItemBase):
    id: int
    user_id: int
    is_purchased: bool
    auto_added: bool
    created_at: datetime
    category_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# Expense Schemas
class ExpenseCreate(BaseModel):
    product_name: str
    amount: float = Field(..., ge=0)
    category_id: Optional[int] = None
    product_id: Optional[int] = None
    expense_date: date = Field(default_factory=date.today)
    payment_method: Optional[str] = "UPI"
    notes: Optional[str] = None


class ExpenseResponse(ExpenseCreate):
    id: int
    user_id: int
    created_at: datetime
    category_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# Recommendations & Dashboard Schemas
class RecommendationItem(BaseModel):
    type: str                # "expiry_urgent", "low_stock", "recipe", "prediction"
    title: str
    message: str
    icon: str
    severity: str            # "critical", "warning", "info", "success"
    action_label: Optional[str] = None
    action_url: Optional[str] = None


class DashboardStats(BaseModel):
    total_products: int
    expiring_soon: int
    expired: int
    low_stock: int
    monthly_spending: float
    total_inventory_value: float
    wastage_cost: float
