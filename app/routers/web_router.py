from pathlib import Path
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user_optional
from app import models

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def root_page(
    request: Request,
    user: models.User = Depends(get_current_user_optional)
):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    user: models.User = Depends(get_current_user_optional)
):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})


@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    user: models.User = Depends(get_current_user_optional)
):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "title": "Create Account"})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    user: models.User = Depends(get_current_user_optional)
):
    if not user:
        return RedirectResponse(url="/login?msg=Please+login+to+continue", status_code=302)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "title": "Smart Dashboard",
        "active_tab": "dashboard"
    })


@router.get("/inventory", response_class=HTMLResponse)
def inventory_page(
    request: Request,
    user: models.User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login?msg=Please+login+to+continue", status_code=302)
    categories = db.query(models.Category).order_by(models.Category.id).all()
    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "user": user,
        "categories": categories,
        "title": "Grocery Inventory",
        "active_tab": "inventory"
    })


@router.get("/shopping-list", response_class=HTMLResponse)
def shopping_page(
    request: Request,
    user: models.User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login?msg=Please+login+to+continue", status_code=302)
    categories = db.query(models.Category).order_by(models.Category.id).all()
    return templates.TemplateResponse("shopping_list.html", {
        "request": request,
        "user": user,
        "categories": categories,
        "title": "Smart Shopping List",
        "active_tab": "shopping"
    })


@router.get("/expenses", response_class=HTMLResponse)
def expenses_page(
    request: Request,
    user: models.User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login?msg=Please+login+to+continue", status_code=302)
    categories = db.query(models.Category).order_by(models.Category.id).all()
    return templates.TemplateResponse("expenses.html", {
        "request": request,
        "user": user,
        "categories": categories,
        "title": "Expense Tracking & Trends",
        "active_tab": "expenses"
    })
