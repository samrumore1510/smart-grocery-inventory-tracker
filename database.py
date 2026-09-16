import os
from pymongo import MongoClient

# MongoDB Connection Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "smart_grocery")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collections
users_col = db["users"]
categories_col = db["categories"]
products_col = db["products"]
shopping_col = db["shopping_items"]
expenses_col = db["expense_logs"]


def serialize_doc(doc):
    """Convert MongoDB document to a clean Python dictionary with string id."""
    if not doc:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def init_db():
    """Ensure essential indexes for speed and uniqueness."""
    users_col.create_index("username", unique=True)
    users_col.create_index("email", unique=True)
    products_col.create_index([("user_id", 1), ("expiry_date", 1)])
    shopping_col.create_index([("user_id", 1), ("is_purchased", 1)])
    expenses_col.create_index([("user_id", 1), ("expense_date", 1)])
