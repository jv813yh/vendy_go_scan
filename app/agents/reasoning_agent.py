from app.tools.gemini_tool import DEFAULT_MODE, ask_gemini_with_image, default_adventure_card, default_prescription, normalize_mode
from app.tools.vision_tool import VisionFeatures


def create_recommendation(
    image_bytes: bytes,
    mime_type: str,
    features: VisionFeatures,
    fallback_text: str,
    custom_prompt: str = "",
    mode: str = DEFAULT_MODE,
) -> dict[str, object]:
    selected_mode = normalize_mode(mode)
    recommendation = ask_gemini_with_image(
        image_bytes=image_bytes,
        mime_type=mime_type,
        features=features,
        custom_prompt=custom_prompt,
        mode=selected_mode,
    )
    if recommendation:
        return recommendation

    return {
        "mode": selected_mode,
        "summary": fallback_text,
        "scores": {"creativity": 3, "energy": 3, "focus": 4},
        "badges": ["Bez analýzy", selected_mode],
        "tips": [fallback_text],
        "prescription": default_prescription(selected_mode),
        "next_step": "Skús inú fotku s lepším svetlom.",
        "challenge": "Mini výzva: sprav novú fotku ako hrdina pred štartom túry.",
        "killer_insight": "Ak máš spraviť len jednu vec: sprav jasnejšiu fotku celej postavy.",
        "share_text": fallback_text,
        "adventure_card": default_adventure_card(selected_mode, fallback_text),
    }
