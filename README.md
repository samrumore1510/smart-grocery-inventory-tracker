# 🛒 Smart Grocery Inventory & Expiry Tracker (NoSQL • Vibe-Coded Edition)

> **Modern Academic Portfolio & Production-Ready Full-Stack Web Application**  
> Built with **Python 3.11+**, **FastAPI**, **MongoDB (NoSQL)**, **Pure PyMongo (Zero ORM)**, **Pandas**, and a **Modern Vanilla JavaScript SPA (Zero Jinja2)**.

---

## 🎯 Real-World Problem Solved
People and households often:
1. **Forget product expiry dates**, leading to food wastage and lost money.
2. **Accidentally buy duplicates** of groceries they already have in the pantry.
3. **Run out of staple items** unexpectedly (e.g., milk, rice, oil).
4. **Lack visibility into grocery expenditure**, unaware of where their monthly food budget goes.

### 💡 The Solution
A clean, lightning-fast web application that:
- 🔔 **Classifies grocery expiry**:
  - `Expired ❌` (already passed expiry date)
  - `Critical 🔴` (expires in 1–3 days)
  - `Warning 🟠` (expires in 4–7 days)
  - `Fresh ✅` (more than 7 days remaining)
- 📦 **Monitors stock thresholds**:
  - `Out of Stock ❌` (quantity = 0)
  - `Low Stock ⚠️` (quantity ≤ minimum threshold)
  - `Available ✅` (healthy stock levels)
- 🛍️ **Auto-Sync Smart Shopping List**:
  - Automatically identifies low-stock items and queues them for restock.
  - Check off purchased items to automatically restore pantry quantities!
  - 📲 **1-Click WhatsApp export** for easy sharing with roommates or family.
- 💰 **Pandas-Powered Financial Analytics**:
  - Continuous 30-day spending trends, monthly expenditure, category distribution charts, and potential food wastage loss calculation.
- 📄 **1-Click Executive Reports**:
  - Beautiful tabular PDF export (ReportLab) and Excel spreadsheet export (OpenPyXL).

---

## 🏗️ Clean "Vibe Code" Architecture (Zero ORM • Zero Jinja2)

This project has been intentionally redesigned to be **intuitive, readable, and easy to explain** in project vivas or interviews:

```
D:\smart_grocery_tracker\
├── database.py         # Direct MongoDB connection & PyMongo collections (Zero ORM)
├── services.py         # Pure Python business logic, expiry classifiers & Pandas analytics
├── main.py             # FastAPI REST endpoints & static web app server
├── seed.py             # One-click demo database populator with exact portfolio metrics
├── requirements.txt    # Lean Python dependencies
├── static/             # Single-Page Application (SPA) Frontend (Zero Jinja2)
│   ├── index.html      # Semantic HTML5 dashboard, modals & tabbed UI
│   ├── style.css       # Modern CSS design system (Plus Jakarta Sans, responsive grid)
│   └── app.js          # Reactive Vanilla JS calling REST API via fetch()
└── tests/
    └── test_mongo.py   # Automated Pytest test suite (100% passing)
```

### ⚡ Why No ORM?
Instead of heavy, complicated Object-Relational Mappers (like SQLAlchemy) that hide what happens under the hood, this project uses **direct PyMongo dictionary queries** (`products_col.find()`, `insert_one()`, `update_one()`, `$set`). This gives:
- 🚀 **Maximum speed & zero overhead**.
- 🧠 **100% transparent Python dictionaries**: what you see in the database is exactly what you get in Python.
- 🎓 **Easy to understand and explain** in viva examinations.

### ⚡ Why No Jinja2?
Instead of fragmented HTML files and server-side template rendering, the frontend is a **modern Single-Page Application (SPA)** using pure Vanilla HTML, CSS, and JavaScript.
- The browser communicates with the Python backend entirely over clean **REST API endpoints** (`/api/dashboard`, `/api/inventory`, `/api/shopping`, `/api/expenses`).
- Provides instantaneous tab switching, live filters, and smooth micro-animations with zero page reloads.

---

## 📊 Seeded Portfolio Benchmark Metrics

When you run `python seed.py`, MongoDB is populated with the following verified portfolio data:

| Metric | Target Value | Description |
| :--- | :---: | :--- |
| **Total Products** | **35** | Distributed across 10 staple grocery categories |
| **Expiring Soon** | **4** | 3 critical (1-3 days) + 1 warning (4-7 days) |
| **Expired Items** | **2** | 1 bread & 1 yogurt past date (triggers wastage warning) |
| **Low Stock Items** | **5** | Low quantity items auto-queued to shopping list |
| **Monthly Spending** | **₹4,250.00** | September 2026 grocery expenditures |
| **Potential Food Wastage** | **₹170.00** | Total monetary value of the 2 expired items |

