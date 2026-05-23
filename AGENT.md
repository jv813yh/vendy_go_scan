# 🧠 AGENT.md — VendyGoScan

## 🎯 Project Goal

Build an AI-powered web application called **VendyGoScan** that:

- Takes an image of a person (hiker)
- Analyzes facial features using computer vision
- Uses an LLM (Gemini) to generate a recommendation

Final output example:

"Kamarát vyzerá unavene. Dajte si pauzu a doplňte vodu."

---

## 🏗️ Architecture (WAT Style)

### Workflows

#### analyze_hiker

Input: image  
Output: recommendation text  

Steps:
1. Call `vision_agent`
2. If confidence < threshold → return fallback
3. Call `reasoning_agent`
4. Return final recommendation

---

### Agents

#### vision_agent

Purpose: Extract features from image

Output format:

{
  "face_detected": true,
  "eyes": "open | closed",
  "emotion": "neutral | tired | happy",
  "confidence": 0.0-1.0
}

Rules:
- If no face detected → confidence = 0.0
- If unsure → lower confidence

---

#### reasoning_agent

Purpose: Convert features → actionable recommendation

Input:
- Output from vision_agent

Output:
- Short actionable text (1–2 sentences)
- Language: Slovak

---

### Tools

#### vision_tool

- Use MediaPipe OR lightweight face/emotion detection
- Must be fast and simple
- No need for perfect accuracy

---

#### gemini_tool

- Use Gemini API
- Input: structured JSON
- Output: text

---

## ⚙️ Tech Stack

- Backend: FastAPI
- Frontend: Streamlit
- LLM: Gemini API
- Language: Python

---

## 📁 Project Structure

vendygoscan/
│
├── app/
│   ├── main.py
│   ├── workflows/
│   │   └── analyze_hiker.py
│   ├── agents/
│   │   ├── vision_agent.py
│   │   └── reasoning_agent.py
│   ├── tools/
│   │   ├── vision_tool.py
│   │   └── gemini_tool.py
│
├── frontend/
│   └── streamlit_app.py
│
├── AGENT.md
├── GEMINI.md
└── requirements.txt

---

## 🧪 API Design

### POST /analyze

Input:
- image (multipart/form-data)

Output:

{
  "result": "Kamarát vyzerá unavene..."
}

---

## ⚠️ Fallback Logic

If:
- No face detected
- OR confidence < 0.6

Return:

"Neviem spoľahlivo vyhodnotiť stav. Skús inú fotku."

---

## 🎨 Frontend Requirements (Streamlit)

- Upload image
- Button: Analyze
- Show:
  - Image preview
  - Result text

---

## 🚀 Development Plan

1. Create project structure
2. Implement FastAPI endpoint
3. Implement vision_tool (basic version)
4. Implement vision_agent
5. Implement gemini_tool
6. Implement reasoning_agent
7. Connect workflow
8. Build Streamlit UI
9. Test with sample images

---

## 🧠 Decision Policy

- Prefer simple solutions over complex ones
- Prioritize working MVP over perfect accuracy
- Avoid overengineering

---

## ✅ Definition of Done

- User uploads image
- Gets recommendation within 3 seconds
- Works via ngrok on mobile