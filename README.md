# 🛒 Smart Grocery Inventory & Expiry Tracker

> **A 90%+ Python Full-Stack Web Application for intelligent grocery inventory management, real-time expiry date classification, low-stock alerts, automated shopping lists, expense analytics, and predictive replenishment.**
> 
> *Designed specifically as a flagship project for an MCA (Master of Computer Applications) Portfolio.*

---

## 🎯 1. Real-World Problem & Motivation

Households and small retail shops consistently face significant inefficiencies:
1. **Unnoticed Product Expiry**: Perishables (dairy, greens, breads) expire silently in refrigerators and pantries, causing financial waste and food hazards.
2. **Duplicate Purchases**: Consumers buy items they already have because they lack an updated inventory in hand.
3. **Unexpected Stockouts**: Essential staples (cooking oil, rice, salt, milk) run out without warning.
4. **Lack of Expense Visibility**: Spending patterns and grocery budgets are rarely tracked systematically.

---

## 💡 2. Proposed Solution

**Smart Grocery Tracker** provides an automated, centralized platform built with Python and modern web standards:
- **Intelligent Expiry Classification**: Dynamic categorization into Expired ❌, Critical (1-3 Days) 🔴, Warning (4-7 Days) 🟠, and Fresh ✅.
- **Stock Buffer Monitoring**: Alerts when products reach minimum threshold or go out of stock.
- **Auto-Sync Smart Shopping List**: Automatically queues low-stock items; restocks inventory upon purchase in one click.
- **Data Analytics Engine (Pandas)**: Computes daily spending trends, monthly totals, category breakdowns, and financial wastage audits.
- **Smart Predictive Recommendations**: Context-aware meal suggestions and replenishment predictions based on burn-rate cycles (*"You usually purchase cooking oil every 30 days. Your current stock may last only 5 days."*).
- **Camera Barcode Scanner**: Scan barcodes using webcams or mobile phones with instant recognition and printable label generator.
- **Audit Reports**: One-click professional PDF audit report (ReportLab) and Excel export (OpenPyXL).

---

## 🏗️ 3. Architecture & 90% Python Implementation

The project is architected so that **over 90% of all executable logic is pure Python**:

```
                       ┌───────────────────────────────┐
                       │     Browser / Mobile Device   │
                       │   (HTML5, CSS3, Camera Barcode)│
                       └──────────────┬────────────────┘
                                      │ HTTP / JSON / Jinja2
                                      ▼
                       ┌───────────────────────────────┐
                       │      FastAPI Web Server       │
                       │     (Python 3.11 Backend)     │
                       └──────┬──────────────┬─────────┘
                              │              │
         ┌────────────────────┴──┐      ┌───┴────────────────────┐
         │ Core Business Modules │      │   Data & Analytics     │
         ├───────────────────────┤      ├────────────────────────┤
         │ • Auth & User Roles   │      │ • Pandas Engine        │
         │ • Inventory CRUD      │      │ • Expiry Classifier    │
         │ • Barcode Generator   │      │ • Smart Recommender    │
         │ • PDF Exporter        │      │ • Demand Predictor     │
         └───────────┬───────────┘      └───┬────────────────────┘
                     │                      │
                     └──────────┬───────────┘
                                ▼
                       ┌─────────────────┐
                       │ SQLAlchemy ORM  │
                       └────────┬────────┘
                                │
                   ┌────────────┴────────────┐
                   ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐
          │ SQLite (Default)│       │  MySQL (Prod)   │
          │ Zero-config dev │       │  schema.sql     │
          └─────────────────┘       └─────────────────┘
```

### Component Breakdown
| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Backend & APIs** | **Python 3.11 + FastAPI** | High-performance asynchronous REST API and Jinja2 template rendering |
| **Database ORM** | **SQLAlchemy 2.0 + PyMySQL** | Dual support for SQLite (development/offline viva) and MySQL (production) |
| **Data Analysis** | **Pandas** | Time-series grocery expense aggregations, burn rate, and wastage calculations |
| **Security & Auth** | **Passlib (Bcrypt) + PyJWT** | Role-based authentication (Admin / User) with JWT cookies and headers |
| **Reporting & Barcode** | **ReportLab + Python-Barcode** | PDF generation and Code128/EAN13 barcode generation |
| **Frontend** | **HTML5 + Vanilla CSS + Chart.js** | Glassmorphic, responsive interface with dark/light mode and camera scanner |

