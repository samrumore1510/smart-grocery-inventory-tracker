import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from main import app
from database import users_col, products_col, expenses_col, shopping_col, categories_col
from services import classify_expiry, classify_stock, get_dashboard_metrics

client = TestClient(app)

def test_expiry_classification():
    today = date.today()
    assert classify_expiry(today - timedelta(days=2), today)[0] == "expired"
    assert classify_expiry(today, today)[0] == "critical"
    assert classify_expiry(today + timedelta(days=2), today)[0] == "critical"
    assert classify_expiry(today + timedelta(days=5), today)[0] == "warning"
    assert classify_expiry(today + timedelta(days=20), today)[0] == "fresh"

def test_stock_classification():
    assert classify_stock(0, 1)[0] == "out_of_stock"
    assert classify_stock(1, 1)[0] == "low_stock"
    assert classify_stock(5, 2)[0] == "available"

def test_seeded_metrics_against_mongodb():
    user = users_col.find_one({"username": "user"})
    assert user is not None
    uid = str(user["_id"])
    metrics = get_dashboard_metrics(uid)
    assert metrics["total_products"] == 35
    assert metrics["expiring_soon"] == 4
    assert metrics["expired"] == 2
    assert metrics["low_stock"] == 5
    assert metrics["monthly_spending"] == 4250.0

def test_api_auth_login():
    res = client.post("/api/auth/login", json={"username": "user", "password": "user123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "user"

def test_api_dashboard_endpoint():
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert data["kpis"]["total_products"] == 35
    assert data["kpis"]["expiring_soon"] == 4
    assert data["kpis"]["expired"] == 2
    assert data["kpis"]["low_stock"] == 5
    assert data["kpis"]["monthly_spending"] == 4250.0
    assert len(data["recommendations"]) > 0

def test_api_inventory_endpoint():
    res = client.get("/api/inventory")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 35
    assert "expiry_status" in items[0]
    assert "stock_status" in items[0]

def test_api_shopping_endpoint():
    res = client.get("/api/shopping")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 5

def test_api_expenses_endpoint():
    res = client.get("/api/expenses")
    assert res.status_code == 200
    data = res.json()
    assert "expenses" in data
    assert "analysis" in data
    assert data["analysis"]["total_expenses_all_time"] == 4250.0

def test_api_reports():
    res_pdf = client.get("/api/reports/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"

    res_excel = client.get("/api/reports/excel")
    assert res_excel.status_code == 200
    assert "openxmlformats" in res_excel.headers["content-type"]
