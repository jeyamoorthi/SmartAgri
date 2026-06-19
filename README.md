# 🌾 SmartAgri — AI-Powered Multilingual Farmer Voice Assistant & Precision Dashboard

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/jeyamoorthi/SmartAgri)

SmartAgri is a modern, voice-first agricultural consultant designed specifically for Indian farmers. The application is built around the philosophy of **"Answer First, Navigate Second"**, prioritizing immediate, context-aware speech feedback in regional languages while providing rich, optional data cards and navigation on the supporting dashboard.

---

## 🚀 Key Features

*   **🎤 Multilingual Voice Consultant (ASR, NMT & TTS)**:
    *   Powered by MeitY's **Bhashini** APIs (with seamless automatic fallbacks to **Google Gemini** & **gTTS**).
    *   Supports 12 major Indian languages (including Tamil, Hindi, Telugu, Kannada, Marathi, Bengali, and Gujarati).
    *   Ensures zero English leakage when a regional language is active.
*   **🧠 Farmer Context Engine (Conversational Memory)**:
    *   Maintains a persistent `farmer_profile` (including location, soil type/pH, crop type/stage, and budget).
    *   Features conversational memory (understands follow-up queries like *"What is tomato price today?"* followed by *"What about rainfed crop recommendations for my farm?"*).
*   **📊 Dynamic Subsidies Eligibility Calculator**:
    *   Calculates eligible government schemes (e.g. PM-Kisan, PKVY) based on farm size, crop type, and state.
    *   Provides active application URLs and specific document checklists.
*   **🌱 Crop Recommendation Engine**:
    *   Recommends optimal regional crops based on soil type, pH levels, and regional climates.
*   **🍂 Disease Diagnosis Scan & Voice Response**:
    *   Identifies crop diseases from images (Gemini Vision) and immediately reads out organic remedies and prevention plans via voice.
*   **☁️ Weather & Mandi (Market) Price Cards**:
    *   Queries live regional mandi prices and local weather forecasts.

---

## 🛠️ Technology Stack

*   **Backend**: FastAPI, Uvicorn, Motor (async MongoDB driver), Pydantic, APScheduler.
*   **Frontend**: React (Vite), React Router DOM, TailwindCSS, Lucide-React, Recharts.
*   **LLMs & AI**: Groq (Llama 3.3 70B), Google Gemini (Advisory & Vision), MeitY Bhashini API.

---

## 📂 Project Structure

```text
SmartAgri/
├── backend/                  # FastAPI Application
│   ├── core/                 # AI Gateway & core orchestration
│   ├── db/                   # MongoDB connection & seeding
│   ├── models/               # Pydantic schemas
│   ├── routers/              # API endpoints (Auth, Advisory, Voice, Subsidies, etc.)
│   ├── services/             # Bhashini, Groq, Gemini, and Weather integrations
│   └── main.py               # Backend Entrypoint
├── frontend/                 # Vite React Application
│   ├── src/
│   │   ├── api/              # Axios wrappers
│   │   ├── components/       # UI Cards (Market, Weather, Subsidies, etc.)
│   │   ├── context/          # Language & Auth contexts
│   │   └── pages/            # Home, Login, SignUp, VoiceConsultant
├── render.yaml               # Render Deployment Blueprint
└── docker-compose.yml        # Local docker setup
```

---

## 💻 Local Setup

### Prerequisite Services
Ensure you have **MongoDB** running locally at `mongodb://localhost:27017`.

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
3. Fill in your API keys:
   ```env
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=smartagri_db
   GEMINI_API_KEY=your_gemini_key
   GROQ_API_KEY=your_groq_key
   BHASHINI_USER_ID=your_bhashini_user_id
   BHASHINI_API_KEY=your_bhashini_api_key
   BHASHINI_AUTH=your_bhashini_auth_token
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the backend server:
   ```bash
   python main.py
   ```
   *The API will be available at `http://localhost:8001`.*

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Create a `.env` file:
   ```env
   VITE_API_URL=http://localhost:8001
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Run the React development server:
   ```bash
   npm run dev
   ```
   *The dashboard will be available at `http://localhost:3000`.*

---

## ☁️ Cloud Deployment (Render Blueprint)

This project is pre-configured with a Render Blueprint (`render.yaml`). To deploy both frontend and backend instantly:

1. Connect your GitHub repository to [Render](https://dashboard.render.com).
2. Choose **New +** > **Blueprint**.
3. Render will automatically detect the FastAPI backend and Vite static site.
4. Input your environment variables (`MONGODB_URI`, `GROQ_API_KEY`, `GEMINI_API_KEY`, and Bhashini keys) in the backend service configuration during setup, and click **Deploy**.
