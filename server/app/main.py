from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "app"

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import Base, SessionLocal, engine
from .models import AdminUser
from .routers import admin_api, admin_ui, verify
from .security import hash_password

app = FastAPI(title="Andromeda License Server")

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.mount(
    "/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static"
)

app.include_router(verify.router)
app.include_router(admin_api.router)
app.include_router(admin_ui.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _bootstrap_admin()


def _bootstrap_admin():
    db = SessionLocal()
    try:
        if db.query(AdminUser).count() == 0:
            admin = AdminUser(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return RedirectResponse("/dashboard")


@app.get("/healthz")
def healthz():
    return {"ok": True}