---

## 🚀 4. Quickstart Guide

### Prerequisites
- Python 3.10+ installed
- Pip package manager

### Step 1: Clone or Navigate to Project
```bash
cd C:\Users\Samruddhi\.gemini\antigravity-ide\scratch\smart_grocery_tracker
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python run.py
```
> **Note**: On first launch, `run.py` automatically initializes the database schema and seeds **35 realistic demo items** matching all portfolio specifications!

### Step 4: Open in Browser
- **Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔑 5. Pre-Configured Demo Credentials

Use these credentials to log in and present the application:
| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Household User** | `user` | `user123` | Demonstrates the 35 preloaded items, alerts, smart shopping list, and charts |
| **Store Admin** | `admin` | `admin123` | Demonstrates administrator privileges and inventory oversight |

*(Quick one-click login buttons are also built directly into the login screen!)*

---

## 📊 6. Seeded Portfolio Metrics

When logging in as `user`, the dashboard displays:
- **Total Products**: `35`
- **Expiring Soon**: `4` (Amul Milk, Spinach, Tomatoes, Paneer)
- **Expired**: `2` (Brown Bread, Greek Yogurt)
- **Low Stock**: `5` (Rice 1kg, Cooking Oil 0L, Sugar 0.5kg, Milk 1L, Bread 1pk)
- **Monthly Spending**: `₹4,250.00`
- **Smart Recommendations**: Dynamic banners for critical expiry, recipe suggestions, and replenishment forecasting.

---

## 🗄️ 7. Switching to MySQL Database

By default, the application runs on **SQLite** (`smart_grocery.db`) so that you can run it anywhere without requiring a running MySQL server.

To switch to **MySQL**:
1. Ensure MySQL server is running (e.g. via XAMPP, WampServer, or MySQL Server).
2. Create the database:
   ```sql
   CREATE DATABASE smart_grocery;
   ```
3. Set the `DATABASE_URL` environment variable (or edit `.env`):
   ```bash
   DATABASE_URL="mysql+pymysql://root:password@localhost:3306/smart_grocery"
   ```
4. Re-run `python run.py` (or import `scripts/schema.sql` directly into MySQL Workbench / phpMyAdmin).

---

## 🧪 8. Running Automated Tests

Run the comprehensive pytest suite:
```bash
python -m pytest tests/ -v
```

Tests cover:
- Password hashing security & JWT token decode
- Expiry date status classifications (Expired, 1-3d Critical, 4-7d Warning, Fresh)
- Low stock & Out of Stock boundary conditions
- Recommendation engine data enrichment

---

## 🎓 9. MCA Viva / Project Defense Q&A

### Q1: Why did you choose FastAPI over Django or Flask?
> **Answer**: FastAPI provides modern asynchronous performance (ASGI), automatic interactive OpenAPI (Swagger) documentation, and native Pydantic type validation, making the codebase cleaner, faster, and enterprise-ready while keeping it lightweight.

### Q2: How does the Smart Recommendation algorithm work?
> **Answer**: The recommendation service (`app/services/recommender.py`) executes multi-tier heuristic and predictive rules:
> 1. *Urgent Expiry*: Identifies perishables expiring within 1-3 days and prioritizes them at the top of the user's dashboard.
> 2. *Recipe Pairing*: Detects combinations of expiring ingredients (e.g., tomatoes + paneer) and suggests culinary usage ideas.
> 3. *Predictive Replenishment*: Evaluates days held vs. current quantity and average household purchase cycles (e.g., 30 days for cooking oil) to warn when stock will deplete within 5 days.

### Q3: How is expense analytics calculated?
> **Answer**: Rather than raw database queries, the system uses **Pandas** in `app/services/analytics.py` to perform time-series resample and group-by aggregations. This produces daily rolling averages, month-over-month trends, category expenditure distribution, and financial loss calculations on expired items.
