from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import GeneratedIcon, StylePreset, User
from app.services.openai_image import generate_icon_with_openai
from app.settings_store import get_setting


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _build_prompt(system_prompt: str, style_instructions: str, metaphor: str) -> str:
    return (
        f"{system_prompt}\n"
        f"Style constraints: {style_instructions}\n"
        f"Metaphor to represent: {metaphor}\n"
        "Output one icon only. Clean edges, no text, no logo, no watermark."
    )


@router.get("/generate")
def generate_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    styles = db.query(StylePreset).filter(StylePreset.is_active == True).order_by(StylePreset.name).all()  # noqa: E712
    return templates.TemplateResponse(
        "generate.html",
        {
            "request": request,
            "current_user": current_user,
            "styles": styles,
            "result_path": None,
            "error": None,
        },
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
    style = db.query(StylePreset).filter(StylePreset.id == style_id, StylePreset.is_active == True).first()  # noqa: E712
    if not style:
        return templates.TemplateResponse(
            "generate.html",
            {
                "request": request,
                "current_user": current_user,
                "styles": styles,
                "result_path": None,
                "error": "Selected style is not available.",
            },
            status_code=400,
        )

    max_length = int(get_setting(db, "max_metaphor_length", "80"))
    metaphor = metaphor.strip()
    if not metaphor:
        return templates.TemplateResponse(
            "generate.html",
            {
                "request": request,
                "current_user": current_user,
                "styles": styles,
                "result_path": None,
                "error": "Metaphor is required.",
            },
            status_code=400,
        )
    if len(metaphor) > max_length:
        return templates.TemplateResponse(
            "generate.html",
            {
                "request": request,
                "current_user": current_user,
                "styles": styles,
                "result_path": None,
                "error": f"Metaphor is too long. Maximum length is {max_length}.",
            },
            status_code=400,
        )

    system_prompt = get_setting(db, "global_system_prompt")
    prompt = _build_prompt(system_prompt, style.prompt_instructions, metaphor)

    try:
        relative_path = generate_icon_with_openai(prompt)
    except Exception as exc:
        return templates.TemplateResponse(
            "generate.html",
            {
                "request": request,
                "current_user": current_user,
                "styles": styles,
                "result_path": None,
                "error": f"Image generation failed: {exc}",
            },
            status_code=500,
        )

    db.add(
        GeneratedIcon(
            user_id=current_user.id,
            style_id=style.id,
            metaphor=metaphor,
            prompt_used=prompt,
            file_path=relative_path,
        )
    )
    db.commit()

    return templates.TemplateResponse(
        "generate.html",
        {
            "request": request,
            "current_user": current_user,
            "styles": styles,
            "result_path": f"/static/{relative_path}",
            "error": None,
        },
    )
