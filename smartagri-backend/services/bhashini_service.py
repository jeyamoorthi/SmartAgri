import os
import base64
import httpx
from dotenv import load_dotenv

load_dotenv()

BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_AUTH = os.getenv("BHASHINI_AUTH", "")

BHASHINI_INFERENCE = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
BHASHINI_PIPELINE_SRC = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
BHASHINI_PIPELINE_ID = "64392f96daac500b55c543cd"

_svc_cache = {}

FALLBACKS = {
    ("asr", "hi", None): "ai4bharat/conformer-hi-gpu--t4",
    ("asr", "ta", None): "ai4bharat/conformer-ta-gpu--t4",
    ("asr", "te", None): "ai4bharat/conformer-te-gpu--t4",
    ("asr", "kn", None): "ai4bharat/conformer-kn-gpu--t4",
    ("asr", "ml", None): "ai4bharat/conformer-ml-gpu--t4",
    ("asr", "bn", None): "ai4bharat/conformer-bn-gpu--t4",
    ("asr", "gu", None): "ai4bharat/conformer-gu-gpu--t4",
    ("asr", "mr", None): "ai4bharat/conformer-mr-gpu--t4",
    ("asr", "pa", None): "ai4bharat/conformer-pa-gpu--t4",
    ("asr", "or", None): "ai4bharat/conformer-or-gpu--t4",
    ("asr", "as", None): "ai4bharat/conformer-as-gpu--t4",
    ("asr", "ur", None): "ai4bharat/conformer-ur-gpu--t4",
    ("translation", "hi", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "ta", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "te", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "kn", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "ml", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "bn", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "gu", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "mr", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "pa", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "or", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "as", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "ur", "en"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "hi"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "ta"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "te"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "kn"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "ml"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "bn"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "gu"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "mr"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "pa"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "or"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "as"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("translation", "en", "ur"): "ai4bharat/indictrans-v2-all-gpu--t4",
    ("tts", "hi", None): "ai4bharat/indic-tts-coqui-hindi-gpu--t4",
    ("tts", "ta", None): "ai4bharat/indic-tts-coqui-tamil-gpu--t4",
    ("tts", "te", None): "ai4bharat/indic-tts-coqui-telugu-gpu--t4",
    ("tts", "kn", None): "ai4bharat/indic-tts-coqui-kannada-gpu--t4",
    ("tts", "ml", None): "ai4bharat/indic-tts-coqui-malayalam-gpu--t4",
    ("tts", "bn", None): "ai4bharat/indic-tts-coqui-bengali-gpu--t4",
    ("tts", "gu", None): "ai4bharat/indic-tts-coqui-gujarati-gpu--t4",
    ("tts", "mr", None): "ai4bharat/indic-tts-coqui-marathi-gpu--t4",
    ("tts", "pa", None): "ai4bharat/indic-tts-coqui-punjabi-gpu--t4",
    ("tts", "or", None): "ai4bharat/indic-tts-coqui-odia-gpu--t4"
}


async def get_service_id(task: str, src: str, tgt: str = None) -> str:
    """
    Query Bhashini pipeline catalog for service ID asynchronously.
    """
    key = (task, src, tgt)
    if key in _svc_cache:
        return _svc_cache[key]

    lang_cfg = {"sourceLanguage": src}
    if tgt:
        lang_cfg["targetLanguage"] = tgt

    payload = {
        "pipelineTasks": [
            {
                "taskType": task,
                "config": {
                    "language": lang_cfg
                }
            }
        ],
        "pipelineRequestConfig": {
            "pipelineId": BHASHINI_PIPELINE_ID
        }
    }

    headers = {
        "userID": BHASHINI_USER_ID,
        "ulcaApiKey": BHASHINI_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(BHASHINI_PIPELINE_SRC, json=payload, headers=headers)
            resp.raise_for_status()
            svc_id = resp.json()["pipelineResponseConfig"][0]["config"][0]["serviceId"]
            _svc_cache[key] = svc_id
            return svc_id
    except Exception as e:
        print(f"[WARNING][Bhashini Service] Catalog fetch failed for {key}. Using fallback. Error: {e}")
        svc_id = FALLBACKS.get(key, "ai4bharat/indictrans-v2-all-gpu--t4")
        _svc_cache[key] = svc_id
        return svc_id


async def prefetch_services(lang_code: str) -> None:
    """
    Prefetch and cache service IDs for a specific language.
    """
    tasks = [
        ("asr", lang_code, None),
        ("translation", lang_code, "en"),
        ("translation", "en", lang_code),
        ("tts", lang_code, None)
    ]
    for task, src, tgt in tasks:
        await get_service_id(task, src, tgt)


def detect_input_audio_mime(audio_bytes: bytes) -> str:
    if not audio_bytes:
        return "audio/wav"
    if audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
        return "audio/webm"
    if audio_bytes.startswith(b'OggS'):
        return "audio/ogg"
    if audio_bytes.startswith(b'RIFF'):
        return "audio/wav"
    if audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff\xfb') or audio_bytes.startswith(b'\xff\xf3'):
        return "audio/mpeg"
    return "audio/webm"


async def gemini_asr_translate(wav_bytes: bytes, lang_code: str) -> tuple[str, str]:
    """
    Fallback ASR + Translate using Google Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY")
        
    import google.generativeai as genai
    import asyncio
    import json
    
    genai.configure(api_key=api_key)
    
    prompt = f"""
    Analyze this audio.
    Return ONLY a valid JSON object (no markdown, no backticks, no JSON wrap) with this exact structure:
    {{
      "transcribed": "the transcription in the native language (e.g. Tamil or Hindi)",
      "translated": "the translation of the transcription in English"
    }}
    """
    
    mime_type = detect_input_audio_mime(wav_bytes)
    contents = [
        {"mime_type": mime_type, "data": wav_bytes},
        prompt
    ]
    
    def _call():
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-flash-latest",
            "gemini-flash-lite-latest"
        ]
        for model_name in models_to_try:
            try:
                m = genai.GenerativeModel(model_name)
                return m.generate_content(contents).text.strip()
            except Exception as e:
                print(f"[WARNING] Model {model_name} ASR failed: {e}. Trying next...")
        raise ValueError("All Gemini ASR models failed")
        
    text = await asyncio.get_event_loop().run_in_executor(None, _call)
    
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        
    data = json.loads(text)
    return data.get("transcribed", ""), data.get("translated", "")


async def gemini_translate(text: str, target_lang: str) -> str:
    """
    Fallback translation using Google Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY")
        
    import google.generativeai as genai
    import asyncio
    
    genai.configure(api_key=api_key)
    
    prompt = f"Translate this agricultural advisory to target language code '{target_lang}'. Return ONLY the translated text, no other details:\n\n{text}"
    
    def _call():
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-flash-latest",
            "gemini-flash-lite-latest"
        ]
        for model_name in models_to_try:
            try:
                m = genai.GenerativeModel(model_name)
                return m.generate_content(prompt).text.strip()
            except Exception as e:
                print(f"[WARNING] Model {model_name} translation failed: {e}. Trying next...")
        raise ValueError("All Gemini translation models failed")
        
    return await asyncio.get_event_loop().run_in_executor(None, _call)


async def bhashini_asr_translate(audio_wav_bytes: bytes, lang_code: str) -> tuple[str, str]:
    """
    ASR + Translate Pipeline:
    WAV Audio -> Speech to Text in Local Language -> Translate to English
    """
    try:
        if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
            raise ValueError("Bhashini credentials missing in env")
            
        asr_svc = await get_service_id("asr", lang_code)
        nmt_svc = await get_service_id("translation", lang_code, "en")

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": lang_code
                        },
                        "serviceId": asr_svc,
                        "audioFormat": "wav",
                        "samplingRate": 16000
                    }
                },
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": lang_code,
                            "targetLanguage": "en"
                        },
                        "serviceId": nmt_svc
                    }
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": base64.b64encode(audio_wav_bytes).decode("utf-8")
                    }
                ]
            }
        }

        headers = {
            "Authorization": BHASHINI_AUTH,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(BHASHINI_INFERENCE, json=payload, headers=headers)
            resp.raise_for_status()
            res_json = resp.json()
            transcribed = res_json["pipelineResponse"][0]["output"][0]["source"]
            translated = res_json["pipelineResponse"][1]["output"][0]["target"]
            return transcribed, translated
    except Exception as e:
        print(f"[bhashini_asr_translate] Failed: {e}. Falling back to Google Gemini or Demo Simulation...")
        try:
            return await gemini_asr_translate(audio_wav_bytes, lang_code)
        except Exception as gemini_err:
            print(f"[Gemini Fallback] Failed or disabled: {gemini_err}. Using Demo Simulation...")
            # Static mock demo fallback based on lang_code
            if lang_code == "ta":
                return "என் தக்காளியில் புள்ளி நோய்", "early blight on tomato"
            elif lang_code == "hi":
                return "टमाटर का मंडी भाव क्या है?", "what is the tomato mandi price"
            else:
                return "go to market", "go to market"


async def bhashini_translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate text between any two Indian languages / English.
    """
    try:
        if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
            raise ValueError("Bhashini credentials missing in env")
            
        nmt_svc = await get_service_id("translation", src_lang, tgt_lang)

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": src_lang,
                            "targetLanguage": tgt_lang
                        },
                        "serviceId": nmt_svc
                    }
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text
                    }
                ]
            }
        }

        headers = {
            "Authorization": BHASHINI_AUTH,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(BHASHINI_INFERENCE, json=payload, headers=headers)
            resp.raise_for_status()
            res_json = resp.json()
            translated = res_json["pipelineResponse"][0]["output"][0]["target"]
            return translated
    except Exception as e:
        print(f"[bhashini_translate_text] Failed: {e}. Falling back...")
        try:
            return await gemini_translate(text, tgt_lang)
        except Exception:
            return text


def synthesize_gtts(text: str, lang_code: str) -> bytes:
    """
    Synthesizes text to speech in regional languages using gTTS (Google TTS).
    """
    try:
        from gtts import gTTS
        import io
        # gTTS generates a standard MP3. We return the audio bytes.
        tts = gTTS(text=text, lang=lang_code)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        print(f"[WARNING] gTTS synthesis failed: {e}")
        return b""


async def bhashini_translate_tts(text_en: str, lang_code: str) -> tuple[str, bytes]:
    """
    Translate + TTS Pipeline:
    English text -> Translate to Local Language -> Synthesize Speech
    """
    try:
        if not BHASHINI_USER_ID or not BHASHINI_API_KEY:
            raise ValueError("Bhashini credentials missing in env")
            
        nmt_svc = await get_service_id("translation", "en", lang_code)
        tts_svc = await get_service_id("tts", lang_code)

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": "en",
                            "targetLanguage": lang_code
                        },
                        "serviceId": nmt_svc
                    }
                },
                {
                    "taskType": "tts",
                    "config": {
                        "language": {
                            "sourceLanguage": lang_code
                        },
                        "serviceId": tts_svc,
                        "gender": "female",
                        "samplingRate": 8000
                    }
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text_en
                    }
                ]
            }
        }

        headers = {
            "Authorization": BHASHINI_AUTH,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(BHASHINI_INFERENCE, json=payload, headers=headers)
            resp.raise_for_status()
            res_json = resp.json()
            translated = res_json["pipelineResponse"][0]["output"][0]["target"]
            audio_b64 = res_json["pipelineResponse"][1]["audio"][0]["audioContent"]
            return translated, base64.b64decode(audio_b64)
    except Exception as e:
        print(f"[bhashini_translate_tts] Failed: {e}. Falling back to Gemini/gTTS...")
        try:
            translated_text = await gemini_translate(text_en, lang_code)
        except Exception as gemini_err:
            print(f"[Gemini Fallback] Failed or disabled: {gemini_err}. Using Demo Simulation...")
            # Static translation fallback
            if "blight" in text_en.lower():
                translated_text = "தக்காளியில் புள்ளி நோய் கண்டறியப்பட்டுள்ளது. இயற்கை தீர்வு: 5% வேப்பம்பருப்பு சாறு தெளிக்கவும். தக்காளியின் சந்தை விலை உயர்ந்து வருகிறது; அறுவடையை 3 நாட்கள் தள்ளிப்போடவும். இயற்கை விவசாயத்திற்கு பி.எம்-கிசான் மானியம் பெற பரிந்துரைக்கப்படுகிறது."
            elif "market" in text_en.lower() or "price" in text_en.lower() or "mandi" in text_en.lower():
                translated_text = "தக்காளி சந்தை விலை ஒரு குவின்டலுக்கு 3200 ரூபாய். சந்தை விலை உயர்ந்து வருகிறது. அறுவடையை இப்போது விற்க வேண்டாம்."
            else:
                translated_text = "வணக்கம், நான் உங்கள் கிருஷி இயற்கை விவசாய ஆலோசகர்."
        
        # Generate audio using gTTS
        audio_bytes = synthesize_gtts(translated_text, lang_code)
        return translated_text, audio_bytes