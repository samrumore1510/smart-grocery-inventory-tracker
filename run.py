"""
One-click application launcher for Smart Grocery Inventory & Expiry Tracker.
Initializes database, automatically seeds demo data if required, and starts Uvicorn server.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.config import HOST, PORT, APP_NAME
from app.database import init_db, SessionLocal
from app import models
from scripts.seed_data import seed


def startup_check():
    print("=" * 70)
    print(f"🚀  Starting {APP_NAME}")
    print("=" * 70)

    # Initialize tables
    init_db()

    # Check if database has products; if empty, automatically run seed
    db = SessionLocal()
    try:
        product_count = db.query(models.Product).count()
        if product_count == 0:
            print("📦 Empty database detected. Auto-seeding 35 demo grocery items...")
            seed()
        else:
            print(f"✅ Found {product_count} existing grocery items in database.")
    except Exception as e:
        print(f"⚠️  Database initialization note: {e}")
    finally:
        db.close()

    print("\n🌐  Application Server running at:")
    print(f"    👉 Web Application: http://{HOST}:{PORT}")
    print(f"    👉 Swagger API Docs: http://{HOST}:{PORT}/docs")
    print(f"    👉 Redoc API Docs:    http://{HOST}:{PORT}/redoc")
    print("\n🔑  Demo Credentials for Viva / Evaluation:")
    print("    • User Login:  user  / user123  (Household view with 35 items)")
    print("    • Admin Login: admin / admin123 (Store manager view)")
    print("=" * 70)


if __name__ == "__main__":
    startup_check()
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=True
    )
