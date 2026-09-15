from datetime import date, timedelta
from app.services.expiry_service import classify_expiry, classify_stock


def test_expiry_classification_expired():
    today = date.today()
    past_date = today - timedelta(days=2)
    status, badge = classify_expiry(past_date, today)
    assert status == "expired"
    assert "❌" in badge


def test_expiry_classification_critical():
    today = date.today()
    # 0 days (today)
    status0, badge0 = classify_expiry(today, today)
    assert status0 == "critical"
    assert "🔴" in badge0

    # 1 day
    status1, badge1 = classify_expiry(today + timedelta(days=1), today)
    assert status1 == "critical"
    assert "🔴" in badge1

    # 3 days
    status3, badge3 = classify_expiry(today + timedelta(days=3), today)
    assert status3 == "critical"
    assert "🔴" in badge3


def test_expiry_classification_warning():
    today = date.today()
    # 4 days
    status4, badge4 = classify_expiry(today + timedelta(days=4), today)
    assert status4 == "warning"
    assert "🟠" in badge4

    # 7 days
    status7, badge7 = classify_expiry(today + timedelta(days=7), today)
    assert status7 == "warning"
    assert "🟠" in badge7


def test_expiry_classification_fresh():
    today = date.today()
    # 8 days or more
    status8, badge8 = classify_expiry(today + timedelta(days=8), today)
    assert status8 == "fresh"
    assert "✅" in badge8


def test_stock_classification():
    # Out of Stock (quantity <= 0)
    st_out, badge_out = classify_stock(0.0, 2.0)
    assert st_out == "out_of_stock"
    assert "❌" in badge_out

    # Low Stock (quantity <= min_quantity)
    st_low, badge_low = classify_stock(1.0, 2.0)
    assert st_low == "low_stock"
    assert "⚠️" in badge_low

    # Available (quantity > min_quantity)
    st_avail, badge_avail = classify_stock(4.0, 2.0)
    assert st_avail == "available"
    assert "✅" in badge_avail
