from datetime import date, timedelta
from app.services.expiry_service import enrich_product


class MockCategory:
    name = "Dairy & Eggs"
    icon = "🥛"


class MockProduct:
    def __init__(self, id, name, qty, min_qty, unit_price, exp_days_from_today):
        self.id = id
        self.user_id = 1
        self.category_id = 1
        self.category = MockCategory()
        self.name = name
        self.brand = "DemoBrand"
        self.quantity = qty
        self.unit = "L"
        self.min_quantity = min_qty
        self.unit_price = unit_price
        self.purchase_date = date.today() - timedelta(days=5)
        self.expiry_date = date.today() + timedelta(days=exp_days_from_today)
        self.barcode = "123456"
        self.storage_location = "Refrigerator"
        self.notes = "Test notes"
        self.created_at = None
        self.updated_at = None


def test_enrich_product_calculation():
    # Milk expiring tomorrow (1 day left)
    prod = MockProduct(1, "Amul Milk", 1.0, 2.0, 56.0, 1)
    enriched = enrich_product(prod, date.today())

    assert enriched["name"] == "Amul Milk"
    assert enriched["days_until_expiry"] == 1
    assert enriched["expiry_status"] == "critical"
    assert enriched["stock_status"] == "low_stock"
    assert enriched["total_value"] == 56.0
