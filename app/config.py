import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = os.getenv("APP_NAME", "Smart Grocery Inventory & Expiry Tracker")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "smart_grocery_super_secret_jwt_key_2026_portfolio_mca")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 24 hours

# Database URL - SQLite default, or MySQL
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'smart_grocery.db'}")

# Expiry threshold rules (in days)
EXPIRY_CRITICAL_DAYS = 3  # Expires in 1-3 days
EXPIRY_WARNING_DAYS = 7   # Expires in 4-7 days

# Currency symbol
CURRENCY_SYMBOL = "₹"
