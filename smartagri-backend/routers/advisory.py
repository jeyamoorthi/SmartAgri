from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from db.mongodb import users_col, advisory_plans_col
from models.user import AdvisoryPlanRequest, VoiceChatRequest
from routers.auth import get_current_user
from services.gemini_service import generate_advisory_plan
from services.voice_service import transcribe_audio, ask_advisory, text_to_speech

router = APIRouter(prefix="/api/advisory", tags=["advisory"])

@router.post("/generate-plan")
async def generate_plan(
    req: AdvisoryPlanRequest = AdvisoryPlanRequest(),
    current_user: dict = Depends(get_current_user),
):
    """Generate a weekly advisory plan using Gemini AI."""
    user_id = str(current_user["_id"])
    
    profile = {
        "present_crop": current_user.get("present_crop") or "paddy",
        "present_crop_stage": current_user.get("present_crop_stage") or "vegetative",
        "land_acres": current_user.get("land_acres", 2),
        "gps_coordinates": current_user.get("gps_coordinates") or {},
        "past_crop": current_user.get("past_crop") or "",
        "past_disease": current_user.get("past_disease") or "",
        "soil_data": current_user.get("soil_data") or {},
        "weather_data": current_user.get("weather_data") or {},
        "include_sustainable": req.include_sustainable
    }
    
    plan = await generate_advisory_plan(profile)
    
    today = datetime.now(timezone.utc)
    week_start = today - timedelta(days=today.weekday())
    
    plan_doc = {
        "user_id": user_id,
        "week_start": week_start.strftime("%Y-%m-%d"),
        "irrigation_schedule": plan.get("irrigation_schedule", []),
        "pest_warnings": plan.get("pest_warnings", []),
        "harvest_plan": plan.get("harvest_plan", {}),
        "sustainable_tips": plan.get("sustainable_tips", []),
        "created_at": today.isoformat()
    }
    
    await advisory_plans_col().update_one(
        {"user_id": user_id, "week_start": plan_doc["week_start"]},
        {"$set": plan_doc},
        upsert=True
    )
    
    import asyncio
    from services.email_service import send_irrigation_reminder
    
    async def schedule_reminders():
        email = current_user.get("email", "")
        crop = current_user.get("present_crop") or "crop"
        for slot in plan.get("irrigation_schedule", []):
            try:
                await send_irrigation_reminder(email, crop, slot)
            except Exception as e:
                print(f"[WARNING] Email reminder scheduling error: {e}")
                
    asyncio.create_task(schedule_reminders())
    
    return {
        "status": "success",
        "plan": plan,
        "week_start": plan_doc["week_start"]
    }

@router.get("/current-plan")
async def get_current_plan(current_user: dict = Depends(get_current_user)):
    """Retrieve the current weekly plan for the user."""
    user_id = str(current_user["_id"])
    today = datetime.now(timezone.utc)
    week_start = today - timedelta(days=today.weekday())
    week_start_str = week_start.strftime("%Y-%m-%d")
    
    plan = await advisory_plans_col().find_one(
        {"user_id": user_id, "week_start": week_start_str},
        {"_id": 0}
    )
    if not plan:
        return {"status": "no_plan", "plan": None}
    return {"status": "success", "plan": plan}

@router.post("/voice-chat")
async def voice_chat(
    req: VoiceChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Pipeline: audio -> transcribe -> ask AI -> TTS response
    """
    transcription = await transcribe_audio(req.audio_base64, req.lang_code)
    if transcription.get("error"):
        raise HTTPException(status_code=500, detail=f"Transcription failed: {transcription['error']}")
        
    user_question = transcription.get("translated", transcription.get("transcribed", ""))
    if not user_question:
        return {
            "transcribed": "",
            "translated": "",
            "answer": "I couldn't hear you clearly. Please try again.",
            "audio": ""
        }
        
    profile = {
        "name": current_user.get("username", "Farmer"),
        "current_crop": current_user.get("present_crop") or "",
        "crop_stage": current_user.get("present_crop_stage") or "",
        "total_area": str(current_user.get("land_acres", "")),
        "soil_type": current_user.get("soil_data", {}).get("texture", ""),
        "soil_ph": str(current_user.get("soil_data", {}).get("ph", "")),
        "state": "Tamil Nadu"
    }
    
    advisory_result = await ask_advisory(user_question, profile, is_comprehensive=False)
    answer = advisory_result.get("answer", "Sorry, I couldn't process that.")
    
    tts_result = await text_to_speech(answer, req.lang_code)
    
    return {
        "transcribed": transcription.get("transcribed", ""),
        "translated": user_question,
        "answer": answer,
        "translated_answer": tts_result.get("translated", answer),
        "audio": tts_result.get("audio", "")
    }
