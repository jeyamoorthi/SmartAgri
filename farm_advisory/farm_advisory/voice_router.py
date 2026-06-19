#!/usr/bin/env python3
"""
KisanAI Voice Router — FastAPI APIRouter module
================================================
Converted from standalone Flask server to a mountable FastAPI router.
All voice logic lives in index.py — this file only provides HTTP routes.
================================================
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import base64, os, sys
import subprocess
import tempfile

def convert_to_wav(audio_bytes: bytes) -> bytes:
    """
    Convert any browser audio format (WebM/Opus/MP4) to WAV 16kHz mono.
    """
    if not audio_bytes or len(audio_bytes) < 10:
        print(f"[⚠️ ffmpeg] Empty or too small audio input: {len(audio_bytes)} bytes")
        return audio_bytes

    print(f"[🔄 ffmpeg] Input size: {len(audio_bytes)} bytes")

    # Check if already WAV (RIFF header)
    if audio_bytes[:4] == b'RIFF':
        print("[🔄 ffmpeg] Input is already WAV, skipping conversion")
        return audio_bytes
    
    # Write input to temp file
    fd, tmp_in_path = tempfile.mkstemp(suffix='.webm')
    try:
        with os.fdopen(fd, 'wb') as tmp_in:
            tmp_in.write(audio_bytes)
            tmp_in.flush()
        
        tmp_out_path = tmp_in_path + ".wav"
        
        # Convert using ffmpeg: any format → WAV 16kHz mono PCM
        result = subprocess.run([
            'ffmpeg', '-y',
            '-i', tmp_in_path,
            '-ar', '16000',      # 16kHz sample rate
            '-ac', '1',          # mono
            '-f', 'wav',
            tmp_out_path
        ], capture_output=True, timeout=15)
        
        if result.returncode != 0:
            err = result.stderr.decode()
            print(f"[⚠️ ffmpeg] conversion failed: {err}")
            return audio_bytes
        
        with open(tmp_out_path, 'rb') as f:
            out_bytes = f.read()
            print(f"[✅ ffmpeg] Conversion successful: {len(out_bytes)} bytes")
            return out_bytes
    finally:
        # Cleanup temp files
        for path in [tmp_in_path, tmp_in_path + ".wav"]:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception as e:
                print(f"[⚠️ ffmpeg] Cleanup error: {e}")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Import from index.py backend ─────────────────────────────────────────────
try:
    from index import (
        bhashini_asr_translate,
        bhashini_translate_tts,
        bhashini_translate_text,
        ask_groq,
        calculate_bleu_score,
        generate_comprehensive_advisory,
        prefetch_services,
        LANGUAGES,
    )
    BACKEND_OK = True
    print("[✅ voice_router] index.py imported successfully — all voice functions ready")
except ImportError as e:
    print(f"[❌ voice_router] IMPORT FAILED: {e}")
    print("[❌ voice_router] This is why /api/voice/transcribe returns 500")
    BACKEND_OK = False
except Exception as e:
    print(f"[❌ voice_router] UNEXPECTED ERROR during import: {type(e).__name__}: {e}")
    BACKEND_OK = False

# ── Language metadata ─────────────────────────────────────────────────────────
NATIVE_NAMES = {
    "hi": "हिन्दी", "ta": "தமிழ்", "te": "తెలుగు", "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം", "bn": "বাংলা", "gu": "ગુજરાતી", "mr": "मराठी",
    "pa": "ਪੰਜਾਬੀ", "or": "ଓଡ଼ିଆ", "as": "অসমীয়া", "ur": "اردو",
}

# ── FastAPI Router ────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.get("/health")
async def health():
    return {"status": "ok", "backend": BACKEND_OK}


@router.get("/languages")
async def get_languages():
    langs = [
        {"id": k, "name": v[0], "code": v[1], "native": NATIVE_NAMES.get(v[1], v[0])}
        for k, v in LANGUAGES.items()
    ]
    return {"languages": langs}


@router.post("/prefetch")
async def prefetch(request: Request):
    data = await request.json()
    lang_code = data.get("lang_code", "hi")
    try:
        prefetch_services(lang_code)
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/transcribe")
async def api_transcribe(request: Request):
    if not BACKEND_OK:
        return JSONResponse(content={"error": "Voice backend not initialized"}, status_code=503)
    data = await request.json()
    audio_b64 = data.get("audio", "")
    lang_code = data.get("lang_code", "ta")
    try:
        audio_raw  = base64.b64decode(audio_b64)
        wav_bytes  = convert_to_wav(audio_raw)          # ← convert first
        transcribed, translated = bhashini_asr_translate(wav_bytes, lang_code)
        return {"transcribed": transcribed, "translated": translated}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[❌ /api/voice/transcribe] {type(e).__name__}: {e}\n{tb}")
        return JSONResponse(content={"error": str(e), "type": type(e).__name__}, status_code=500)

@router.post("/converse")
async def api_converse(request: Request):
    """
    Full pipeline in one call:
    audio (base64 WebM) → convert to WAV → ASR → translate → Groq → TTS
    Returns: { transcribed, translated, answer, answer_local, audio_b64 }
    """
    if not BACKEND_OK:
        return JSONResponse(
            content={"error": "Voice backend not initialized"},
            status_code=503
        )
    
    data = await request.json()
    audio_b64    = data.get("audio", "")
    lang_code    = data.get("lang_code", "ta")   # default Tamil for SmartAgri
    profile      = data.get("profile", None)
    is_comprehensive = data.get("is_comprehensive", False)

    try:
        # STEP 1: Decode and convert audio WebM → WAV 16kHz mono
        audio_raw = base64.b64decode(audio_b64)
        wav_bytes = convert_to_wav(audio_raw)

        # STEP 2: ASR + translate to English
        transcribed, english = bhashini_asr_translate(wav_bytes, lang_code)

        # STEP 3: Groq AI answer
        if profile and is_comprehensive:
            prompt = generate_comprehensive_advisory(profile, english)
        else:
            prompt = english
        answer_en = ask_groq(prompt, is_comprehensive=is_comprehensive)

        # STEP 4: Translate answer + TTS
        answer_local, audio_resp = bhashini_translate_tts(answer_en, lang_code)
        audio_out_b64 = base64.b64encode(audio_resp).decode()

        return {
            "transcribed":   transcribed,
            "translated":    english,
            "answer":        answer_en,
            "answer_local":  answer_local,
            "audio":         audio_out_b64,   # base64 WAV — frontend plays this
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[❌ /api/voice/converse] {type(e).__name__}: {e}\n{tb}")
        return JSONResponse(
            content={"error": str(e), "type": type(e).__name__},
            status_code=500
        )


@router.post("/ask")
async def api_ask(request: Request):
    if not BACKEND_OK:
        return JSONResponse(
            content={"error": "Voice backend failed to initialize. Check server logs for pyaudio/import errors."},
            status_code=503
        )
    data = await request.json()
    question         = data.get("question", "")
    profile          = data.get("profile")
    is_comprehensive = data.get("is_comprehensive", False)
    try:
        if profile and is_comprehensive:
            prompt = generate_comprehensive_advisory(profile, question)
        else:
            prompt = question
        answer = ask_groq(prompt, is_comprehensive=is_comprehensive)
        return {"answer": answer}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/speak")
async def api_speak(request: Request):
    if not BACKEND_OK:
        return JSONResponse(
            content={"error": "Voice backend failed to initialize. Check server logs for pyaudio/import errors."},
            status_code=503
        )
    data = await request.json()
    text_en   = data.get("text", "")
    lang_code = data.get("lang_code", "hi")
    try:
        translated_local, audio_bytes = bhashini_translate_tts(text_en, lang_code)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return {"translated": translated_local, "audio": audio_b64}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/bleu")
async def api_bleu(request: Request):
    data = await request.json()
    reference = data.get("reference", "")
    candidate = data.get("candidate", "")
    try:
        scores = calculate_bleu_score(reference, candidate)
        return scores
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/translate-field")
async def api_translate_field(request: Request):
    data = await request.json()
    text     = data.get("text", "")
    tgt_lang = data.get("tgt_lang", "hi")
    try:
        translated = bhashini_translate_text(text, "en", tgt_lang)
        return {"translated": translated}
    except Exception as e:
        return JSONResponse(content={"error": str(e), "translated": text}, status_code=200)  # graceful fallback


# ── Auto-prefetch on startup ──────────────────────────────────────────────────
import threading

def _startup_prefetch():
    """Warm up Bhashini service IDs for Tamil on server start."""
    if not BACKEND_OK:
        return
    try:
        print("[🔄 voice_router] Pre-warming Bhashini service IDs for Tamil...")
        # Call get_service_id directly (not prefetch_services — avoids spinner)
        from index import get_service_id
        for task, src, tgt in [
            ("asr",         "ta", None),
            ("translation", "ta", "en"),
            ("translation", "en", "ta"),
            ("tts",         "ta", None),
        ]:
            get_service_id(task, src, tgt)
        print("[✅ voice_router] Bhashini service IDs cached — voice ready")
    except Exception as e:
        print(f"[⚠️ voice_router] Prefetch failed (non-fatal): {e}")

# Run in background thread so it doesn't block server startup
threading.Thread(target=_startup_prefetch, daemon=True).start()
