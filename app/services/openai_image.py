import base64
import os
import uuid
from pathlib import Path

from openai import OpenAI

from app.config import settings


def _save_generated_image(image_bytes: bytes) -> str:
    out_dir = Path(settings.generated_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.png"
    output_path = out_dir / filename
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    return os.path.join("generated", filename)


def _generate_with_openai(prompt: str, model: str, api_key: str, size: str) -> bytes:
    client = OpenAI(api_key=api_key)
    result = client.images.generate(model=model, prompt=prompt, size=size)

    image_b64 = result.data[0].b64_json
    if not image_b64:
        raise RuntimeError("Image API returned no base64 payload.")

    return base64.b64decode(image_b64)


def _generate_with_gemini(prompt: str, model: str, api_key: str) -> bytes:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("Gemini support requires installing 'google-genai'.") from exc

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"response_modalities": ["TEXT", "IMAGE"]},
    )

    for candidate in response.candidates or []:
        content = getattr(candidate, "content", None)
        for part in (getattr(content, "parts", None) or []):
            inline_data = getattr(part, "inline_data", None)
            if not inline_data:
                continue
            raw_data = getattr(inline_data, "data", None)
            if not raw_data:
                continue
            if isinstance(raw_data, bytes):
                return raw_data
            if isinstance(raw_data, str):
                return base64.b64decode(raw_data)

    raise RuntimeError("Gemini API returned no image bytes.")


def generate_icon_image(
    prompt: str,
    provider: str,
    model: str,
    api_key: str | None = None,
    size: str | None = None,
) -> str:
    normalized_provider = (provider or "").strip().lower()
    effective_api_key = (api_key or "").strip()

    if not effective_api_key:
        if normalized_provider == "gemini":
            effective_api_key = settings.gemini_api_key.strip()
        else:
            effective_api_key = settings.openai_api_key.strip()
    if not effective_api_key:
        if normalized_provider == "gemini":
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    if normalized_provider == "gemini":
        image_bytes = _generate_with_gemini(prompt, model, effective_api_key)
    else:
        image_bytes = _generate_with_openai(
            prompt,
            model=model,
            api_key=effective_api_key,
            size=size or settings.image_size,
        )

    return _save_generated_image(image_bytes)
