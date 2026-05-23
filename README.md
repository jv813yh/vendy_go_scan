# VendyGoScan

Local MVP for uploading a hiker photo and receiving a short Slovak coach recommendation.

## Recommended Models And Tools

- Gemini model: `gemini-2.5-flash` for the MVP because it supports multimodal image workflows.
- Fallback model: `gemini-2.5-flash-lite`.
- Backend: FastAPI with `uvicorn`.
- Frontend: Streamlit for a simple upload form.
- Vision: OpenCV Haar cascades for a local hint only.
- Gemini receives the uploaded image directly; local vision output is only extra context.
- Prompt role: friendly outdoor trainer who checks visible face, posture, hands, legs, feet, mood, energy, clothing, environment, and overall readiness.
- Weekend deploy: Render Docker web service.

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

Available modes:

- `Before hike`
- `During hike`
- `After hike`
- `Gym / training`
- `Cottage / recovery`
- `Chill / ordinary day`

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
