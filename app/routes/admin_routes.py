from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.db import get_db
from app.deps import require_admin
from app.models import StylePreset, User
from app.settings_store import get_setting, set_setting


router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def admin_home():
    return RedirectResponse(url="/admin/styles", status_code=302)


@router.get("/styles")
def styles_page(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    styles = db.query(StylePreset).order_by(StylePreset.name).all()
    return templates.TemplateResponse(
        "admin_styles.html",
        {
            "request": request,
            "current_user": admin,
            "styles": styles,
        },
    )


@router.post("/styles")
def create_style(
    name: str = Form(...),
    prompt_instructions: str = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not db.query(StylePreset).filter(StylePreset.name == name.strip()).first():
        db.add(
            StylePreset(
                name=name.strip(),
                prompt_instructions=prompt_instructions.strip(),
                is_active=True,
            )
        )
        db.commit()
    return RedirectResponse(url="/admin/styles", status_code=302)


@router.post("/styles/{style_id}/toggle")
def toggle_style(
    style_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    style = db.query(StylePreset).filter(StylePreset.id == style_id).first()
    if style:
        style.is_active = not style.is_active
        db.commit()
    return RedirectResponse(url="/admin/styles", status_code=302)


@router.post("/styles/{style_id}/delete")
def delete_style(
    style_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    style = db.query(StylePreset).filter(StylePreset.id == style_id).first()
    if style:
        db.delete(style)
        db.commit()
    return RedirectResponse(url="/admin/styles", status_code=302)


@router.get("/settings")
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse(
        "admin_settings.html",
        {
            "request": request,
            "current_user": admin,
            "global_system_prompt": get_setting(db, "global_system_prompt"),
            "max_metaphor_length": get_setting(db, "max_metaphor_length", "80"),
            "users": users,
        },
    )


@router.post("/settings")
def update_settings(
    global_system_prompt: str = Form(...),
    max_metaphor_length: int = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    set_setting(db, "global_system_prompt", global_system_prompt.strip())
    set_setting(db, "max_metaphor_length", str(max(10, min(max_metaphor_length, 300))))
    return RedirectResponse(url="/admin/settings", status_code=302)


@router.post("/users")
def create_user(
    username: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.username == username.strip()).first()
    if not existing and username.strip() and password:
        db.add(
            User(
                username=username.strip(),
                password_hash=hash_password(password),
                is_admin=is_admin,
                is_active=True,
            )
        )
        db.commit()
    return RedirectResponse(url="/admin/settings", status_code=302)


@router.post("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.id != admin.id:
        user.is_active = not user.is_active
        db.commit()
    return RedirectResponse(url="/admin/settings", status_code=302)
