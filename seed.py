import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import sys
from datetime import date, timedelta
from bson import ObjectId
import bcrypt
from database import db, users_col, categories_col, products_col, shopping_col, expenses_col, init_db

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")



def seed():
    print("Connecting to MongoDB and initializing indexes...")
    init_db()

    # 1. Seed Categories
    categories_col.delete_many({})
    categories = [
        {"id": 1, "name": "Dairy & Eggs", "icon": "🥛"},
        {"id": 2, "name": "Grains & Pulses", "icon": "🌾"},
        {"id": 3, "name": "Vegetables & Fruits", "icon": "🥦"},
        {"id": 4, "name": "Oils & Ghee", "icon": "🛢️"},
        {"id": 5, "name": "Spices & Seasoning", "icon": "🧂"},
        {"id": 6, "name": "Snacks & Beverages", "icon": "🍪"},
        {"id": 7, "name": "Meat & Seafood", "icon": "🍗"},
        {"id": 8, "name": "Bakery & Breads", "icon": "🍞"},
        {"id": 9, "name": "Household & Cleaning", "icon": "🧼"},
        {"id": 10, "name": "Personal Care", "icon": "🧴"}
    ]
    categories_col.insert_many(categories)
    print("Categories seeded: 10 categories.")

    # 2. Seed Users
    users_col.delete_many({})
    user_id = str(ObjectId())
    admin_id = str(ObjectId())

    users_col.insert_one({
        "_id": ObjectId(admin_id),
        "username": "admin",
        "email": "admin@smartgrocery.com",
        "full_name": "Portfolio Admin",
        "hashed_password": hash_password("admin123"),
        "role": "admin"
    })

    users_col.insert_one({
        "_id": ObjectId(user_id),
        "username": "user",
        "email": "user@smartgrocery.com",
        "full_name": "Samruddhi (MCA)",
        "hashed_password": hash_password("user123"),
        "role": "user"
    })
    print("Users created: admin / admin123 and user / user123")

    # 3. Seed Products (Exact 35 Items)
    products_col.delete_many({"user_id": user_id})
    expenses_col.delete_many({"user_id": user_id})
    shopping_col.delete_many({"user_id": user_id})

    today = date.today()

    products = [
        # --- 2 EXPIRED ITEMS ---
        {"name": "Britannia Brown Bread", "brand": "Britannia", "category_id": 8, "category_name": "Bakery & Breads", "quantity": 1.0, "unit": "packets", "min_quantity": 1.0, "unit_price": 50.0, "purchase_date": str(today - timedelta(days=7)), "expiry_date": str(today - timedelta(days=2)), "storage_location": "Kitchen Counter"},
        {"name": "Epigamia Greek Yogurt (Blueberry)", "brand": "Epigamia", "category_id": 1, "category_name": "Dairy & Eggs", "quantity": 2.0, "unit": "pcs", "min_quantity": 1.0, "unit_price": 60.0, "purchase_date": str(today - timedelta(days=10)), "expiry_date": str(today - timedelta(days=1)), "storage_location": "Refrigerator"},

        # --- 4 EXPIRING SOON ITEMS (1-7 Days) ---
        {"name": "Amul Taaza Toned Milk (1L)", "brand": "Amul", "category_id": 1, "category_name": "Dairy & Eggs", "quantity": 1.0, "unit": "L", "min_quantity": 2.0, "unit_price": 56.0, "purchase_date": str(today - timedelta(days=2)), "expiry_date": str(today + timedelta(days=1)), "storage_location": "Refrigerator"},
        {"name": "Fresh Organic Spinach (Palak)", "brand": "Fresh Farms", "category_id": 3, "category_name": "Vegetables & Fruits", "quantity": 2.0, "unit": "packets", "min_quantity": 1.0, "unit_price": 30.0, "purchase_date": str(today - timedelta(days=1)), "expiry_date": str(today + timedelta(days=2)), "storage_location": "Refrigerator"},
        {"name": "Hybrid Red Tomatoes", "brand": "Local Market", "category_id": 3, "category_name": "Vegetables & Fruits", "quantity": 1.5, "unit": "kg", "min_quantity": 1.0, "unit_price": 40.0, "purchase_date": str(today - timedelta(days=2)), "expiry_date": str(today + timedelta(days=3)), "storage_location": "Kitchen Counter"},
        {"name": "Amul Fresh Malai Paneer (200g)", "brand": "Amul", "category_id": 1, "category_name": "Dairy & Eggs", "quantity": 2.0, "unit": "packets", "min_quantity": 1.0, "unit_price": 90.0, "purchase_date": str(today - timedelta(days=3)), "expiry_date": str(today + timedelta(days=5)), "storage_location": "Refrigerator"},

        # --- 29 FRESH ITEMS (> 7 Days) including 3 Low Stock ---
        {"name": "Daawat Rozana Super Basmati Rice", "brand": "Daawat", "category_id": 2, "category_name": "Grains & Pulses", "quantity": 1.0, "unit": "kg", "min_quantity": 2.0, "unit_price": 95.0, "purchase_date": str(today - timedelta(days=15)), "expiry_date": str(today + timedelta(days=240)), "storage_location": "Pantry"},
        {"name": "Fortune Sunlite Refined Sunflower Oil", "brand": "Fortune", "category_id": 4, "category_name": "Oils & Ghee", "quantity": 0.0, "unit": "L", "min_quantity": 2.0, "unit_price": 165.0, "purchase_date": str(today - timedelta(days=28)), "expiry_date": str(today + timedelta(days=180)), "storage_location": "Pantry"},
        {"name": "Madhur Pure & Hygienic Sugar", "brand": "Madhur", "category_id": 2, "category_name": "Grains & Pulses", "quantity": 0.5, "unit": "kg", "min_quantity": 1.0, "unit_price": 48.0, "purchase_date": str(today - timedelta(days=20)), "expiry_date": str(today + timedelta(days=300)), "storage_location": "Pantry"},

        # Remaining 26 items
        {"name": "Aashirvaad Shudh Chakki Atta (5kg)", "brand": "Aashirvaad", "category_id": 2, "category_name": "Grains & Pulses", "quantity": 5.0, "unit": "kg", "min_quantity": 2.0, "unit_price": 55.0, "purchase_date": str(today - timedelta(days=5)), "expiry_date": str(today + timedelta(days=85)), "storage_location": "Pantry"},
        {"name": "Tata Salt Vacuum Evaporated", "brand": "Tata", "category_id": 5, "category_name": "Spices & Seasoning", "quantity": 2.0, "unit": "kg", "min_quantity": 1.0, "unit_price": 28.0, "purchase_date": str(today - timedelta(days=10)), "expiry_date": str(today + timedelta(days=365)), "storage_location": "Pantry"},
        {"name": "Tata Sampann Toor Dal", "brand": "Tata Sampann", "category_id": 2, "category_name": "Grains & Pulses", "quantity": 2.0, "unit": "kg", "min_quantity": 1.0, "unit_price": 175.0, "purchase_date": str(today - timedelta(days=12)), "expiry_date": str(today + timedelta(days=180)), "storage_location": "Pantry"},
        {"name": "Tata Sampann Moong Dal", "brand": "Tata Sampann", "category_id": 2, "category_name": "Grains & Pulses", "quantity": 1.5, "unit": "kg", "min_quantity": 1.0, "unit_price": 140.0, "purchase_date": str(today - timedelta(days=12)), "expiry_date": str(today + timedelta(days=180)), "storage_location": "Pantry"},
        {"name": "Maggi 2-Minute Masala Noodles", "brand": "Nestle", "category_id": 6, "category_name": "Snacks & Beverages", "quantity": 4.0, "unit": "packets", "min_quantity": 2.0, "unit_price": 14.0, "purchase_date": str(today - timedelta(days=6)), "expiry_date": str(today + timedelta(days=120)), "storage_location": "Pantry"},
        {"name": "Red Label Natural Care Tea (500g)", "brand": "Brooke Bond", "category_id": 6, "category_name": "Snacks & Beverages", "quantity": 1.0, "unit": "packets", "min_quantity": 0.25, "unit_price": 280.0, "purchase_date": str(today - timedelta(days=15)), "expiry_date": str(today + timedelta(days=270)), "storage_location": "Pantry"},
        {"name": "Nescafe Classic Instant Coffee", "brand": "Nescafe", "category_id": 6, "category_name": "Snacks & Beverages", "quantity": 1.0, "unit": "bottles", "min_quantity": 0.25, "unit_price": 195.0, "purchase_date": str(today - timedelta(days=8)), "expiry_date": str(today + timedelta(days=365)), "storage_location": "Pantry"},
        {"name": "Everest Turmeric Powder", "brand": "Everest", "category_id": 5, "category_name": "Spices & Seasoning", "quantity": 1.0, "unit": "packets", "min_quantity": 0.25, "unit_price": 38.0, "purchase_date": str(today - timedelta(days=14)), "expiry_date": str(today + timedelta(days=200)), "storage_location": "Pantry"},
        {"name": "Everest Kashmiri Chilli Powder", "brand": "Everest", "category_id": 5, "category_name": "Spices & Seasoning", "quantity": 1.0, "unit": "packets", "min_quantity": 0.25, "unit_price": 65.0, "purchase_date": str(today - timedelta(days=14)), "expiry_date": str(today + timedelta(days=200)), "storage_location": "Pantry"},
        {"name": "Everest Garam Masala", "brand": "Everest", "category_id": 5, "category_name": "Spices & Seasoning", "quantity": 1.0, "unit": "packets", "min_quantity": 0.25, "unit_price": 78.0, "purchase_date": str(today - timedelta(days=14)), "expiry_date": str(today + timedelta(days=200)), "storage_location": "Pantry"},
        {"name": "Catch Jeera (Cumin Seeds)", "brand": "Catch", "category_id": 5, "category_name": "Spices & Seasoning", "quantity": 1.0, "unit": "packets", "min_quantity": 0.25, "unit_price": 85.0, "purchase_date": str(today - timedelta(days=10)), "expiry_date": str(today + timedelta(days=180)), "storage_location": "Pantry"},
        {"name": "Amul Butter Pasteurised", "brand": "Amul", "category_id": 1, "category_name": "Dairy & Eggs", "quantity": 1.0, "unit": "packets", "min_quantity": 0.5, "unit_price": 275.0, "purchase_date": str(today - timedelta(days=4)), "expiry_date": str(today + timedelta(days=60)), "storage_location": "Refrigerator"},
        {"name": "Amul Processed Cheese Cubes", "brand": "Amul", "category_id": 1, "category_name": "Dairy & Eggs", "quantity": 1.0, "unit": "packets", "min_quantity": 0.5, "unit_price": 135.0, "purchase_date": str(today - timedelta(days=4)), "expiry_date": str(today + timedelta(days=90)), "storage_location": "Refrigerator"},
        {"name": "Fresh Red Onions (Kanda)", "brand": "Local Market", "category_id": 3, "category_name": "Vegetables & Fruits", "quantity": 3.0, "unit": "kg", "min_quantity": 1.5, "unit_price": 35.0, "purchase_date": str(today - timedelta(days=3)), "expiry_date": str(today + timedelta(days=14)), "storage_location": "Pantry"},
        {"name": "Fresh Potatoes (Aloo)", "brand": "Local Market", "category_id": 3, "category_name": "Vegetables & Fruits", "quantity": 4.0, "unit": "kg", "min_quantity": 2.0, "unit_price": 30.0, "purchase_date": str(today - timedelta(days=3)), "expiry_date": str(today + timedelta(days=21)), "storage_location": "Pantry"},
        {"name": "Shimla Green Capsicum", "brand": "Local Market", "category_id": 3, "category_name": "Vegetables & Fruits", "quantity": 1.0, "unit": "kg", "min_quantity": 0.5, "unit_price": 60.0, "purchase_date": str(today - timedelta(days=2)), "expiry_date": str(today + timedelta(days=8)), "storage_location": "Refrigerator"},
        {"name": "Fresh Ginger & Garlic Paste", "brand": "Dabur", "category_id": 5, "category_name": "Spices & Seasoning", "quantity": 1.0, "unit": "packets", "min_quantity": 0.25, "unit_price": 45.0, "purchase_date": str(today - timedelta(days=5)), "expiry_date": str(today + timedelta(days=90)), "storage_location": "Refrigerator"},
        {"name": "Kissan Fresh Tomato Ketchup", "brand": "Kissan", "category_id": 4, "category_name": "Oils & Ghee", "quantity": 1.0, "unit": "bottles", "min_quantity": 0.25, "unit_price": 120.0, "purchase_date": str(today - timedelta(days=10)), "expiry_date": str(today + timedelta(days=180)), "storage_location": "Refrigerator"},
        {"name": "Parle-G Gold Biscuits", "brand": "Parle", "category_id": 6, "category_name": "Snacks & Beverages", "quantity": 2.0, "unit": "packets", "min_quantity": 1.0, "unit_price": 80.0, "purchase_date": str(today - timedelta(days=5)), "expiry_date": str(today + timedelta(days=150)), "storage_location": "Pantry"},
        {"name": "Kellogg's Corn Flakes Original", "brand": "Kellogg's", "category_id": 2, "category_name": "Grains & Pulses", "quantity": 1.0, "unit": "packets", "min_quantity": 0.5, "unit_price": 185.0, "purchase_date": str(today - timedelta(days=7)), "expiry_date": str(today + timedelta(days=180)), "storage_location": "Pantry"},
        {"name": "Surf Excel Quick Wash Detergent", "brand": "Surf Excel", "category_id": 9, "category_name": "Household & Cleaning", "quantity": 2.0, "unit": "kg", "min_quantity": 1.0, "unit_price": 140.0, "purchase_date": str(today - timedelta(days=12)), "expiry_date": str(today + timedelta(days=720)), "storage_location": "Pantry"},
        {"name": "Vim Dishwash Gel Lemon", "brand": "Vim", "category_id": 9, "category_name": "Household & Cleaning", "quantity": 1.0, "unit": "bottles", "min_quantity": 0.25, "unit_price": 155.0, "purchase_date": str(today - timedelta(days=12)), "expiry_date": str(today + timedelta(days=500)), "storage_location": "Pantry"},
        {"name": "Colgate Total Toothpaste", "brand": "Colgate", "category_id": 10, "category_name": "Personal Care", "quantity": 2.0, "unit": "pcs", "min_quantity": 1.0, "unit_price": 95.0, "purchase_date": str(today - timedelta(days=10)), "expiry_date": str(today + timedelta(days=400)), "storage_location": "Pantry"},
        {"name": "Dettol Original Bathing Soap", "brand": "Dettol", "category_id": 10, "category_name": "Personal Care", "quantity": 1.0, "unit": "packets", "min_quantity": 0.5, "unit_price": 130.0, "purchase_date": str(today - timedelta(days=10)), "expiry_date": str(today + timedelta(days=500)), "storage_location": "Pantry"},
        {"name": "Dabur Honey 100% Pure", "brand": "Dabur", "category_id": 4, "category_name": "Oils & Ghee", "quantity": 1.0, "unit": "bottles", "min_quantity": 0.25, "unit_price": 210.0, "purchase_date": str(today - timedelta(days=15)), "expiry_date": str(today + timedelta(days=365)), "storage_location": "Pantry"},
        {"name": "MDH Chana Masala Spice Mix", "brand": "MDH", "category_id": 5, "category_name": "Spices & Seasoning", "quantity": 1.0, "unit": "packets", "min_quantity": 0.25, "unit_price": 75.0, "purchase_date": str(today - timedelta(days=14)), "expiry_date": str(today + timedelta(days=220)), "storage_location": "Pantry"}
    ]

    for p in products:
        p["user_id"] = user_id
        products_col.insert_one(p)

    print(f"Products seeded in MongoDB: exactly {len(products)} products.")

    # 4. Seed Expenses (Sum = Rs. 4,250)
    expenses = [
        {"product_name": "D-Mart Monthly Grocery Basket", "category_name": "Grains & Pulses", "amount": 1850.0, "days_ago": 12, "payment_method": "UPI"},
        {"product_name": "Dairy & Breakfast Supply", "category_name": "Dairy & Eggs", "amount": 620.0, "days_ago": 8, "payment_method": "UPI"},
        {"product_name": "Weekly Fresh Vegetables", "category_name": "Vegetables & Fruits", "amount": 430.0, "days_ago": 6, "payment_method": "Cash"},
        {"product_name": "Cooking Oil & Spices", "category_name": "Oils & Ghee", "amount": 550.0, "days_ago": 5, "payment_method": "Card"},
        {"product_name": "Household Detergents", "category_name": "Household & Cleaning", "amount": 420.0, "days_ago": 3, "payment_method": "UPI"},
        {"product_name": "Tea, Coffee & Snacks", "category_name": "Snacks & Beverages", "amount": 380.0, "days_ago": 2, "payment_method": "UPI"}
    ]
    for exp in expenses:
        exp["user_id"] = user_id
        exp["expense_date"] = str(today - timedelta(days=exp.pop("days_ago")))
        expenses_col.insert_one(exp)

    # 5. Populate Shopping List with Low Stock Items
    lows = list(products_col.find({"user_id": user_id, "$expr": {"$lte": ["$quantity", "$min_quantity"]}}))
    for l in lows:
        needed = max(round(l["min_quantity"] * 2 - l["quantity"], 1), 1.0)
        shopping_col.insert_one({
            "user_id": user_id,
            "product_id": str(l["_id"]),
            "product_name": l["name"],
            "category_name": l.get("category_name", "General"),
            "target_quantity": needed,
            "unit": l["unit"],
            "estimated_price": round(needed * l["unit_price"], 2),
            "is_purchased": False,
            "auto_added": True
        })

    print(f"Expenses seeded: Rs.{sum(e['amount'] for e in expenses):,.2f}")
    print(f"Shopping list seeded with {len(lows)} low-stock items.")
    print("MongoDB Seeding complete! Done.")


if __name__ == "__main__":
    seed()

