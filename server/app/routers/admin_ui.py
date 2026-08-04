from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser
from ..security import require_login, verify_password

router = APIRouter(tags=["admin-ui"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None, "username": None})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Usuário ou senha inválidos", "username": None}
        )
    request.session["admin_id"] = admin.id
    request.session["admin_username"] = admin.username
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request, admin_id: str = Depends(require_login)):
    return templates.TemplateResponse(
        request, "dashboard.html", {"username": request.session.get("admin_username")}
    )


@router.get("/licenses/new")
def new_license_form(request: Request, admin_id: str = Depends(require_login)):
    return templates.TemplateResponse(
        request,
        "new_license.html",
        {"error": None, "username": request.session.get("admin_username")},
    )


@router.get("/admins")
def admins_page(request: Request, admin_id: str = Depends(require_login)):
    return templates.TemplateResponse(
        request, "admins.html", {"username": request.session.get("admin_username")}
    )
