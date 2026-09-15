import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.services.analytics import get_dashboard_metrics
from app.services.recommender import generate_smart_recommendations
from app import models


def test_portfolio_dashboard_metrics():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "user").first()
        assert user is not None, "Demo user 'user' must exist"

        metrics = get_dashboard_metrics(db, user.id)
        
        # Verify exact target metrics from user request
        assert metrics["total_products"] == 35, f"Expected 35, got {metrics['total_products']}"
        assert metrics["expiring_soon"] == 4, f"Expected 4, got {metrics['expiring_soon']}"
        assert metrics["expired"] == 2, f"Expected 2, got {metrics['expired']}"
        assert metrics["low_stock"] == 5, f"Expected 5, got {metrics['low_stock']}"
        assert metrics["monthly_spending"] == 4250.0, f"Expected 4250.0, got {metrics['monthly_spending']}"

        # Verify recommendations
        recs = generate_smart_recommendations(db, user.id)
        assert len(recs) > 0, "Recommendations should be generated"
        
        # Check that urgent expiry and predictive replenish exist
        rec_types = [r["type"] for r in recs]
        assert "expiry_urgent" in rec_types
        assert "prediction" in rec_types

        print("\nAll Portfolio Target Metrics Verified Successfully:")
        print(f"  • Total Products:   {metrics['total_products']}")
        print(f"  • Expiring Soon:    {metrics['expiring_soon']}")
        print(f"  • Expired:          {metrics['expired']}")
        print(f"  • Low Stock:        {metrics['low_stock']}")
        print(f"  • Monthly Spending: Rs.{metrics['monthly_spending']:,.2f}")
        print(f"  • Generated {len(recs)} Smart Recommendations")
    finally:
        db.close()


if __name__ == "__main__":
    test_portfolio_dashboard_metrics()
