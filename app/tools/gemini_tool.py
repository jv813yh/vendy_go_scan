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
DEFAULT_MODE = "During hike"
VALID_MODES = {
    "Before hike",
    "During hike",
    "After hike",
    "Gym / training",
    "Cottage / recovery",
    "Chill / ordinary day",
}

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


def normalize_mode(mode: str) -> str:
    clean_mode = mode.strip()
    return clean_mode if clean_mode in VALID_MODES else DEFAULT_MODE


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


def _normalize_mapping(value: Any, defaults: dict[str, str]) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    return {
        key: str(source.get(key) or default).strip()
        for key, default in defaults.items()
    }


def default_prescription(mode: str) -> dict[str, str]:
    if mode == "Gym / training":
        return {
            "water": "Pár dúškov teraz, potom priebežne počas tréningu.",
            "food": "Po tréningu daj proteín a normálne jedlo, cukry len ak energia padá.",
            "pace": "Kontrolované série, technika pred egom.",
            "rest": "Medzi sériami si daj pokojný oddych.",
            "sleep": "Večer nepodceň spánok, svaly rastú mimo činky.",
        }
    if mode == "Cottage / recovery":
        return {
            "water": "Daj si vodu aj medzi odmenami.",
            "food": "Niečo teplé a dobré padne vhod, telo nie je len batéria.",
            "pace": "Tempo pokojné, dnes vyhráva regenerácia.",
            "rest": "Sadni si, vylož nohy a nechaj systém dobehnúť.",
            "sleep": "Dnes choď spať rozumne, zajtra sa ti nohy poďakujú.",
        }
    if mode == "Chill / ordinary day":
        return {
            "water": "Drž vodu po ruke a priebežne sa napi.",
            "food": "Daj si normálne jedlo, nie iba náhodné zobkanie popri dni.",
            "pace": "Tempo pokojné, stačí krátka prechádzka alebo ľahký pohyb.",
            "rest": "Ak si unavený, daj si vedomú pauzu bez výčitiek.",
            "sleep": "Večer to nenaťahuj zbytočne, spánok je dnešný upgrade.",
        }
    if mode == "After hike":
        return {
            "water": "Doplň vodu a minerály.",
            "food": "Daj kombináciu sacharidov a bielkovín.",
            "pace": "Už nepretekaj, prejdi do režimu návratu.",
            "rest": "Krátky strečing a nohy hore.",
            "sleep": "Spánok dnes ber ako súčasť tréningu.",
        }
    if mode == "Before hike":
        return {
            "water": "Napij sa ešte pred štartom.",
            "food": "Zober snack na rýchlu energiu.",
            "pace": "Začni ľahko, prvé minúty nie sú finále.",
            "rest": "Skontroluj výstroj bez stresu.",
            "sleep": "Ak si spal málo, naplánuj kratšiu trasu.",
        }
    return {
        "water": "Daj si pár dúškov vody.",
        "food": "Ak energia padá, doplň niečo malé alebo sladké.",
        "pace": "Pokračuj ľahkým tempom a sleduj dych.",
        "rest": "Pri únave si daj krátku pauzu.",
        "sleep": "Večer nezabudni na spánok, regenerácia je tichý tréner.",
    }


def default_adventure_card(mode: str, summary: str) -> dict[str, str]:
    return {
        "title": "VendyGoScan Adventure Check",
        "subtitle": summary or "Rýchla kontrola energie, tempa a ďalšieho kroku.",
        "vibe": mode,
        "share_text": summary or "VendyGoScan mi dal mini plán na ďalší krok.",
    }


def _normalize_analysis(data: dict[str, Any], mode: str) -> dict[str, Any]:
    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    summary = str(data.get("summary", "")).strip()
    prescription = _normalize_mapping(data.get("prescription"), default_prescription(mode))
    adventure_card = _normalize_mapping(
        data.get("adventure_card"),
        default_adventure_card(mode, summary),
    )
    return {
        "mode": normalize_mode(str(data.get("mode") or mode)),
        "summary": summary,
        "scores": {
            "creativity": _normalize_score(scores.get("creativity"), 6),
            "energy": _normalize_score(scores.get("energy"), 6),
            "focus": _normalize_score(scores.get("focus"), 6),
        },
        "badges": _normalize_list(data.get("badges"), 4),
        "tips": _normalize_list(data.get("tips"), 5),
        "prescription": prescription,
        "next_step": str(data.get("next_step", "")).strip(),
        "challenge": str(data.get("challenge", "")).strip(),
        "killer_insight": str(data.get("killer_insight", "")).strip(),
        "share_text": str(data.get("share_text") or adventure_card["share_text"]).strip(),
        "adventure_card": adventure_card,
    }


