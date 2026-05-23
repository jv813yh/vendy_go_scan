import os

import requests
import streamlit as st
from PIL import Image

DEFAULT_API_URL = "http://localhost:8000/analyze"
PREVIEW_MAX_WIDTH = 420
ACTIVITY_MODES = [
    "Before hike",
    "During hike",
    "After hike",
    "Gym / training",
    "Cottage / recovery",
]
PROMPT_PRESETS = {
    "Default coach": "",
    "Continue or rest": "Focus mainly on whether I should continue, slow down, or rest now.",
    "Food and hydration": "Focus mainly on hydration, food, sugar/quick energy, and whether I should eat before continuing.",
    "Mood and funny": "Focus mainly on mood and motivation. If I look sad or demotivated, add something kind and funny.",
    "Sleep and recovery": "Focus mainly on tiredness, recovery, and whether I should prioritize sleep tonight.",
    "Gentle fitness": "Focus mainly on gentle sustainable exercise, easy pace, consistency, and recovery without body-shaming.",
    "Full detailed coach": "Give a more detailed coach recommendation covering movement, food, water, mood, rest, and sleep.",
    "Custom": "",
}


def preview_image(uploaded_file, max_width: int = PREVIEW_MAX_WIDTH) -> Image.Image | None:
    try:
        image = Image.open(uploaded_file)
        image.thumbnail((max_width, max_width), Image.Resampling.LANCZOS)
        return image.copy()
    except Exception:
        return None
    finally:
        uploaded_file.seek(0)


def render_score(label: str, value: int) -> None:
    st.caption(f"{label}: {value}/10")
    st.progress(max(0, min(value, 10)) / 10)


