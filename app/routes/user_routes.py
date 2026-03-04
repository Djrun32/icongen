from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models import GeneratedIcon, StylePreset, User
from app.services.openai_image import generate_icon_image
from app.settings_store import get_setting


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _build_prompt(style_instructions: str, metaphor: str) -> str:
    return (
        f"Style instructions: {style_instructions}\n"
        f"Metaphor to represent: {metaphor}"
    )


def _get_recent_history(db: Session, user_id: int, limit: int = 10):
    history_rows = (
        db.query(GeneratedIcon, StylePreset.name)
        .join(StylePreset, GeneratedIcon.style_id == StylePreset.id, isouter=True)
        .filter(GeneratedIcon.user_id == user_id)
        .order_by(GeneratedIcon.created_at.desc(), GeneratedIcon.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "metaphor": icon.metaphor,
            "style_name": style_name or "Unknown style",
            "created_at": icon.created_at,
            "result_path": f"/static/{icon.file_path}",
        }
        for icon, style_name in history_rows
    ]


def _render_generate_page(
    request: Request,
    current_user: User,
    styles: list[StylePreset],
    history: list[dict],
    result_path: str | None = None,
    error: str | None = None,
    metaphor: str = "",
    selected_style_id: int | None = None,
    status_code: int = 200,
):
    if selected_style_id is None and styles:
        selected_style_id = styles[0].id
    return templates.TemplateResponse(
        "generate.html",
        {
            "request": request,
            "current_user": current_user,
            "styles": styles,
            "history": history,
            "result_path": result_path,
            "error": error,
            "metaphor": metaphor,
            "selected_style_id": selected_style_id,
        },
        status_code=status_code,
    )


@router.get("/generate")
def generate_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    styles = db.query(StylePreset).filter(StylePreset.is_active == True).order_by(StylePreset.name).all()  # noqa: E712
    history = _get_recent_history(db, current_user.id, limit=10)
    return _render_generate_page(
        request=request,
        current_user=current_user,
        styles=styles,
        history=history,
    )


@router.post("/generate")
def generate_icon(
    request: Request,
    metaphor: str = Form(...),
    style_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    styles = db.query(StylePreset).filter(StylePreset.is_active == True).order_by(StylePreset.name).all()  # noqa: E712
    history = _get_recent_history(db, current_user.id, limit=10)
    style = db.query(StylePreset).filter(StylePreset.id == style_id, StylePreset.is_active == True).first()  # noqa: E712
    raw_metaphor = metaphor.strip()

    if not style:
        return _render_generate_page(
            request=request,
            current_user=current_user,
            styles=styles,
            history=history,
            error="Selected style is not available.",
            metaphor=raw_metaphor,
            selected_style_id=style_id,
            status_code=400,
        )

    max_length = int(get_setting(db, "max_metaphor_length", "80"))
    if not raw_metaphor:
        return _render_generate_page(
            request=request,
            current_user=current_user,
            styles=styles,
            history=history,
            error="Metaphor is required.",
            selected_style_id=style_id,
            status_code=400,
        )
    if len(raw_metaphor) > max_length:
        return _render_generate_page(
            request=request,
            current_user=current_user,
            styles=styles,
            history=history,
            error=f"Metaphor is too long. Maximum length is {max_length}.",
            metaphor=raw_metaphor,
            selected_style_id=style_id,
            status_code=400,
        )

    prompt = _build_prompt(style.prompt_instructions, raw_metaphor)
    image_provider = get_setting(db, "image_provider", settings.image_provider).strip().lower() or settings.image_provider
    image_model = get_setting(db, "image_model", settings.image_model).strip() or settings.image_model
    legacy_openai_api_key = get_setting(db, "openai_api_key", "").strip()
    stored_model_api_key = get_setting(db, "model_api_key", legacy_openai_api_key).strip()
    if image_provider == "gemini":
        effective_api_key = stored_model_api_key or settings.gemini_api_key
    else:
        effective_api_key = stored_model_api_key or settings.openai_api_key

    try:
        relative_path = generate_icon_image(
            prompt=prompt,
            provider=image_provider,
            model=image_model,
            api_key=effective_api_key,
            size=settings.image_size,
        )
    except Exception as exc:
        return _render_generate_page(
            request=request,
            current_user=current_user,
            styles=styles,
            history=history,
            error=f"Image generation failed: {exc}",
            metaphor=raw_metaphor,
            selected_style_id=style_id,
            status_code=500,
        )

    db.add(
        GeneratedIcon(
            user_id=current_user.id,
            style_id=style.id,
            metaphor=raw_metaphor,
            prompt_used=prompt,
            file_path=relative_path,
        )
    )
    db.commit()
    updated_history = _get_recent_history(db, current_user.id, limit=10)

    return _render_generate_page(
        request=request,
        current_user=current_user,
        styles=styles,
        history=updated_history,
        result_path=f"/static/{relative_path}",
        metaphor=raw_metaphor,
        selected_style_id=style_id,
    )
