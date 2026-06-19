"""
Voice service — HTTP wrapper around the farm_advisory Flask app (sidecar on port 5000).
Handles transcription (ASR), advisory Q&A, and TTS.
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

FARM_ADVISORY_URL = os.getenv("FARM_ADVISORY_URL", "http://localhost:5000")


async def transcribe_audio(audio_base64: str, lang_code: str = "ta") -> dict:
    """
    Send audio to farm_advisory /api/transcribe endpoint.
    Returns { transcribed: str, translated: str }
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{FARM_ADVISORY_URL}/api/transcribe",
                json={"audio": audio_base64, "lang_code": lang_code},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"⚠ Voice transcription error: {e}")
        return {"transcribed": "", "translated": "", "error": str(e)}


async def ask_advisory(question: str, profile: dict = None, is_comprehensive: bool = False) -> dict:
    """
    Send question to farm_advisory /api/ask endpoint.
    Optionally include farmer profile for comprehensive advisory.
    Returns { answer: str }
    """
    try:
        payload = {
            "question": question,
            "is_comprehensive": is_comprehensive,
        }
        if profile:
            payload["profile"] = profile

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{FARM_ADVISORY_URL}/api/ask",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"⚠ Voice advisory error: {e}")
        return {"answer": f"Sorry, I couldn't process that right now. Error: {str(e)}"}


async def text_to_speech(text: str, lang_code: str = "ta") -> dict:
    """
    Send text to farm_advisory /api/speak endpoint for TTS.
    Returns { translated: str, audio: str (base64) }
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{FARM_ADVISORY_URL}/api/speak",
                json={"text": text, "lang_code": lang_code},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"⚠ TTS error: {e}")
        return {"translated": text, "audio": "", "error": str(e)}


async def health_check() -> bool:
    """Check if farm_advisory service is healthy."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{FARM_ADVISORY_URL}/api/health")
            return resp.status_code == 200
    except Exception:
        return False