def render_prescription_item(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="prescription-row">
            <span class="prescription-label">{label}</span>
            <span class="prescription-value">{value}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_card(analysis: dict[str, object]) -> None:
    scores = analysis.get("scores") if isinstance(analysis.get("scores"), dict) else {}
    badges = analysis.get("badges") if isinstance(analysis.get("badges"), list) else []
    tips = analysis.get("tips") if isinstance(analysis.get("tips"), list) else []
    prescription = analysis.get("prescription") if isinstance(analysis.get("prescription"), dict) else {}
    adventure_card = analysis.get("adventure_card") if isinstance(analysis.get("adventure_card"), dict) else {}
    mode = str(analysis.get("mode") or "")
    summary = str(analysis.get("summary") or "")
    next_step = str(analysis.get("next_step") or "")
    challenge = str(analysis.get("challenge") or "")
    killer_insight = str(analysis.get("killer_insight") or "")
    share_text = str(
        adventure_card.get("share_text")
        or analysis.get("share_text")
        or summary
    )

    creativity = int(scores.get("creativity", 5))
    energy = int(scores.get("energy", 5))
    focus = int(scores.get("focus", 5))

    st.markdown(
        """
        <style>
        .coach-card {
            border: 1px solid #d7eadf;
            border-radius: 14px;
            padding: 18px;
            background: linear-gradient(180deg, #f7fff9 0%, #eefbf3 100%);
            box-shadow: 0 6px 18px rgba(29, 94, 54, 0.08);
            margin-top: 16px;
        }
        .coach-title {
            color: #143d2a;
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .coach-summary {
            color: #24513a;
            font-size: 1rem;
            line-height: 1.45;
            margin-bottom: 12px;
        }
        .badge {
            display: inline-block;
            background: #dff7e8;
            color: #195b38;
            border: 1px solid #bdeacb;
            border-radius: 999px;
            padding: 4px 10px;
            margin: 2px 4px 8px 0;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .mini-card, .prescription-card {
            border-radius: 12px;
            padding: 12px;
            background: #ffffff;
            border: 1px solid #e1efe6;
            margin-top: 10px;
        }
        .prescription-row {
            display: flex;
            justify-content: space-between;
            gap: 14px;
            padding: 8px 0;
            border-bottom: 1px solid #edf5ef;
        }
        .prescription-row:last-child { border-bottom: 0; }
        .prescription-label {
            min-width: 72px;
            color: #1d5b38;
            font-weight: 700;
        }
        .prescription-value {
            color: #2c3f34;
            text-align: right;
        }
        .adventure-card {
            border-radius: 14px;
            padding: 16px;
            background: linear-gradient(135deg, #173d2b 0%, #246d45 100%);
            color: #ffffff;
            margin-top: 12px;
        }
        .adventure-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 4px;
        }
        .adventure-subtitle {
            color: #e9fff0;
            line-height: 1.45;
            margin-bottom: 10px;
        }
        .adventure-vibe {
            display: inline-block;
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.28);
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .killer-card {
            border-radius: 12px;
            padding: 14px;
            background: #fff7dc;
            border: 1px solid #f3d46a;
            color: #4b3810;
            margin-top: 12px;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="coach-card">', unsafe_allow_html=True)
    st.markdown('<div class="coach-title">VendyGoScan Coach</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="coach-summary">{summary}</div>', unsafe_allow_html=True)

    badge_values = [mode, *badges] if mode else badges
    if badge_values:
        st.markdown(
            "".join(f'<span class="badge">{badge}</span>' for badge in badge_values if badge),
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        render_score("Creativity", creativity)
    with col2:
        render_score("Energy", energy)
    with col3:
        render_score("Focus", focus)

    st.markdown('<div class="prescription-card">', unsafe_allow_html=True)
    st.markdown("**Prescription**")
    render_prescription_item("Water", str(prescription.get("water") or "Daj si pár dúškov vody."))
    render_prescription_item("Food", str(prescription.get("food") or "Daj si niečo malé podľa energie."))
    render_prescription_item("Pace", str(prescription.get("pace") or "Drž ľahké tempo."))
    render_prescription_item("Rest", str(prescription.get("rest") or "Pri únave si daj krátku pauzu."))
    render_prescription_item("Sleep", str(prescription.get("sleep") or "Večer dopraj telu spánok."))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="mini-card">', unsafe_allow_html=True)
    st.markdown("**Tips**")
    for tip in tips:
        st.markdown(f"- {tip}")
    st.markdown("</div>", unsafe_allow_html=True)

    action_col, challenge_col = st.columns(2)
    with action_col:
        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
        st.markdown("**Next step**")
        st.write(next_step)
        st.markdown("</div>", unsafe_allow_html=True)
    with challenge_col:
        st.markdown('<div class="mini-card">', unsafe_allow_html=True)
        st.markdown("**Challenge**")
        st.write(challenge)
        st.markdown("</div>", unsafe_allow_html=True)

    if killer_insight:
        st.markdown(f'<div class="killer-card">🧠 {killer_insight}</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="adventure-card">
            <div class="adventure-title">{adventure_card.get("title") or "Adventure Check"}</div>
            <div class="adventure-subtitle">{adventure_card.get("subtitle") or summary}</div>
            <span class="adventure-vibe">{adventure_card.get("vibe") or mode or "Coach vibe"}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        "Share adventure card",
        data=share_text,
        file_name="vendygoscan-adventure-card.txt",
        mime="text/plain",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def offline_analysis(api_url: str, exc: requests.RequestException) -> dict[str, object]:
    return {
        "mode": "During hike",
        "summary": "Backend alebo model teraz neodpovedá, ale panika nie je tréningový plán.",
        "scores": {"creativity": 4, "energy": 4, "focus": 5},
        "badges": ["Offline", "Skús znova"],
        "tips": [
            f"API endpoint: {api_url}",
            f"Detail chyby: {exc}",
            "Na Renderi má API endpoint zostať prázdny v env alebo byť http://127.0.0.1:8000/analyze.",
        ],
        "prescription": {
            "water": "Daj si vodu, kým to opravíme.",
            "food": "Ak si hladný, malý snack je povolený debugging.",
            "pace": "Technické tempo: pomaly a pokojne.",
            "rest": "Daj si krátky reset.",
            "sleep": "Nenechaj deploy pokaziť spánok.",
        },
        "next_step": "Skontroluj Render logs a redeployni posledný commit.",
        "challenge": "30-sekundový reset: narovnaj sa a urob tri pokojné nádychy.",
        "killer_insight": "Ak máš spraviť len jednu vec: pozri Render logs, či backend hlási 'FastAPI backend is ready.'",
        "share_text": "VendyGoScan je dočasne offline. Skúsim znova.",
        "adventure_card": {
            "title": "Offline Adventure Check",
            "subtitle": "Tréner si práve šnuruje topánky v cloude.",
            "vibe": "Render check",
            "share_text": "VendyGoScan je dočasne offline. Skúsim znova.",
        },
    }


st.set_page_config(page_title="VendyGoScan", page_icon="V", layout="centered")
st.title("VendyGoScan")

with st.expander("Settings", expanded=False):
    api_url = st.text_input("API endpoint", value=os.getenv("VENDYGOSCAN_API_URL", DEFAULT_API_URL))
    preset_label = st.selectbox(
        "Extra instruction",
        options=list(PROMPT_PRESETS.keys()),
    )
    custom_prompt = ""
    if preset_label == "Custom":
        custom_prompt = st.text_input(
            "Custom instruction",
            value="",
            placeholder="e.g. Focus on sleep and recovery.",
        )

selected_mode = st.selectbox(
    "Activity mode",
    options=ACTIVITY_MODES,
    index=ACTIVITY_MODES.index("During hike"),
)

uploaded_image = st.file_uploader(
    "Upload photo",
    type=["jpg", "jpeg", "png", "webp", "heic", "heif"],
)

if uploaded_image:
    preview = preview_image(uploaded_image)
    if preview:
        st.image(preview, width=min(preview.width, PREVIEW_MAX_WIDTH))
    else:
        st.info("Photo selected. Preview may not show in the browser, but analysis can run.")

analyze = st.button("Analyze", type="primary", disabled=uploaded_image is None, use_container_width=True)
if analyze and uploaded_image:
    files = {"image": (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)}
    prompt_parts = [PROMPT_PRESETS[preset_label], custom_prompt.strip()]
    combined_prompt = "\n".join(part for part in prompt_parts if part)
    data = {"prompt": combined_prompt, "mode": selected_mode}
    with st.spinner("Coach is checking the photo..."):
        try:
            response = requests.post(api_url, files=files, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()["result"]
            if isinstance(result, dict):
                render_analysis_card(result)
            else:
                render_analysis_card(
                    {
                        "mode": selected_mode,
                        "summary": str(result),
                        "scores": {"creativity": 5, "energy": 5, "focus": 5},
                        "badges": ["Coach note"],
                        "tips": [str(result)],
                        "prescription": {
                            "water": "Daj si pár dúškov vody.",
                            "food": "Daj si niečo malé podľa energie.",
                            "pace": "Drž ľahké tempo.",
                            "rest": "Pri únave si daj krátku pauzu.",
                            "sleep": "Večer dopraj telu spánok.",
                        },
                        "next_step": "Skús ďalšiu fotku alebo pridaj inštrukciu v Settings.",
                        "challenge": "Mini výzva: 10 drepov alebo pohár vody. Vyber si múdro.",
                        "killer_insight": "Ak máš spraviť len jednu vec: daj si vodu a skús lepšiu fotku.",
                        "share_text": str(result),
                        "adventure_card": {
                            "title": "Adventure Check",
                            "subtitle": str(result),
                            "vibe": selected_mode,
                            "share_text": str(result),
                        },
                    }
                )
        except requests.RequestException as exc:
            render_analysis_card(offline_analysis(api_url, exc))
