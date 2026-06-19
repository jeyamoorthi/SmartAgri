import os
import base64
import tempfile
import subprocess
import re
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from services.bhashini_service import (
    bhashini_asr_translate,
    bhashini_translate_tts,
    bhashini_translate_text,
    prefetch_services
)
from services.groq_service import ask_groq, parse_intent_and_advisory
from services.openai_service import parse_intent_openai
from services.bleu_service import calculate_bleu
from core.ai_gateway import AIGateway
from routers.auth import get_current_user, _user_to_response
from db.mongodb import market_trends_col, users_col
from services.agent_tools import (
    get_market_price,
    get_weather,
    get_schemes,
    get_crop_recommendation,
    diagnose_disease,
    get_natural_farming_guide
)
import asyncio

router = APIRouter(prefix="/api/voice-consultant", tags=["voice-consultant"])

NATIVE_NAMES = {
    "hi": "हिन्दी",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "bn": "বাংলা",
    "gu": "ગુજરાતી",
    "mr": "मराठी",
    "pa": "ਪੰਜਾਬੀ",
    "or": "ଓଡ଼ିଆ",
    "as": "অসমীয়া",
    "ur": "اردو",
}

LANGUAGES = {
    "1":  ("Hindi",      "hi"),
    "2":  ("Tamil",      "ta"),
    "3":  ("Telugu",     "te"),
    "4":  ("Kannada",    "kn"),
    "5":  ("Malayalam",  "ml"),
    "6":  ("Bengali",    "bn"),
    "7":  ("Gujarati",   "gu"),
    "8":  ("Marathi",    "mr"),
    "9":  ("Punjabi",    "pa"),
    "10": ("Odia",       "or"),
    "11": ("Assamese",   "as"),
    "12": ("Urdu",       "ur"),
}


