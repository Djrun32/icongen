from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.bootstrap import ensure_default_settings, ensure_initial_admin, ensure_seed_styles
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routes import admin_routes, auth_routes, user_routes


app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie,
    same_site="lax",
    https_only=settings.session_https_only,
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    Path(settings.generated_dir).mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        ensure_initial_admin(db)
        ensure_default_settings(db)
        ensure_seed_styles(db)
    finally:
        db.close()


app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(admin_routes.router)


@app.get("/")
def home(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/generate", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.exception_handler(401)
def unauthorized(_: Request, __):
    return RedirectResponse(url="/login", status_code=302)


@app.exception_handler(403)
def forbidden(request: Request, __):
    return templates.TemplateResponse(
        "forbidden.html",
        {
            "request": request,
            "message": "This section is restricted to administrators.",
        },
        status_code=403,
    )
