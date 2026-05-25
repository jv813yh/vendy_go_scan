# VendyGoScan

What can you build in a 3-hour window before going hiking?

That was the starting point for VendyGoScan. On a Saturday morning, before a hike, I had a little time to experiment on the PC and wanted to build something we could actually use later that day on the trail. The result was a small AI coach app: upload a photo, choose the current activity mode, and get a practical Slovak recommendation for what to do next.

VendyGoScan is intentionally simple, but it tries to be more than a generic "upload photo to AI" demo. It wraps the model output into a coach-style product experience with activity modes, scores, practical prescriptions, challenges, and one clear next action.

## What It Does

- Upload a photo from desktop or mobile.
- Choose an activity mode:
  - `Before hike`
  - `During hike`
  - `After hike`
  - `Gym / training`
  - `Cottage / recovery`
  - `Chill / ordinary day`
- Get a coach-style result in Slovak:
  - summary
  - creativity / energy / focus scores
  - badges
  - practical tips
  - water / food / pace / rest / sleep prescription
  - next step
  - small challenge
  - "if you only do one thing" insight
  - shareable adventure card

## LinkedIn Story Angle

This project is also a small build-in-public story:

> What can you build in 3 hours before a hike?
>
> I had some time on Saturday morning, wanted to try a few AI/product ideas, and decided to build something we could actually use on the hike.
>
> So I built VendyGoScan: a small photo-based outdoor coach.
>
> The first version worked on desktop. Then mobile uploads caused issues. Then Render deployment needed fixes. Then image compression and model fallback became necessary.
>
> The lesson: AI makes the prototype fast, but real usage makes the product real.

Useful screenshots for a LinkedIn post:

- Upload screen with activity mode selector.
- Photo preview.
- Coach result card.
- Prescription section.
- Adventure card / killer insight.
- Render/mobile view.

## Stack

- Gemini model: `gemini-2.5-flash`.
- Fallback model: `gemini-2.5-flash-lite`.
- Backend: FastAPI with `uvicorn`.
- Frontend: Streamlit.
- Vision: OpenCV Haar cascades for a local hint only.
- Image handling: Pillow and `pillow-heif` for mobile photo support.
- Deployment: Docker web service on Render.

Gemini receives the uploaded image directly. Local vision output is only extra context.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` and set:

```env
GEMINI_API_KEY=your-real-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=gemini-2.5-flash-lite
VENDYGOSCAN_API_URL=http://localhost:8000/analyze
VENDYGOSCAN_LOG_DIR=logs
```

Keep the real key only in `.env`. Gemini responses are logged to `logs/gemini_responses.jsonl`.

## Run Locally

Backend:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
.\.venv\Scripts\Activate.ps1
$env:VENDYGOSCAN_API_URL="http://localhost:8000/analyze"
streamlit run frontend/streamlit_app.py --server.address 0.0.0.0 --server.port 8502
```

ngrok for mobile frontend testing:

```powershell
ngrok http 8502
```

Flow:

```text
Phone -> ngrok -> Streamlit :8502 -> FastAPI :8000 -> Gemini
```

## Deploy To Render

Render builds this repo from the included `Dockerfile`. The container starts both services:

- FastAPI internally on `8000`
- Streamlit publicly on Render's `$PORT`

The public Render URL opens the Streamlit app. Streamlit calls FastAPI inside the same container.

You do **not** start the backend locally when using Render. Render runs the Docker container, and `scripts/start_render.sh` starts both FastAPI and Streamlit inside that container.

### Simple Render Deploy

1. Push this repo to GitHub.
2. In Render, create a new **Web Service**.
3. Connect the GitHub repo.
4. Runtime: **Docker**.
5. Add environment variables:

```env
GEMINI_API_KEY=your-real-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=gemini-2.5-flash-lite
VENDYGOSCAN_LOG_DIR=logs
```

Do not set `VENDYGOSCAN_API_URL` on Render unless you are debugging. If you set it, use:

```env
VENDYGOSCAN_API_URL=http://127.0.0.1:8000/analyze
```

If the frontend opens but analysis says the backend is offline, open Render **Logs** and look for:

```text
FastAPI backend is ready.
Starting Streamlit frontend on port ...
```

## Docker Local Test

Build:

```powershell
docker build -t vendygoscan .
```

Run:

```powershell
docker run --rm -p 8502:8502 --env-file .env vendygoscan
```

Open:

```text
http://localhost:8502
```

## Mobile Notes

The app is meant to work from a phone. Mobile photos can be large or uploaded as HEIC/HEIF, so the frontend converts uploaded photos to a smaller JPEG before sending them to the backend:

- max side: `1280px`
- JPEG quality: `85`
- EXIF orientation is respected
- original preview is resized on the page

This avoids many Render/Gemini timeouts caused by huge phone images.

## Port Troubleshooting

If a port is already used by another process, find the owner in PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Replace `8000` with `8502` when checking the Streamlit frontend.

Show details about the owning process:

```powershell
Get-Process -Id <OwningProcess>
```

Stop that process:

```powershell
Stop-Process -Id <OwningProcess> -Force
```

Alternative with `netstat`:

```powershell
netstat -ano | findstr :8502
taskkill /PID <PID> /F
```

## API

`POST /analyze`

Multipart form fields:

- `image`: jpg, jpeg, png, webp, heic, or heif
- `prompt`: optional extra instruction for this photo
- `mode`: optional activity mode; default is `During hike`

Response:

```json
{
  "result": {
    "mode": "During hike",
    "summary": "Vyzeráš pripravený na ľahké tempo.",
    "scores": {
      "creativity": 7,
      "energy": 8,
      "focus": 6
    },
    "badges": ["Svieži ťah"],
    "tips": ["Daj si vodu.", "Drž ľahké tempo."],
    "prescription": {
      "water": "Daj si pár dúškov vody.",
      "food": "Ak energia padá, doplň niečo malé.",
      "pace": "Drž ľahké tempo.",
      "rest": "Pri únave si daj krátku pauzu.",
      "sleep": "Večer dopraj telu spánok."
    },
    "next_step": "Napij sa a pokračuj pokojne.",
    "challenge": "10 minút bez šprintu.",
    "killer_insight": "Ak máš spraviť len jednu vec: napi sa vody pred pokračovaním.",
    "share_text": "VendyGoScan: energia 8/10.",
    "adventure_card": {
      "title": "Trail Check",
      "subtitle": "Svieža energia na ľahké tempo.",
      "vibe": "During hike",
      "share_text": "VendyGoScan: energia 8/10."
    }
  }
}
```
