import base64
import os
import uuid
from pathlib import Path

from openai import OpenAI

from app.config import settings


def generate_icon_with_openai(prompt: str, api_key: str | None = None) -> str:
    effective_api_key = (api_key or "").strip() or settings.openai_api_key
    if not effective_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=effective_api_key)
    result = client.images.generate(
        model=settings.image_model,
        prompt=prompt,
        size=settings.image_size,
    )

    image_b64 = result.data[0].b64_json
    if not image_b64:
        raise RuntimeError("Image API returned no base64 payload.")

    image_bytes = base64.b64decode(image_b64)
    out_dir = Path(settings.generated_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.png"
    output_path = out_dir / filename

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return os.path.join("generated", filename)
