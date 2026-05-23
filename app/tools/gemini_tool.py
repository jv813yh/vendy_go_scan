import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.tools.vision_tool import VisionFeatures

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_FALLBACK_MODELS = ["gemini-2.5-flash-lite"]

load_dotenv()

LOG_DIR = Path(os.getenv("VENDYGOSCAN_LOG_DIR", "logs"))
MODEL_LOG_FILE = LOG_DIR / "gemini_responses.jsonl"


def _model_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("vendygoscan.gemini")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(MODEL_LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def _log_model_event(event: dict[str, object]) -> None:
    event_with_time = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    _model_logger().info(json.dumps(event_with_time, ensure_ascii=False))


def _model_candidates() -> list[str]:
    primary = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    fallback_env = os.getenv("GEMINI_FALLBACK_MODELS", "")
    fallback_models = [item.strip() for item in fallback_env.split(",") if item.strip()]
    if not fallback_models:
        fallback_models = DEFAULT_FALLBACK_MODELS

    models = []
    for model in [primary, *fallback_models]:
        if model not in models:
            models.append(model)
    return models


def _normalize_score(value: Any, default: int) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(score, 10))


def _normalize_list(value: Any, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    items = [str(item).strip() for item in value if str(item).strip()]
    return items[:limit]


def _normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    return {
        "summary": str(data.get("summary", "")).strip(),
        "scores": {
            "creativity": _normalize_score(scores.get("creativity"), 6),
            "energy": _normalize_score(scores.get("energy"), 6),
            "focus": _normalize_score(scores.get("focus"), 6),
        },
        "badges": _normalize_list(data.get("badges"), 4),
        "tips": _normalize_list(data.get("tips"), 5),
        "next_step": str(data.get("next_step", "")).strip(),
        "challenge": str(data.get("challenge", "")).strip(),
        "killer_insight": str(data.get("killer_insight", "")).strip(),
        "share_text": str(data.get("share_text", "")).strip(),
    }


def _analysis_from_text(text: str) -> dict[str, Any]:
    return {
        "summary": text,
        "scores": {"creativity": 5, "energy": 5, "focus": 5},
        "badges": ["Coach note"],
        "tips": [text],
        "next_step": "Skús fotku znova alebo pridaj krátku poznámku, na čo sa má tréner zamerať.",
        "challenge": "Mini výzva: daj si 5 hlbokých nádychov a rozhodni sa pokojne.",
        "killer_insight": "Ak máš spraviť len jednu vec: zastav sa na chvíľu a skontroluj vodu, dych a energiu.",
        "share_text": text,
    }


def unavailable_analysis() -> dict[str, Any]:
    return {
        "summary": "Tréner je teraz preťažený, ale stále vieme spraviť rozumný mini plán.",
        "scores": {"creativity": 4, "energy": 4, "focus": 6},
        "badges": ["Model busy", "Skús znova"],
        "tips": [
            "Gemini je momentálne zaneprázdnený alebo rate-limitovaný.",
            "Skús analýzu zopakovať o chvíľu.",
            "Ak si na túre: voda, krátka pauza a niečo malé pod zub sú bezpečná klasika.",
        ],
        "next_step": "Stlač Analyze ešte raz o pár sekúnd.",
        "challenge": "Kým čakáš: 30 sekúnd ramená dozadu, nádych, výdych. Malý reset, veľký efekt.",
        "killer_insight": "Ak máš spraviť len jednu vec: daj si vodu a skús analýzu znova o chvíľu.",
        "share_text": "VendyGoScan tréner si dáva krátky oddych. Skúsim znova o chvíľu.",
    }


def ask_gemini_with_image(
    image_bytes: bytes,
    mime_type: str,
    features: VisionFeatures,
    custom_prompt: str = "",
) -> dict[str, Any] | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "replace-with-your-real-key":
        _log_model_event(
            {
                "event": "missing_api_key",
                "features": features.to_dict(),
                "custom_prompt": custom_prompt,
            }
        )
        return None

    client = genai.Client(api_key=api_key)
    extra_instruction = ""
    if custom_prompt:
        extra_instruction = (
            "\n\nUser extra instruction for this photo. Follow it if it does not conflict "
            f"with safety rules or the Slovak output format: {custom_prompt}"
        )

    prompt = (
        "You are VendyGoScan Coach: a friendly, funny outdoor trainer for hikers, gym "
        "people, and active people. Analyze the uploaded photo comprehensively, but "
        "only from visible cues. Consider face, expression, eyes, mood, posture, "
        "shoulders, hands, arms, legs, feet, balance, clothing, backpack load, "
        "apparent energy, readiness to continue, and the visible environment.\n\n"
        "Adapt advice to visible context. Gym: controlled training, enough protein, "
        "hydration, and do not overdo fast carbohydrates unless quick energy is needed. "
        "Hiking/sun: sun, shade, water, pace, electrolytes, and quick sugars when energy "
        "looks low. Fresh on trail: encourage steady tempo. Tired on trail: break, water, "
        "sugars, and food before pushing on. Cottage/mountain hut/post-hike stop: playful "
        "food suggestion; optionally mention beer or raspberry soft drink as a joke/choice, "
        "but never pressure alcohol. Unsuitable clothes: mention layers, shoes, rain/sun "
        "protection, or changing plans.\n\n"
        "Return ONLY valid JSON, no markdown fences. All user-facing string values must "
        "be in Slovak. Schema:\n"
        "{\n"
        "  \"summary\": \"one sentence\",\n"
        "  \"scores\": {\"creativity\": 0-10, \"energy\": 0-10, \"focus\": 0-10},\n"
        "  \"badges\": [\"2-4 short badges\"],\n"
        "  \"tips\": [\"3-5 practical bullet tips\"],\n"
        "  \"next_step\": \"one concrete action\",\n"
        "  \"challenge\": \"one small fun challenge\",\n"
        "  \"killer_insight\": \"Ak máš spraviť len jednu vec: ...\",\n"
        "  \"share_text\": \"short shareable result\"\n"
        "}\n\n"
        "Always make killer_insight the strongest, simplest final action. Be supportive, "
        "honest, varied, and lightly funny. Do not make medical diagnoses, identify the "
        "person, infer sensitive traits, body-shame, or claim certainty from unclear "
        "visual cues. If the person/body/environment is not visible enough, still return "
        "the JSON shape and say that the photo is not clear enough in the summary."
        f"{extra_instruction}\n\n"
        f"Local computer-vision hints, use only as secondary context: {features.to_dict()}"
    )

    for model in _model_candidates():
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt,
                ],
            )
        except Exception as exc:
            _log_model_event(
                {
                    "event": "error",
                    "model": model,
                    "mime_type": mime_type,
                    "image_bytes": len(image_bytes),
                    "features": features.to_dict(),
                    "custom_prompt": custom_prompt,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue

        text = getattr(response, "text", None)
        if not text:
            _log_model_event(
                {
                    "event": "empty_response",
                    "model": model,
                    "mime_type": mime_type,
                    "image_bytes": len(image_bytes),
                    "features": features.to_dict(),
                    "custom_prompt": custom_prompt,
                }
            )
            continue

        cleaned_text = text.strip().strip("`").strip()
        if cleaned_text.startswith("json"):
            cleaned_text = cleaned_text[4:].strip()

        try:
            analysis = _normalize_analysis(json.loads(cleaned_text))
        except json.JSONDecodeError:
            analysis = _analysis_from_text(text.strip().strip('"'))
            _log_model_event(
                {
                    "event": "json_parse_fallback",
                    "model": model,
                    "response_text": text,
                    "analysis": analysis,
                }
            )
        else:
            _log_model_event(
                {
                    "event": "response",
                    "model": model,
                    "mime_type": mime_type,
                    "image_bytes": len(image_bytes),
                    "features": features.to_dict(),
                    "custom_prompt": custom_prompt,
                    "analysis": analysis,
                }
            )

        return analysis

    return unavailable_analysis()