def convert_to_wav(audio_bytes: bytes) -> bytes:
    """
    Attempt to convert audio WebM/MP4 to WAV 16kHz mono PCM using ffmpeg if available.
    Otherwise returns original bytes.
    """
    if not audio_bytes or len(audio_bytes) < 10:
        return audio_bytes

    if audio_bytes[:4] == b'RIFF':
        return audio_bytes  # Already WAV

    fd, tmp_in_path = tempfile.mkstemp(suffix='.webm')
    fd_out, tmp_out_path = tempfile.mkstemp(suffix='.wav')
    os.close(fd_out) # Let ffmpeg create it
    try:
        with os.fdopen(fd, 'wb') as tmp_in:
            tmp_in.write(audio_bytes)
            tmp_in.flush()
        
        # Call ffmpeg to convert to 16kHz mono wav
        cmd = ["ffmpeg", "-y", "-i", tmp_in_path, "-ar", "16000", "-ac", "1", tmp_out_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        with open(tmp_out_path, 'rb') as f_out:
            return f_out.read()
    except Exception as e:
        print(f"[WARNING][convert_to_wav] Conversion failed: {e}. Returning original bytes.")
        return audio_bytes
    finally:
        try:
            os.remove(tmp_in_path)
            os.remove(tmp_out_path)
        except Exception:
            pass


def detect_audio_mime(audio_bytes: bytes) -> str:
    if not audio_bytes:
        return "audio/wav"
    if audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff\xfb') or audio_bytes.startswith(b'\xff\xf3'):
        return "audio/mpeg"
    return "audio/wav"


@router.get("/languages")
async def api_languages():
    """Get list of supported languages."""
    res = []
    for key, (name, code) in LANGUAGES.items():
        res.append({
            "code": code,
            "name": name,
            "native": NATIVE_NAMES.get(code, name)
        })
    return {"languages": res}


@router.post("/prefetch")
async def api_prefetch(request: Request):
    """Pre-warm Bhashini pipeline services for a language."""
    data = await request.json()
    lang_code = data.get("lang_code", "ta")
    try:
        await prefetch_services(lang_code)
        return {"status": "success", "message": f"Pre-warmed services for {lang_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def prefetch_agent_context(query_en: str, profile: dict) -> dict:
    """
    Scans the query and determines which tools' contexts are relevant.
    Fetches them in parallel.
    """
    q = query_en.lower()
    
    # 1. Determine active crop
    crop = profile.get("crop", "tomato")
    # Scan query or last query memory for crop name overrides
    for c in ["tomato", "paddy", "rice", "cotton", "onion", "potato", "groundnut", "millet", "wheat"]:
        if c in q:
            crop = c
            break
    else:
        # Check conversational memory for crop context
        if profile.get("last_market_query"):
            crop = profile.get("last_market_query")
        elif profile.get("crop"):
            crop = profile.get("crop")
            
    # 2. Extract coordinates
    coords = profile.get("gps_coordinates") or {}
    lat = coords.get("lat", 13.0827)
    lon = coords.get("lng", 80.2707)
    
    # 3. Determine which tools to run
    tasks = {}
    
    # Always pre-fetch natural farming tips or specific ones if requested
    tasks["natural_farming"] = get_natural_farming_guide(q)
    
    if any(k in q for k in ["market", "price", "mandi", "cost", "sell", "buyer", "yesterday", "today", "tomorrow"]):
        tasks["market"] = get_market_price(crop)
        
    if any(k in q for k in ["weather", "rain", "temperature", "forecast", "climate", "wind", "humidity"]):
        tasks["weather"] = get_weather(lat, lon)
        
    if any(k in q for k in ["subsidy", "scheme", "government", "grant", "support", "benefit", "pm-kisan", "pkvy"]):
        tasks["subsidies"] = get_schemes(
            state=profile.get("state", "Tamil Nadu"),
            crop=crop,
            farm_size=float(profile.get("farm_size", 2.0))
        )
        
    if any(k in q for k in ["recommend", "recommendation", "plant", "grow", "next crop", "alternative"]):
        tasks["crop_recommendations"] = get_crop_recommendation(
            state=profile.get("state", "Tamil Nadu"),
            crop=crop,
            soil_type=profile.get("soil_type", "Red Soil"),
            farm_size=float(profile.get("farm_size", 2.0))
        )
        
    if any(k in q for k in ["disease", "pest", "bug", "remedy", "treatment", "blight", "spot", "borer"]):
        # Use last disease if query doesn't specify
        disease_name = profile.get("last_disease_query", "early blight")
        for d in ["early blight", "leaf spot", "stem borer"]:
            if d in q:
                disease_name = d
                break
        tasks["disease_diagnosis"] = diagnose_disease(disease_name, crop)
        
    # If tasks dict is empty, pre-fetch market and weather for default crop
    if not tasks or len(tasks) <= 1:
        tasks["market"] = get_market_price(crop)
        tasks["weather"] = get_weather(lat, lon)
        
    # Run in parallel
    keys = list(tasks.keys())
    results = await asyncio.gather(*tasks.values())
    
    return {keys[i]: results[i] for i in range(len(keys))}


@router.post("/converse")
async def api_converse(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Voice-first chat/advisory converse endpoint:
    ASR -> Translate -> Context Pre-fetching -> Tool-Based LLM Agent -> TTS -> Output Audio
    """
    data = await request.json()
    audio_b64 = data.get("audio", "")
    text_input = data.get("text", "")
    lang_code = data.get("lang_code", "ta")
    is_comprehensive = data.get("is_comprehensive", False)

    if not audio_b64 and not text_input:
        raise HTTPException(status_code=400, detail="Missing audio or text field")

    try:
        if text_input:
            transcribed = text_input
            if lang_code == "en":
                english = text_input
            else:
                try:
                    english = await bhashini_translate_text(text_input, lang_code, "en")
                except Exception as e_trans:
                    print(f"[WARNING] Translation of text_input failed: {e_trans}. Using original.")
                    english = text_input
        else:
            audio_raw = base64.b64decode(audio_b64)
            wav_bytes = convert_to_wav(audio_raw)
            transcribed, english = await bhashini_asr_translate(wav_bytes, lang_code)

        # ── Pre-fetch context based on query & user profile ──
        profile = _user_to_response(current_user)["farmer_profile"]
        tool_context = await prefetch_agent_context(english, profile)

        # ── Use Semantic Intent Parser via OpenAI first, fallback to Groq ──
        try:
            parsed = await parse_intent_openai(english, profile=profile, tool_context=tool_context)
        except Exception as e_openai:
            print(f"[WARNING] OpenAI parse_intent failed: {e_openai}. Falling back to Groq...")
            parsed = await parse_intent_and_advisory(english, profile=profile, tool_context=tool_context)

        intent = parsed.get("intent", "GeneralQuestion")
        action = parsed.get("action", "AnswerOnly")
        target = parsed.get("target")
        answer_en = parsed.get("answer", "I didn't quite catch that. Could you repeat?")
        tool_used = parsed.get("tool_used", "none")

        # Synthesize reply to local language audio
        translated_answer, audio_resp_bytes = await bhashini_translate_tts(answer_en, lang_code)
        audio_out_b64 = base64.b64encode(audio_resp_bytes).decode()
        mime_type = detect_audio_mime(audio_resp_bytes)

        # Translate suggest button label if present
        suggest_label = parsed.get("suggest_label")
        suggest_label_local = None
        if suggest_label:
            if lang_code == "en":
                suggest_label_local = suggest_label
            else:
                try:
                    suggest_label_local = await bhashini_translate_text(suggest_label, "en", lang_code)
                except Exception as e_lbl:
                    print(f"[WARNING] Failed to translate suggest label: {e_lbl}")
                    suggest_label_local = suggest_label

        # Map tool_used to tool_context key
        card_key = None
        if tool_used == "get_market_price":
            card_key = "market"
        elif tool_used == "get_weather":
            card_key = "weather"
        elif tool_used == "get_schemes":
            card_key = "subsidies"
        elif tool_used == "get_crop_recommendation":
            card_key = "crop_recommendations"
        elif tool_used == "diagnose_disease":
            card_key = "disease_diagnosis"
        elif tool_used == "get_natural_farming_guide":
            card_key = "natural_farming"

        data_card = tool_context.get(card_key) if card_key else None

        # ── Update conversational memory / session_context in MongoDB ──
        col = users_col()
        from bson import ObjectId
        set_fields = {}
        
        # Save last query states
        if tool_used == "get_market_price" and data_card:
            set_fields["last_market_query"] = data_card.get("crop", "tomato")
        elif tool_used == "diagnose_disease" and data_card:
            set_fields["last_disease_query"] = data_card.get("disease_name", "early blight")
        elif tool_used == "get_crop_recommendation" and data_card:
            set_fields["last_recommendation"] = data_card.get("crop_name", "groundnut")
            
        # Add to history
        history = current_user.get("session_context") or []
        history.append({"role": "user", "content": transcribed})
        history.append({"role": "assistant", "content": translated_answer})
        set_fields["session_context"] = history[-10:]  # keep last 10 messages
        
        await col.update_one({"_id": ObjectId(current_user["id"])}, {"$set": set_fields})

        response_payload = {
            "transcribed": transcribed,
            "translated": english,
            "answer": answer_en,
            "answer_local": translated_answer,
            "audio": audio_out_b64,
            "mime_type": mime_type,
            "intent": intent,
            "action": action,
            "target": target,
            "suggest_label": suggest_label_local,
            "data_card": data_card
        }

        return response_payload
    except Exception as e:
        safe_err = str(e).encode('ascii', 'backslashreplace').decode('ascii')
        print(f"[ERROR][voice-consultant /converse] {safe_err}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/ask")
async def api_ask(request: Request, current_user: dict = Depends(get_current_user)):
    """Text-based agricultural Q&A."""
    data = await request.json()
    question = data.get("question", "")
    is_comprehensive = data.get("is_comprehensive", False)
    
    try:
        answer = await AIGateway.get_advisory(question, is_comprehensive=is_comprehensive, profile=current_user)
        return {"answer": answer}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/speak")
async def api_speak(request: Request):
    """Text to regional language speech synthesis."""
    data = await request.json()
    text = data.get("text", "")
    lang_code = data.get("lang_code", "ta")
    
    try:
        translated_text, audio_bytes = await bhashini_translate_tts(text, lang_code)
        audio_out_b64 = base64.b64encode(audio_bytes).decode()
        mime_type = detect_audio_mime(audio_bytes)
        return {
            "translated": translated_text,
            "audio": audio_out_b64,
            "mime_type": mime_type
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/voice-diagnose")
async def api_voice_diagnose(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Voice + Image disease diagnosis:
    Image (base64) + Language code -> Gemini Vision identifies crop, disease, and organic remedies -> 
    translates remedies to local language -> TTS voice response + JSON details
    """
    data = await request.json()
    image_b64 = data.get("image", "")
    lang_code = data.get("lang_code", "ta")
    crop_context = data.get("crop_context", "")

    if not image_b64:
        raise HTTPException(status_code=400, detail="Missing image field")

    try:
        # 1. Diagnose via Gemini Vision in AI Gateway
        result = await AIGateway.diagnose_disease(image_b64, crop_context)
        
        # 2. Extract organic remedies and disease name
        disease_name = result.get("disease_name", "Unknown disease")
        organic_remedies = result.get("organic_remedies", [])
        
        # 3. Create English audio script
        remedies_text = " ".join(organic_remedies)
        advisory_en = f"The issue is identified as {disease_name} with {result.get('severity_level', 'moderate')} severity. Organic remedies: {remedies_text}"
        
        # 4. Translate and synthesize
        translated_advisory, audio_bytes = await bhashini_translate_tts(advisory_en, lang_code)
        audio_out_b64 = base64.b64encode(audio_bytes).decode()
        mime_type = detect_audio_mime(audio_bytes)
        
        # 5. Return JSON + audio
        result["translated_answer"] = translated_advisory
        result["audio"] = audio_out_b64
        result["mime_type"] = mime_type
        return result
    except Exception as e:
        safe_err = str(e).encode('ascii', 'backslashreplace').decode('ascii')
        print(f"[ERROR][voice-consultant /voice-diagnose] {safe_err}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/voice-market")
async def api_voice_market(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Voice market query:
    Audio (base64) + Language code -> transcribe -> get crop price trends -> NMT + TTS audio reply
    """
    data = await request.json()
    audio_b64 = data.get("audio", "")
    lang_code = data.get("lang_code", "ta")

    if not audio_b64:
        raise HTTPException(status_code=400, detail="Missing audio field")

    try:
        audio_raw = base64.b64decode(audio_b64)
        wav_bytes = convert_to_wav(audio_raw)
        transcribed, english = await bhashini_asr_translate(wav_bytes, lang_code)

        # Match crop name
        crop_match = re.search(r'\b(tomato|paddy|rice|potato|onion|cotton)\b', english.lower())
        crop = crop_match.group(1) if crop_match else "tomato"

        trend = await market_trends_col().find_one({"crop_name": {"$regex": crop, "$options": "i"}}, sort=[("timestamp", -1)])
        if trend:
            price = trend.get("price_per_quintal", 2500)
            status = trend.get("price_trend", "stable")
            rec = "Hold harvest" if status == "rising" else "Sell harvest on schedule"
            market_text = f"Mandi price for {crop} is {price} rupees per quintal. The trend is {status}. Recommendation: {rec}."
        else:
            market_text = f"Current mandi price for {crop} is 2800 rupees per quintal with stable trends. Recommend selling on schedule."

        # Translate + TTS
        translated_market, audio_bytes = await bhashini_translate_tts(market_text, lang_code)
        audio_out_b64 = base64.b64encode(audio_bytes).decode()
        mime_type = detect_audio_mime(audio_bytes)

        return {
            "transcribed": transcribed,
            "translated": english,
            "answer": market_text,
            "answer_local": translated_market,
            "audio": audio_out_b64,
            "mime_type": mime_type
        }
    except Exception as e:
        safe_err = str(e).encode('ascii', 'backslashreplace').decode('ascii')
        print(f"[ERROR][voice-consultant /voice-market] {safe_err}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/voice-weather")
async def api_voice_weather(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Voice weather query:
    Audio (base64) + Language code -> transcribe -> get weather -> forecast NMT + TTS audio reply
    """
    data = await request.json()
    audio_b64 = data.get("audio", "")
    lang_code = data.get("lang_code", "ta")
    lat = data.get("lat", 13.0827)
    lon = data.get("lon", 80.2707)

    if not audio_b64:
        raise HTTPException(status_code=400, detail="Missing audio field")

    try:
        audio_raw = base64.b64decode(audio_b64)
        wav_bytes = convert_to_wav(audio_raw)
        transcribed, english = await bhashini_asr_translate(wav_bytes, lang_code)

        from services.weather_service import fetch_weather_data
        w = await fetch_weather_data(lat, lon)
        weather_text = (
            f"The current weather is {w.get('condition', 'clear sky')} with a temperature of "
            f"{w.get('temp', 30.0)} degrees Celsius and {w.get('humidity', 65)}% humidity. "
            f"Farming recommendation: Proceed with natural composting and maintain soil mulching."
        )

        # Translate + TTS
        translated_weather, audio_bytes = await bhashini_translate_tts(weather_text, lang_code)
        audio_out_b64 = base64.b64encode(audio_bytes).decode()
        mime_type = detect_audio_mime(audio_bytes)

        return {
            "transcribed": transcribed,
            "translated": english,
            "answer": weather_text,
            "answer_local": translated_weather,
            "audio": audio_out_b64,
            "mime_type": mime_type
        }
    except Exception as e:
        safe_err = str(e).encode('ascii', 'backslashreplace').decode('ascii')
        print(f"[ERROR][voice-consultant /voice-weather] {safe_err}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/bleu")
async def api_bleu(request: Request):
    """Calculate BLEU score for translations."""
    data = await request.json()
    reference = data.get("reference", "")
    candidate = data.get("candidate", "")
    try:
        scores = calculate_bleu(reference, candidate)
        return scores
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/translate-field")
async def api_translate_field(request: Request):
    """Translate text fields."""
    data = await request.json()
    text = data.get("text", "")
    tgt_lang = data.get("tgt_lang", "ta")
    try:
        translated = await bhashini_translate_text(text, "en", tgt_lang)
        return {"translated": translated}
    except Exception as e:
        return {"translated": text, "error": str(e)}