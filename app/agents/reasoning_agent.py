from app.tools.gemini_tool import ask_gemini_with_image
from app.tools.vision_tool import VisionFeatures


def create_recommendation(
    image_bytes: bytes,
    mime_type: str,
    features: VisionFeatures,
    fallback_text: str,
    custom_prompt: str = "",
) -> dict[str, object]:
    recommendation = ask_gemini_with_image(image_bytes, mime_type, features, custom_prompt)
    if recommendation:
        return recommendation

    return {
        "summary": fallback_text,
        "scores": {"creativity": 3, "energy": 3, "focus": 4},
        "badges": ["Bez analýzy"],
        "tips": [fallback_text],
        "next_step": "Skús inú fotku s lepším svetlom.",
        "challenge": "Mini výzva: sprav novú fotku ako hrdina pred štartom túry.",
        "killer_insight": "Ak máš spraviť len jednu vec: sprav jasnejšiu fotku celej postavy.",
        "share_text": fallback_text,
    }
