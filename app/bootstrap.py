from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.models import AppSetting, StylePreset, User


DEFAULT_SYSTEM_PROMPT = (
    "Create a clean presentation icon with a transparent background if possible. "
    "Use strong contrast, no text, no watermark, and keep composition simple."
)


def ensure_initial_admin(db: Session) -> None:
    existing_admin = db.query(User).filter(User.is_admin == True).first()  # noqa: E712
    if existing_admin:
        return

    db.add(
        User(
            username=settings.initial_admin_username,
            password_hash=hash_password(settings.initial_admin_password),
            is_admin=True,
            is_active=True,
        )
    )
    db.commit()


def ensure_default_settings(db: Session) -> None:
    if not db.query(AppSetting).filter(AppSetting.key == "global_system_prompt").first():
        db.add(AppSetting(key="global_system_prompt", value=DEFAULT_SYSTEM_PROMPT))
    if not db.query(AppSetting).filter(AppSetting.key == "max_metaphor_length").first():
        db.add(AppSetting(key="max_metaphor_length", value="80"))
    if not db.query(AppSetting).filter(AppSetting.key == "image_provider").first():
        db.add(AppSetting(key="image_provider", value=settings.image_provider))
    if not db.query(AppSetting).filter(AppSetting.key == "image_model").first():
        db.add(AppSetting(key="image_model", value=settings.image_model))
    db.commit()


def ensure_seed_styles(db: Session) -> None:
    if db.query(StylePreset).count() > 0:
        return
    seeds = [
        StylePreset(
            name="Minimal Outline",
            prompt_instructions="Monoline vector icon, minimal strokes, geometric proportions.",
            is_active=True,
        ),
        StylePreset(
            name="Flat Corporate",
            prompt_instructions="Flat icon style, solid fills, corporate colors, no gradients.",
            is_active=True,
        ),
        StylePreset(
            name="Soft 3D",
            prompt_instructions="Soft 3D clay icon, rounded shapes, subtle lighting.",
            is_active=True,
        ),
    ]
    db.add_all(seeds)
    db.commit()