def _analysis_from_text(text: str, mode: str) -> dict[str, Any]:
    summary = text.strip()
    return {
        "mode": mode,
        "summary": summary,
        "scores": {"creativity": 5, "energy": 5, "focus": 5},
        "badges": ["Coach note", mode],
        "tips": [summary],
        "prescription": default_prescription(mode),
        "next_step": "Skús fotku znova alebo pridaj krátku poznámku, na čo sa má tréner zamerať.",
        "challenge": "Mini výzva: daj si 5 hlbokých nádychov a rozhodni sa pokojne.",
        "killer_insight": "Ak máš spraviť len jednu vec: zastav sa na chvíľu a skontroluj vodu, dych a energiu.",
        "share_text": summary,
        "adventure_card": default_adventure_card(mode, summary),
    }


def unavailable_analysis(mode: str = DEFAULT_MODE) -> dict[str, Any]:
    summary = "Tréner je teraz preťažený, ale stále vieme spraviť rozumný mini plán."
    return {
        "mode": mode,
        "summary": summary,
        "scores": {"creativity": 4, "energy": 4, "focus": 6},
        "badges": ["Model busy", "Skús znova", mode],
        "tips": [
            "Gemini je momentálne zaneprázdnený alebo rate-limitovaný.",
            "Skús analýzu zopakovať o chvíľu.",
            "Ak si na túre: voda, krátka pauza a niečo malé pod zub sú bezpečná klasika.",
        ],
        "prescription": default_prescription(mode),
        "next_step": "Stlač Analyze ešte raz o pár sekúnd.",
        "challenge": "Kým čakáš: 30 sekúnd ramená dozadu, nádych, výdych. Malý reset, veľký efekt.",
        "killer_insight": "Ak máš spraviť len jednu vec: daj si vodu a skús analýzu znova o chvíľu.",
        "share_text": "VendyGoScan tréner si dáva krátky oddych. Skúsim znova o chvíľu.",
        "adventure_card": default_adventure_card(mode, summary),
    }


def ask_gemini_with_image(
    image_bytes: bytes,
    mime_type: str,
    features: VisionFeatures,
    custom_prompt: str = "",
    mode: str = DEFAULT_MODE,
) -> dict[str, Any] | None:
    selected_mode = normalize_mode(mode)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "replace-with-your-real-key":
        _log_model_event(
            {
                "event": "missing_api_key",
                "features": features.to_dict(),
                "custom_prompt": custom_prompt,
                "mode": selected_mode,
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
        f"Selected activity mode: {selected_mode}. Use this mode strongly.\n"
        "Mode rules: Before hike means readiness, clothing, pack, water, snack, and route prep. "
        "During hike means continue/rest decision, pace, sugar, water, shade, and safety. "
        "After hike means recovery, protein/carbs, stretching, warm food, and sleep. "
        "Gym / training means controlled training, enough protein, hydration, and avoiding "
        "unnecessary fast carbohydrates unless quick energy is needed. Cottage / recovery "
        "means food, rest, playful cottage mood, optional beer or raspberry soft drink as "
        "a joke/choice, and never pressuring alcohol. Chill / ordinary day means normal daily "
        "energy, mood, gentle movement, hydration, food rhythm, stress reset, and sleep hygiene.\n\n"
        "Return ONLY valid JSON, no markdown fences. All user-facing string values must "
        "be in Slovak. Schema:\n"
        "{\n"
        "  \"mode\": \"one of the provided mode labels\",\n"
        "  \"summary\": \"one sentence\",\n"
        "  \"scores\": {\"creativity\": 0-10, \"energy\": 0-10, \"focus\": 0-10},\n"
        "  \"badges\": [\"2-4 short badges\"],\n"
        "  \"tips\": [\"3-5 practical bullet tips\"],\n"
        "  \"prescription\": {\n"
        "    \"water\": \"concrete water advice\",\n"
        "    \"food\": \"concrete food advice\",\n"
        "    \"pace\": \"pace or training intensity advice\",\n"
        "    \"rest\": \"rest or recovery advice\",\n"
        "    \"sleep\": \"sleep advice\"\n"
        "  },\n"
        "  \"next_step\": \"one concrete action\",\n"
        "  \"challenge\": \"one small fun challenge\",\n"
        "  \"killer_insight\": \"Ak máš spraviť len jednu vec: ...\",\n"
        "  \"share_text\": \"short shareable result\",\n"
        "  \"adventure_card\": {\n"
        "    \"title\": \"short card title\",\n"
        "    \"subtitle\": \"short card subtitle\",\n"
        "    \"vibe\": \"short vibe label\",\n"
        "    \"share_text\": \"short shareable card text\"\n"
        "  }\n"
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
                    "mode": selected_mode,
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
                    "mode": selected_mode,
                }
            )
            continue

        cleaned_text = text.strip().strip("`").strip()
        if cleaned_text.startswith("json"):
            cleaned_text = cleaned_text[4:].strip()

        try:
            analysis = _normalize_analysis(json.loads(cleaned_text), selected_mode)
        except json.JSONDecodeError:
            analysis = _analysis_from_text(text.strip().strip('"'), selected_mode)
            _log_model_event(
                {
                    "event": "json_parse_fallback",
                    "model": model,
                    "mode": selected_mode,
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
                    "mode": selected_mode,
                    "analysis": analysis,
                }
            )

        return analysis

    return unavailable_analysis(selected_mode)