### Pre-configured User Accounts
- **Regular User (Primary Demo)**:
  - **Username**: `user`
  - **Password**: `user123`
  - *Contains the complete 35-item pantry and ₹4,250 expense history.*
- **System Administrator**:
  - **Username**: `admin`
  - **Password**: `admin123`

---

## 🚀 How to Run the Project (Step-by-Step)

### Prerequisites
- Python 3.11 or higher installed on your computer.
- Local MongoDB running on `localhost:27017` (MongoDB Community Server).

### Step 1: Install Dependencies
Open PowerShell or Command Prompt in the project folder:
```powershell
cd D:\smart_grocery_tracker
pip install -r requirements.txt
```

### Step 2: Seed the Database
Populate MongoDB with the 35 products and ₹4,250 spending metrics:
```powershell
python seed.py
```
*(You will see confirmation output confirming 35 products and ₹4,250 expenses).*

### Step 3: Start the Application
```powershell
python main.py
```
Now open your web browser and go to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Interactive API Swagger documentation is available at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🧪 Running Automated Unit Tests
To verify all expiry calculations, stock classifications, database queries, and report exports:
```powershell
pytest tests/test_mongo.py -v
```
*All 9 tests pass with 100% green checkmarks.*

---

## 💡 How to Share This Project with Friends / Evaluators

### Option A: Send via ZIP Archive
1. Delete the `__pycache__` and `.pytest_cache` folders if present.
2. Right-click the `smart_grocery_tracker` folder -> **Send to** -> **Compressed (zipped) folder**.
3. Send the ZIP file to your friend.
4. Your friend simply extracts the ZIP, runs `pip install -r requirements.txt`, runs `python seed.py`, and launches `python main.py`!

### Option B: Host on Local Wi-Fi (Live Demo on Phone/Laptop)
To let friends on the same Wi-Fi network use your tracker from their mobile phones:
1. In `main.py`, change `host="127.0.0.1"` to `host="0.0.0.0"`.
2. Find your laptop IP address by typing `ipconfig` in PowerShell (e.g. `192.168.1.15`).
3. Run `python main.py`.
4. Anyone on your Wi-Fi can open `http://192.168.1.15:8000` from their mobile phone!

---

## 🎓 Academic Viva & Technical Interview Q&A

**Q1: Why did you choose MongoDB over a relational database like MySQL or SQLite?**  
> *Grocery items have dynamic, heterogeneous attributes (e.g., expiry dates, storage locations, varying units like kg, L, packets). A document-oriented NoSQL database like MongoDB provides flexible BSON schema, natural JSON compatibility with REST APIs, and blazing-fast indexed lookups without complex JOIN queries.*

**Q2: How does the expiry classification logic work?**  
> *The application compares each product's `expiry_date` against the current date (`date.today()`). If days < 0, it's marked `Expired ❌`. If 0 to 3 days, it's `Critical 🔴`. If 4 to 7 days, it's `Warning 🟠`. Otherwise, it's `Fresh ✅`. This calculation is performed dynamically by pure Python functions in `services.py`.*

**Q3: How does the automated shopping list work?**  
> *Whenever a product's `quantity` falls below its `min_quantity` threshold (or when the user clicks 'Auto-Sync'), the system calculates the replenishment amount needed (`2 * min_quantity - current_quantity`) and inserts it into `shopping_col`. When the user checks the item as purchased, the system automatically increases the inventory quantity in `products_col`.*

**Q4: How does Pandas fit into this application?**  
> *Pandas acts as the data analytics engine. In `services.py`, expense documents from MongoDB are converted into a Pandas DataFrame. We use `df.groupby()` and `pd.date_range()` to resample daily transactions over a 30-day window, aggregate monthly spending, and compute food wastage loss from expired items.*

---

## 📜 Technology Stack Summary
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic
- **Database**: MongoDB 7.0+, PyMongo (Direct NoSQL, Zero ORM)
- **Analytics & Math**: Pandas
- **Document Generation**: ReportLab (PDF), OpenPyXL (Excel)
- **Security & Auth**: JWT (python-jose), Passlib (Bcrypt)
- **Frontend**: Vanilla HTML5, Vanilla CSS3 (Custom Design System), Modern ES6 JavaScript (Fetch API), Chart.js (Charts)
- **Testing**: Pytest, HTTPX, FastAPI TestClient
