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
- Local tunnel: ngrok with `ngrok http 8502`.
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

Render is a good weekend option because it can build this repo from the included `Dockerfile`. The container starts both services:

- FastAPI internally on `8000`
- Streamlit publicly on Render's `$PORT`

The public Render URL opens the Streamlit app. Streamlit calls FastAPI inside the same container.

### Option A: Simple Render Deploy

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

6. Deploy.

You do not need ngrok after Render deploys the app.

### Option B: GitHub Actions + Render Deploy Hook

The workflow at `.github/workflows/deploy.yml` builds a Docker image and pushes it to GitHub Container Registry.

To trigger Render from GitHub Actions:

1. Create a Render service.
2. Copy the Render deploy hook URL.
3. In GitHub repo settings, add a secret:

```text
RENDER_DEPLOY_HOOK=your-render-deploy-hook-url
```

4. Push to `main` or run the workflow manually.

For the fastest weekend path, use **Option A** first. Add the GitHub Actions deploy hook later if you want a more automated pipeline.

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

Response:

```json
{
  "result": {
    "summary": "Vyzeráš pripravený na ľahké tempo.",
    "scores": {
      "creativity": 7,
      "energy": 8,
      "focus": 6
    },
    "badges": ["Svieži ťah"],
    "tips": ["Daj si vodu.", "Drž ľahké tempo."],
    "next_step": "Napij sa a pokračuj pokojne.",
    "challenge": "10 minút bez šprintu.",
    "killer_insight": "Ak máš spraviť len jednu vec: napi sa vody pred pokračovaním.",
    "share_text": "VendyGoScan: energia 8/10."
  }
}
```
