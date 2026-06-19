import os
import json
from services.groq_service import ask_groq
from services.openai_service import ask_openai
from services.gemini_service import generate_advisory_plan, recommend_next_crop
import google.generativeai as genai

class AIGateway:
    @staticmethod
    async def get_advisory(question: str, is_comprehensive: bool = False, profile: dict = None) -> str:
        """
        Routes text advisory to OpenAI GPT-4o-mini first, and falls back to Groq LLaMA.
        """
        try:
            return await ask_openai(question, is_comprehensive=is_comprehensive, profile=profile)
        except Exception as e:
            print(f"[WARNING] OpenAI advisory failed: {e}. Falling back to Groq...")
            return await ask_groq(question, is_comprehensive=is_comprehensive, profile=profile)

    @staticmethod
    async def generate_weekly_plan(profile: dict) -> dict:
        """
        Routes structured weekly planning to Google Gemini 1.5 Flash.
        """
        return await generate_advisory_plan(profile)

    @staticmethod
    async def get_next_crop_recommendation(profile: dict, market_data: list) -> dict:
        """
        Routes crop recommendations to Google Gemini 1.5 Flash.
        """
        return await recommend_next_crop(profile, market_data)

    @staticmethod
    async def diagnose_disease(image_base64: str, crop_context: str = "") -> dict:
        """
        Routes image-based disease diagnosis to Gemini Vision.
        Returns a dict containing diagnosis, organic remedies, severity, and prevention.
        """
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        genai.configure(api_key=GEMINI_API_KEY)

        prompt = f"""You are an expert plant pathologist specializing in Indian agriculture and natural farming.
Analyze this crop image. The crop is: {crop_context or "unknown crop"}.

Return ONLY valid JSON (no markdown, no backticks, no JSON code block wrap) with this structure:
{{
  "disease_name": "Early Blight",
  "identified": true,
  "confidence": 0.92,
  "severity_level": "Medium (4/10)",
  "organic_remedies": [
    "Spray 5% Neem Seed Kernel Extract (NSKE) at weekly intervals.",
    "Apply Sour Buttermilk spray (1L sour buttermilk + 20L water)."
  ],
  "prevention_steps": [
    "Use healthy, disease-free certified seeds.",
    "Ensure proper spacing to allow air circulation."
  ]
}}
"""
        # Load image bytes from base64
        import base64
        image_data = base64.b64decode(image_base64)
        
        contents = [
            {"mime_type": "image/jpeg", "data": image_data},
            prompt
        ]
        
        # We run the synchronous Gemini API call in the executor
        import asyncio
        def _call_gemini():
            models_to_try = [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-flash-latest",
                "gemini-flash-lite-latest"
            ]
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(contents)
                    return response.text.strip()
                except Exception as e:
                    print(f"[WARNING] Model {model_name} Vision failed: {e}. Trying next...")
            raise ValueError("All Gemini Vision models failed")
            
        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(None, _call_gemini)
        
        # Clean response text in case Gemini wraps it in markdown code blocks
        clean_text = response_text
        if clean_text.startswith("```"):
            # strip off ```json and ```
            lines = clean_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_text = "\n".join(lines).strip()
            
        try:
            return json.loads(clean_text)
        except Exception as e:
            print(f"[⚠️ AI Gateway] Gemini JSON parsing failed: {e}. Raw response: {response_text}")
            # Fallback structure
            return {
                "disease_name": "General Pest/Disease Symptoms",
                "identified": False,
                "confidence": 0.5,
                "severity_level": "Unknown",
                "organic_remedies": [
                    "Spray Jivamrita (mixed with water in 1:10 ratio).",
                    "Apply Neem Oil (5ml per liter of water) mixed with soap emulsifier."
                ],
                "prevention_steps": [
                    "Maintain field sanitation.",
                    "Practice crop rotation."
                ],
                "raw_error": str(e)
            }
