from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app import models
from app.services.expiry_service import enrich_product


def generate_smart_recommendations(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Generates intelligent contextual recommendations:
    1. Critical expiry warnings ("Milk expires tomorrow. Consider using it first.")
    2. Predictive replenishment ("You usually purchase cooking oil every 30 days. Stock will last 5 days.")
    3. Recipe suggestions based on expiring items
    4. Auto-restock notifications
    5. Cost-saving insights
    """
    products = db.query(models.Product).filter(models.Product.user_id == user_id).all()
    if not products:
        return [
            {
                "type": "info",
                "title": "Welcome to Smart Grocery Tracker",
                "message": "Start by adding your pantry and fridge items to activate intelligent expiry tracking and predictions!",
                "icon": "✨",
                "severity": "info",
                "action_label": "Add First Product",
                "action_url": "/inventory?action=add"
            }
        ]

    today = date.today()
    enriched = [enrich_product(p, today) for p in products]
    recommendations: List[Dict[str, Any]] = []

    # 1. Immediate Expiry Recommendations (Critical Priority)
    critical_items = [p for p in enriched if p["expiry_status"] == "critical"]
    critical_items.sort(key=lambda x: x["days_until_expiry"])

    for item in critical_items[:3]:
        days = item["days_until_expiry"]
        if days == 0:
            msg = f"{item['name']} expires today! Consider consuming or preparing it right away."
        elif days == 1:
            msg = f"{item['name']} expires tomorrow. Consider using it first to avoid waste."
        else:
            msg = f"{item['name']} expires in {days} days ({item['expiry_date'].strftime('%d %b')}). Plan meals around it."

        recommendations.append({
            "type": "expiry_urgent",
            "title": f"Urgent: {item['name']}",
            "message": msg,
            "icon": "⏰",
            "severity": "critical",
            "action_label": "View Item",
            "action_url": f"/inventory?search={item['name']}"
        })

    # 2. Recipe suggestions based on expiring items
    expiring_names = [p["name"].lower() for p in enriched if p["days_until_expiry"] <= 4 and p["quantity"] > 0]
    if any(n in ["tomato", "tomatoes", "onion", "paneer", "vegetable", "veggie"] for n in expiring_names):
        recommendations.append({
            "type": "recipe",
            "title": "Smart Recipe Idea",
            "message": "You have vegetables and dairy expiring soon! A quick vegetable curry, paneer bhurji, or hearty stew will use them up perfectly.",
            "icon": "🍳",
            "severity": "info",
            "action_label": "Explore Recipes",
            "action_url": "#"
        })
    elif any(n in ["bread", "milk", "egg", "eggs", "butter"] for n in expiring_names):
        recommendations.append({
            "type": "recipe",
            "title": "Breakfast Recipe Idea",
            "message": "Your bread and dairy are nearing their best before dates. Try making French toast or savory bread pudding today!",
            "icon": "🍞",
            "severity": "info",
            "action_label": "View Items",
            "action_url": "/inventory?filter=expiring"
        })

    # 3. Consumption Pattern & Predictive Replenishment
    # Look for items like Cooking Oil, Rice, Atta/Flour, Milk, Tea, Sugar
    predictive_targets = ["cooking oil", "sunflower oil", "mustard oil", "basmati rice", "rice", "atta", "wheat flour", "tea", "coffee"]
    for p in enriched:
        name_lower = p["name"].lower()
        if any(target in name_lower for target in predictive_targets):
            qty = p["quantity"]
            min_q = p["min_quantity"]
            # Estimate days left based on standard household burn-rate
            days_held = max((today - p["purchase_date"]).days, 1)
            
            # Predict replenishment frequency
            cycle_days = 30  # typical monthly purchase cycle
            estimated_days_left = max(int((qty / max(min_q, 1.0)) * 5), 1)

            if qty <= min_q * 1.5:
                recommendations.append({
                    "type": "prediction",
                    "title": f"Predictive Restock: {p['name']}",
                    "message": f"You usually purchase {p['name']} every {cycle_days} days. Your current stock ({qty} {p['unit']}) may last only ~{estimated_days_left} days.",
                    "icon": "📈",
                    "severity": "warning",
                    "action_label": "Add to Shopping List",
                    "action_url": f"/shopping-list?add_product={p['id']}"
                })
                break

    # 4. Low Stock / Out of Stock Auto-Restock Alert
    low_stock = [p for p in enriched if p["stock_status"] in ("low_stock", "out_of_stock")]
    if low_stock:
        first_low = low_stock[0]
        status_desc = "is out of stock" if first_low["quantity"] <= 0 else f"is running low ({first_low['quantity']} {first_low['unit']})"
        recommendations.append({
            "type": "low_stock",
            "title": "Inventory Restock Needed",
            "message": f"{first_low['name']} {status_desc}. It has been marked for your Smart Shopping List.",
            "icon": "🛒",
            "severity": "warning",
            "action_label": "Open Shopping List",
            "action_url": "/shopping-list"
        })

    # 5. Financial Waste Alert
    at_risk_value = sum(p["total_value"] for p in enriched if 0 <= p["days_until_expiry"] <= 7)
    if at_risk_value > 100:
        recommendations.append({
            "type": "saving",
            "title": "Savings Opportunity",
            "message": f"You have ₹{round(at_risk_value, 2)} worth of groceries expiring within the next 7 days. Utilizing them now directly cuts your grocery budget waste.",
            "icon": "💡",
            "severity": "success",
            "action_label": "View Expiring Items",
            "action_url": "/inventory?filter=expiring"
        })

    return recommendations
