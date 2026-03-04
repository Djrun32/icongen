import os


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_name: str = os.getenv("APP_NAME", "Intranet Icon Generator")
    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret-in-production")
    session_cookie: str = os.getenv("SESSION_COOKIE_NAME", "icongen_session")
    session_https_only: bool = _env_bool("SESSION_HTTPS_ONLY", False)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./icongen.db")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    image_model: str = os.getenv("IMAGE_MODEL", "gpt-image-1")
    image_size: str = os.getenv("IMAGE_SIZE", "1024x1024")
    generated_dir: str = os.getenv("GENERATED_DIR", "app/static/generated")
    initial_admin_username: str = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
    initial_admin_password: str = os.getenv("INITIAL_ADMIN_PASSWORD", "change-me-now")


settings = Settings()
