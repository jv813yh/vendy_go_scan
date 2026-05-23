from app.agents.reasoning_agent import create_recommendation
from app.agents.vision_agent import analyze_image

FALLBACK_TEXT = "Nie je možné spoľahlivo vyhodnotiť stav. Skús inú fotku."


def analyze_hiker(image_bytes: bytes, mime_type: str, custom_prompt: str = "") -> dict[str, object]:
    features = analyze_image(image_bytes)
    return create_recommendation(
        image_bytes=image_bytes,
        mime_type=mime_type,
        features=features,
        fallback_text=FALLBACK_TEXT,
        custom_prompt=custom_prompt,
    )
