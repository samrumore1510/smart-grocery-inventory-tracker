from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import APP_NAME, DEBUG
from app.database import init_db
from app.routers import (
    auth_router,
    inventory_router,
    shopping_router,
    analytics_router,
    web_router,
)

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    yield


app = FastAPI(
    title=APP_NAME,
    description="Intelligent Grocery Inventory, Expiry Date Classifier, Expense Tracking & Predictive Replenishment System",
    version="1.0.0",
    debug=DEBUG,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include Routers
app.include_router(web_router.router)
app.include_router(auth_router.router)
app.include_router(inventory_router.router)
app.include_router(shopping_router.router)
app.include_router(analytics_router.router)


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
    # For web browser requests, redirect to dashboard or login
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)
