"""
Seed database script for Smart Grocery Inventory & Expiry Tracker.
Configures default categories, demo users ('admin' and 'user'), and pre-loads
exactly 35 realistic grocery items matching the portfolio dashboard specifications:
- Total Products: 35
- Expiring Soon: 4
- Expired: 2
- Low Stock: 5
- Monthly Spending: ~₹4,250
"""

import sys
from pathlib import Path
from datetime import date, timedelta, datetime

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal, init_db
from app import models
from app.auth import get_password_hash


def seed():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Categories
        categories_data = [
            {"id": 1, "name": "Dairy & Eggs", "icon": "🥛", "description": "Milk, cheese, butter, yogurt, eggs"},
            {"id": 2, "name": "Grains & Pulses", "icon": "🌾", "description": "Rice, atta, dal, lentils, oats"},
            {"id": 3, "name": "Vegetables & Fruits", "icon": "🥦", "description": "Fresh produce and greens"},
            {"id": 4, "name": "Oils & Ghee", "icon": "🛢️", "description": "Cooking oil, mustard oil, ghee"},
            {"id": 5, "name": "Spices & Seasoning", "icon": "🧂", "description": "Salt, pepper, turmeric, masala"},
            {"id": 6, "name": "Snacks & Beverages", "icon": "🍪", "description": "Biscuits, tea, coffee, noodles"},
            {"id": 7, "name": "Meat & Seafood", "icon": "🍗", "description": "Chicken, fish, eggs, paneer"},
            {"id": 8, "name": "Bakery & Breads", "icon": "🍞", "description": "Bread, buns, baked goods"},
            {"id": 9, "name": "Household & Cleaning", "icon": "🧼", "description": "Detergents, dishwash, cleaners"},
            {"id": 10, "name": "Personal Care", "icon": "🧴", "description": "Soap, toothpaste, shampoo"}
        ]

        for cat in categories_data:
            existing = db.query(models.Category).filter(models.Category.id == cat["id"]).first()
            if not existing:
                db.add(models.Category(**cat))
        db.commit()
        print("Categories seeded.")

        # 2. Seed Demo Users
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                email="admin@smartgrocery.com",
                full_name="Portfolio Admin",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin_user)

        demo_user = db.query(models.User).filter(models.User.username == "user").first()
        if not demo_user:
            demo_user = models.User(
                username="user",
                email="user@smartgrocery.com",
                full_name="Samruddhi (MCA)",
                hashed_password=get_password_hash("user123"),
                role="user"
            )
            db.add(demo_user)
        db.commit()
        db.refresh(admin_user)
        db.refresh(demo_user)
        print("Users created: admin / admin123 and user / user123")

        # 3. Clean and seed Products for demo_user
        # Clear existing products for fresh reliable metrics
        db.query(models.ShoppingItem).filter(models.ShoppingItem.user_id == demo_user.id).delete()
        db.query(models.ExpenseLog).filter(models.ExpenseLog.user_id == demo_user.id).delete()
        db.query(models.Product).filter(models.Product.user_id == demo_user.id).delete()
        db.commit()

        today = date.today()

        # Product plan:
        # Total = 35 items
        # Expired (< today) = 2 items
        # Expiring Soon (1-7 days) = 4 items
        # Fresh (> 7 days) = 29 items
        # Low Stock (qty <= min_qty) = 5 items (specifically: 1 out-of-stock, 4 low-stock)

        products_list = [
            # --- 2 EXPIRED ITEMS ---
            {
                "name": "Britannia Brown Bread",
                "brand": "Britannia",
                "category_id": 8,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 1.0,  # [Low Stock #1]
                "unit_price": 50.0,
                "purchase_date": today - timedelta(days=7),
                "expiry_date": today - timedelta(days=2),  # Expired 2 days ago
                "storage_location": "Kitchen Counter",
                "barcode": "8901063012111",
                "notes": "Purchased last week"
            },
            {
                "name": "Epigamia Greek Yogurt (Blueberry)",
                "brand": "Epigamia",
                "category_id": 1,
                "quantity": 2.0,
                "unit": "pcs",
                "min_quantity": 1.0,
                "unit_price": 60.0,
                "purchase_date": today - timedelta(days=10),
                "expiry_date": today - timedelta(days=1),  # Expired 1 day ago
                "storage_location": "Refrigerator",
                "barcode": "8906073120199",
                "notes": "Unopened cup in fridge"
            },

            # --- 4 EXPIRING SOON ITEMS (1-7 Days) ---
            {
                "name": "Amul Taaza Toned Milk (1L)",
                "brand": "Amul",
                "category_id": 1,
                "quantity": 1.0,
                "unit": "L",
                "min_quantity": 2.0,  # [Low Stock #2]
                "unit_price": 56.0,
                "purchase_date": today - timedelta(days=2),
                "expiry_date": today + timedelta(days=1),  # Expiring Tomorrow! (Critical 1-3d)
                "storage_location": "Refrigerator",
                "barcode": "8901262010017",
                "notes": "Keep refrigerated"
            },
            {
                "name": "Fresh Organic Spinach (Palak)",
                "brand": "Fresh Farms",
                "category_id": 3,
                "quantity": 2.0,
                "unit": "packets",
                "min_quantity": 1.0,
                "unit_price": 30.0,
                "purchase_date": today - timedelta(days=1),
                "expiry_date": today + timedelta(days=2),  # Expiring in 2 days (Critical 1-3d)
                "storage_location": "Refrigerator",
                "barcode": "8904000100021",
                "notes": "Use for palak paneer"
            },
            {
                "name": "Hybrid Red Tomatoes",
                "brand": "Local Market",
                "category_id": 3,
                "quantity": 1.5,
                "unit": "kg",
                "min_quantity": 1.0,
                "unit_price": 40.0,
                "purchase_date": today - timedelta(days=2),
                "expiry_date": today + timedelta(days=3),  # Expiring in 3 days (Critical 1-3d)
                "storage_location": "Kitchen Counter",
                "barcode": "8904000100038",
                "notes": "Ripe, consume soon"
            },
            {
                "name": "Amul Fresh Malai Paneer (200g)",
                "brand": "Amul",
                "category_id": 1,
                "quantity": 2.0,
                "unit": "packets",
                "min_quantity": 1.0,
                "unit_price": 90.0,
                "purchase_date": today - timedelta(days=3),
                "expiry_date": today + timedelta(days=5),  # Expiring in 5 days (Warning 4-7d)
                "storage_location": "Refrigerator",
                "barcode": "8901262020023",
                "notes": "Vacuum sealed"
            },

            # --- 29 FRESH ITEMS (> 7 Days) including 3 Low/Out of Stock items ---
            # [Low Stock #3 - Rice 1 kg / min 2 kg]
            {
                "name": "Daawat Rozana Super Basmati Rice",
                "brand": "Daawat",
                "category_id": 2,
                "quantity": 1.0,
                "unit": "kg",
                "min_quantity": 2.0,  # LOW STOCK
                "unit_price": 95.0,
                "purchase_date": today - timedelta(days=15),
                "expiry_date": today + timedelta(days=240),
                "storage_location": "Pantry",
                "barcode": "8901030001000",
                "notes": "Pantry grain box"
            },
            # [Low Stock #4 - Oil 0 L (Out of Stock)]
            {
                "name": "Fortune Sunlite Refined Sunflower Oil",
                "brand": "Fortune",
                "category_id": 4,
                "quantity": 0.0,
                "unit": "L",
                "min_quantity": 2.0,  # OUT OF STOCK
                "unit_price": 165.0,
                "purchase_date": today - timedelta(days=28),
                "expiry_date": today + timedelta(days=180),
                "storage_location": "Pantry",
                "barcode": "8906007280014",
                "notes": "Finished cooking oil bottle"
            },
            # [Low Stock #5 - Sugar 0.5 kg / min 1 kg]
            {
                "name": "Madhur Pure & Hygienic Sugar",
                "brand": "Madhur",
                "category_id": 2,
                "quantity": 0.5,
                "unit": "kg",
                "min_quantity": 1.0,  # LOW STOCK
                "unit_price": 48.0,
                "purchase_date": today - timedelta(days=20),
                "expiry_date": today + timedelta(days=300),
                "storage_location": "Pantry",
                "barcode": "8906014410015",
                "notes": "Sugar jar near empty"
            },

            # Other Fresh Items (26 more to reach 35 total)
            {
                "name": "Aashirvaad Shudh Chakki Atta (5kg)",
                "brand": "Aashirvaad",
                "category_id": 2,
                "quantity": 5.0,
                "unit": "kg",
                "min_quantity": 2.0,
                "unit_price": 55.0,
                "purchase_date": today - timedelta(days=5),
                "expiry_date": today + timedelta(days=85),
                "storage_location": "Pantry",
                "barcode": "8901725131238"
            },
            {
                "name": "Tata Salt Vacuum Evaporated",
                "brand": "Tata",
                "category_id": 5,
                "quantity": 2.0,
                "unit": "kg",
                "min_quantity": 1.0,
                "unit_price": 28.0,
                "purchase_date": today - timedelta(days=10),
                "expiry_date": today + timedelta(days=365),
                "storage_location": "Pantry",
                "barcode": "8901030383847"
            },
            {
                "name": "Tata Sampann Toor Dal (Pigeon Pea)",
                "brand": "Tata Sampann",
                "category_id": 2,
                "quantity": 2.0,
                "unit": "kg",
                "min_quantity": 1.0,
                "unit_price": 175.0,
                "purchase_date": today - timedelta(days=12),
                "expiry_date": today + timedelta(days=180),
                "storage_location": "Pantry",
                "barcode": "8901030551017"
            },
            {
                "name": "Tata Sampann Moong Dal (Yellow)",
                "brand": "Tata Sampann",
                "category_id": 2,
                "quantity": 1.5,
                "unit": "kg",
                "min_quantity": 1.0,
                "unit_price": 140.0,
                "purchase_date": today - timedelta(days=12),
                "expiry_date": today + timedelta(days=180),
                "storage_location": "Pantry",
                "barcode": "8901030551024"
            },
            {
                "name": "Maggi 2-Minute Masala Noodles (Pack of 4)",
                "brand": "Nestle",
                "category_id": 6,
                "quantity": 4.0,
                "unit": "packets",
                "min_quantity": 2.0,
                "unit_price": 14.0,
                "purchase_date": today - timedelta(days=6),
                "expiry_date": today + timedelta(days=120),
                "storage_location": "Pantry",
                "barcode": "8901058852332"
            },
            {
                "name": "Red Label Natural Care Tea (500g)",
                "brand": "Brooke Bond",
                "category_id": 6,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.25,
                "unit_price": 280.0,
                "purchase_date": today - timedelta(days=15),
                "expiry_date": today + timedelta(days=270),
                "storage_location": "Pantry",
                "barcode": "8901525000018"
            },
            {
                "name": "Nescafe Classic Instant Coffee",
                "brand": "Nescafe",
                "category_id": 6,
                "quantity": 1.0,
                "unit": "bottles",
                "min_quantity": 0.25,
                "unit_price": 195.0,
                "purchase_date": today - timedelta(days=8),
                "expiry_date": today + timedelta(days=365),
                "storage_location": "Pantry",
                "barcode": "8901058841022"
            },
            {
                "name": "Everest Turmeric Powder (Haldi)",
                "brand": "Everest",
                "category_id": 5,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.25,
                "unit_price": 38.0,
                "purchase_date": today - timedelta(days=14),
                "expiry_date": today + timedelta(days=200),
                "storage_location": "Pantry",
                "barcode": "8901786101111"
            },
            {
                "name": "Everest Kashmiri Chilli Powder",
                "brand": "Everest",
                "category_id": 5,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.25,
                "unit_price": 65.0,
                "purchase_date": today - timedelta(days=14),
                "expiry_date": today + timedelta(days=200),
                "storage_location": "Pantry",
                "barcode": "8901786102222"
            },
            {
                "name": "Everest Garam Masala (100g)",
                "brand": "Everest",
                "category_id": 5,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.25,
                "unit_price": 78.0,
                "purchase_date": today - timedelta(days=14),
                "expiry_date": today + timedelta(days=200),
                "storage_location": "Pantry",
                "barcode": "8901786103333"
            },
            {
                "name": "Catch Jeera (Cumin Seeds 100g)",
                "brand": "Catch",
                "category_id": 5,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.25,
                "unit_price": 85.0,
                "purchase_date": today - timedelta(days=10),
                "expiry_date": today + timedelta(days=180),
                "storage_location": "Pantry",
                "barcode": "8901786104444"
            },
            {
                "name": "Amul Butter Pasteurised (500g)",
                "brand": "Amul",
                "category_id": 1,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.5,
                "unit_price": 275.0,
                "purchase_date": today - timedelta(days=4),
                "expiry_date": today + timedelta(days=60),
                "storage_location": "Refrigerator",
                "barcode": "8901262030039"
            },
            {
                "name": "Amul Processed Cheese Cubes (200g)",
                "brand": "Amul",
                "category_id": 1,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.5,
                "unit_price": 135.0,
                "purchase_date": today - timedelta(days=4),
                "expiry_date": today + timedelta(days=90),
                "storage_location": "Refrigerator",
                "barcode": "8901262040045"
            },
            {
                "name": "Fresh Red Onions (Kanda)",
                "brand": "Local Market",
                "category_id": 3,
                "quantity": 3.0,
                "unit": "kg",
                "min_quantity": 1.5,
                "unit_price": 35.0,
                "purchase_date": today - timedelta(days=3),
                "expiry_date": today + timedelta(days=14),
                "storage_location": "Pantry",
                "barcode": "8904000100052"
            },
            {
                "name": "Fresh Potatoes (Aloo)",
                "brand": "Local Market",
                "category_id": 3,
                "quantity": 4.0,
                "unit": "kg",
                "min_quantity": 2.0,
                "unit_price": 30.0,
                "purchase_date": today - timedelta(days=3),
                "expiry_date": today + timedelta(days=21),
                "storage_location": "Pantry",
                "barcode": "8904000100069"
            },
            {
                "name": "Shimla Green Capsicum",
                "brand": "Local Market",
                "category_id": 3,
                "quantity": 1.0,
                "unit": "kg",
                "min_quantity": 0.5,
                "unit_price": 60.0,
                "purchase_date": today - timedelta(days=2),
                "expiry_date": today + timedelta(days=8),
                "storage_location": "Refrigerator",
                "barcode": "8904000100076"
            },
            {
                "name": "Fresh Ginger & Garlic Paste",
                "brand": "Dabur Hommade",
                "category_id": 5,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.25,
                "unit_price": 45.0,
                "purchase_date": today - timedelta(days=5),
                "expiry_date": today + timedelta(days=90),
                "storage_location": "Refrigerator",
                "barcode": "8901207011018"
            },
            {
                "name": "Kissan Fresh Tomato Ketchup",
                "brand": "Kissan",
                "category_id": 4,
                "quantity": 1.0,
                "unit": "bottles",
                "min_quantity": 0.25,
                "unit_price": 120.0,
                "purchase_date": today - timedelta(days=10),
                "expiry_date": today + timedelta(days=180),
                "storage_location": "Refrigerator",
                "barcode": "8901030612015"
            },
            {
                "name": "Parle-G Gold Biscuits (1kg)",
                "brand": "Parle",
                "category_id": 6,
                "quantity": 2.0,
                "unit": "packets",
                "min_quantity": 1.0,
                "unit_price": 80.0,
                "purchase_date": today - timedelta(days=5),
                "expiry_date": today + timedelta(days=150),
                "storage_location": "Pantry",
                "barcode": "8901719101018"
            },
            {
                "name": "Kellogg's Corn Flakes Original",
                "brand": "Kellogg's",
                "category_id": 2,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.5,
                "unit_price": 185.0,
                "purchase_date": today - timedelta(days=7),
                "expiry_date": today + timedelta(days=180),
                "storage_location": "Pantry",
                "barcode": "8901499008012"
            },
            {
                "name": "Surf Excel Quick Wash Detergent",
                "brand": "Surf Excel",
                "category_id": 9,
                "quantity": 2.0,
                "unit": "kg",
                "min_quantity": 1.0,
                "unit_price": 140.0,
                "purchase_date": today - timedelta(days=12),
                "expiry_date": today + timedelta(days=720),
                "storage_location": "Pantry",
                "barcode": "8901030825316"
            },
            {
                "name": "Vim Dishwash Gel Lemon (750ml)",
                "brand": "Vim",
                "category_id": 9,
                "quantity": 1.0,
                "unit": "bottles",
                "min_quantity": 0.25,
                "unit_price": 155.0,
                "purchase_date": today - timedelta(days=12),
                "expiry_date": today + timedelta(days=500),
                "storage_location": "Pantry",
                "barcode": "8901030826016"
            },
            {
                "name": "Colgate Total Toothpaste (150g)",
                "brand": "Colgate",
                "category_id": 10,
                "quantity": 2.0,
                "unit": "pcs",
                "min_quantity": 1.0,
                "unit_price": 95.0,
                "purchase_date": today - timedelta(days=10),
                "expiry_date": today + timedelta(days=400),
                "storage_location": "Pantry",
                "barcode": "8901314010114"
            },
            {
                "name": "Dettol Original Bathing Soap (Pack of 3)",
                "brand": "Dettol",
                "category_id": 10,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.5,
                "unit_price": 130.0,
                "purchase_date": today - timedelta(days=10),
                "expiry_date": today + timedelta(days=500),
                "storage_location": "Pantry",
                "barcode": "8901396010112"
            },
            {
                "name": "Dabur Honey 100% Pure (500g)",
                "brand": "Dabur",
                "category_id": 4,
                "quantity": 1.0,
                "unit": "bottles",
                "min_quantity": 0.25,
                "unit_price": 210.0,
                "purchase_date": today - timedelta(days=15),
                "expiry_date": today + timedelta(days=365),
                "storage_location": "Pantry",
                "barcode": "8901207005017"
            },
            {
                "name": "MDH Chana Masala Spice Mix",
                "brand": "MDH",
                "category_id": 5,
                "quantity": 1.0,
                "unit": "packets",
                "min_quantity": 0.25,
                "unit_price": 75.0,
                "purchase_date": today - timedelta(days=14),
                "expiry_date": today + timedelta(days=220),
                "storage_location": "Pantry",
                "barcode": "8902167000014"
            }
        ]

        print(f"Adding {len(products_list)} items to inventory...")
        for p_data in products_list:
            prod = models.Product(
                user_id=demo_user.id,
                **p_data
            )
            db.add(prod)

        db.commit()
        print(f"Products seeded: exactly {len(products_list)} products for user '{demo_user.username}'.")

        # 4. Seed Expense Log to match Monthly Spending = ₹4,250
        # Current month expenses breakdown:
        first_day_of_month = date(today.year, today.month, 1)
        
        expenses_data = [
            {"product_name": "D-Mart Monthly Grocery Basket (Atta, Rice, Dal)", "category_id": 2, "amount": 1850.0, "days_ago": 12, "method": "UPI"},
            {"product_name": "Dairy & Breakfast Supply (Milk, Butter, Cheese)", "category_id": 1, "amount": 620.0, "days_ago": 8, "method": "UPI"},
            {"product_name": "Weekly Fresh Vegetables & Greens", "category_id": 3, "amount": 430.0, "days_ago": 6, "method": "Cash"},
            {"product_name": "Cooking Essentials (Sunflower Oil & Spices)", "category_id": 4, "amount": 550.0, "days_ago": 5, "method": "Card"},
            {"product_name": "Household Detergents & Dishwash Refill", "category_id": 9, "amount": 420.0, "days_ago": 3, "method": "UPI"},
            {"product_name": "Tea, Coffee & Tea-time Snacks", "category_id": 6, "amount": 380.0, "days_ago": 2, "method": "UPI"}
        ]
        # Sum = 1850 + 620 + 430 + 550 + 420 + 380 = ₹4,250! Exactly matching user prompt!

        for exp in expenses_data:
            exp_record = models.ExpenseLog(
                user_id=demo_user.id,
                product_name=exp["product_name"],
                category_id=exp["category_id"],
                amount=exp["amount"],
                expense_date=today - timedelta(days=exp["days_ago"]),
                payment_method=exp["method"],
                notes="Portfolio seed demo expense"
            )
            db.add(exp_record)

        # 5. Populate Shopping List with Low Stock Items
        low_stock_products = db.query(models.Product).filter(
            models.Product.user_id == demo_user.id,
            models.Product.quantity <= models.Product.min_quantity
        ).all()

        for lsp in low_stock_products:
            needed = max(round(lsp.min_quantity * 2 - lsp.quantity, 1), 1.0)
            shop_item = models.ShoppingItem(
                user_id=demo_user.id,
                product_id=lsp.id,
                product_name=lsp.name,
                category_id=lsp.category_id,
                target_quantity=needed,
                unit=lsp.unit,
                estimated_price=round(needed * lsp.unit_price, 2),
                is_purchased=False,
                auto_added=True
            )
            db.add(shop_item)

        db.commit()
        print("Expense records and Smart Shopping List seeded successfully.")
        print(f"Total Monthly Spending seeded: Rs.{sum(e['amount'] for e in expenses_data):,.2f}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Database seeding completed successfully! ✨")
