# backend/services/openai_service.py
import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT_QUICK = """You are KisanAI — an expert in Zero Budget Natural Farming (ZBNF) based on Subhash Palekar's principles. You ONLY recommend organic, chemical-free solutions.

RULES:
- Give MEDIUM length answers (35-50 words) - not too short, not too long.
- State the problem cause in 1 brief sentence.
- Give 1-2 specific organic/natural solutions with exact dosages (e.g., Neem oil, Jivamrita).
- Integrate the provided market/subsidy context naturally if available.
- Use simple, farmer-friendly language.
- Respond in English ONLY.
- Be direct and actionable.
- NO greetings, NO introductions, NO conclusions.
- ONLY give the actual answer - no extra words.
"""

SYSTEM_PROMPT_COMPREHENSIVE = """You are Krishi, the expert Natural Farming Consultant (Zero Budget Natural Farming, Multilevel Cropping) for Indian farmers.
Generate a structured, comprehensive farming advisory report based on the farmer's profile and query.

You must focus on organic and natural farming techniques, including:
1. Disease & Pest Control: Suggest organic remedies (Neem oil spray, Jivamrita, Beejamrita, Agniastra, Neemastra, Dashaparni Ark).
2. Soil & Irrigation: Natural mulching, crop rotation, cover crops, and drip schedule.
3. Multilevel Cropping: 5-layer model (canopy trees, medium trees, shrubs, ground cover, root crops) if applicable.
4. Financial/Subsidy: Mention government schemes like PM-KISAN, PKVY (Paramparagat Krishi Vikas Yojana), and Soil Health Card.
5. Market: Actionable crop holding/selling tips based on price trends.

Structure your response into clear sections using these headings:
[DIAGNOSIS & TREATMENT]
- Cause of issue.
- Organic remedies (dosages & schedule).

[SOIL, WATER & CROP ROTATION]
- Organic soil inputs and companion planting.
- Dynamic watering schedule.

[MULTILEVEL NATURAL STRATEGY]
- Cropping patterns (canopy, shrubs, root layers).

[MARKET & SUBSIDY VALUE]
- Mandi price advice (e.g. hold harvest, price rising).
- Applicable subsidies (e.g. PM-KISAN organic inputs).

RULES:
- Keep the total report length under 180 words.
- Be extremely practical and direct.
- Respond in English ONLY.
"""

async def ask_openai(question: str, is_comprehensive: bool = False, profile: dict = None) -> str:
    """
    Asynchronously query OpenAI GPT for agricultural advice.
    """
    if not openai_client:
        raise ValueError("OpenAI client not configured")
        
    model_name = "gpt-4o-mini"
    context_injection = ""
    q_lower = question.lower()

    if "tomato" in q_lower or "thakkali" in q_lower or "புள்ளி நோய்" in q_lower:
        context_injection += (
            "\n[CONTEXT - TOMATO MANDI INFO]: Current tomato mandi price is ₹3,200 per quintal. Price is trending upwards. "
            "Strongly advise farmer to hold harvest for 3 days to maximize profit.\n"
            "[CONTEXT - SUBSIDY]: Recommend the PM-KISAN subsidy for organic inputs (Rs. 6,000/year) and PKVY scheme for organic transition.\n"
        )
    elif "paddy" in q_lower or "rice" in q_lower or "nel" in q_lower:
        context_injection += (
            "\n[CONTEXT - PADDY MANDI INFO]: Current paddy price is ₹2,150 per quintal. Trend is stable. Recommend harvesting on schedule.\n"
            "[CONTEXT - SUBSIDY]: State seed subsidy offers 50% off certified organic seeds at AEC centers.\n"
        )

    if any(k in q_lower for k in ["subsidy", "scheme", "government", "money"]):
        context_injection += (
            "\n[CONTEXT - SUBSIDIES]: The PM-KISAN scheme provides Rs. 6,000 direct income support. "
            "PKVY provides Rs. 50,000 per hectare for organic farming transition.\n"
        )

    if is_comprehensive:
        system_prompt = SYSTEM_PROMPT_COMPREHENSIVE
        max_tokens = 300
        context = ""
        if profile:
            context += "FARMER PROFILE:\n"
            context += f"- Crop: {profile.get('present_crop', 'Tomato')}\n"
            context += f"- Stage: {profile.get('present_crop_stage', 'Vegetative')}\n"
            context += f"- Location: {profile.get('district', '')}, {profile.get('state', 'Tamil Nadu')}\n"
            context += f"- Land Area: {profile.get('land_acres', '2')} acres\n"
            context += f"- Soil Type: {profile.get('soil_type', 'Red Clay')}\n"
            if profile.get("current_issues"):
                context += f"- Current issues: {profile.get('current_issues')}\n"
            context += "\n"

        context += f"QUESTION: {question}\n"
        if context_injection:
            context += f"{context_injection}\n"
        user_prompt = context
    else:
        system_prompt = SYSTEM_PROMPT_QUICK
        max_tokens = 90
        user_prompt = question
        if context_injection:
            user_prompt += f"\nNote: Incorporate this data: {context_injection}"

    resp = await openai_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()


SYSTEM_PROMPT_INTENT = """You are KisanAI — a multilingual tool-using AI farming advisor.
Analyze the user's agricultural query using the provided profile, conversation history, and pre-fetched tool database context.

Determine the semantic intent (Layer 1) and the required UX action (Layer 2):

### Layer 1: INTENT
- AskPrice: User asks about crop prices, mandi rates, buyers, or holding/selling recommendations.
- AskDiseaseRemedy: User asks about plant diseases, bugs, crop damage, symptoms, or organic treatments.
- AskScheme: User asks about subsidies, government schemes, grants, or financial aid.
- AskRecommendation: User asks about which crop to plant next, soil suitability, or profitability.
- OpenPage: User explicitly asks to open a specific screen (e.g. "Open market page", "Show recommendations").
- GeneralQuestion: General agricultural Q&A, weather reports, ZBNF recipes (Jivamrita), ZBNF concepts (multilevel cropping), or general greeting.

### Layer 2: ACTION (Strict Rules)
- Navigate: ONLY trigger this action if the intent is OpenPage (e.g. "take me to prices", "open disease scanner").
- AnswerAndSuggestNavigation: Use this for AskPrice, AskDiseaseRemedy, AskScheme, and AskRecommendation when they ask for information (e.g., "What is tomato price?"). Do NOT navigate automatically. Suggest navigation via the target field.
- AnswerOnly: Use this for GeneralQuestion or if no navigation screen matches.

### Navigation Targets
- Market Page -> Target: "/market"
- Disease/Pest Page -> Target: "/pest"
- Crop Recommendation Page -> Target: "/recommendations"
- Home/Dashboard -> Target: "/home"
- Otherwise -> Target: null

Output ONLY a valid JSON object (no markdown, no backticks, no JSON code block wrap) with this exact structure:
{
  "intent": "AskPrice" | "AskDiseaseRemedy" | "AskScheme" | "AskRecommendation" | "OpenPage" | "GeneralQuestion",
  "action": "AnswerOnly" | "AnswerAndSuggestNavigation" | "Navigate",
  "target": "/market" | "/pest" | "/recommendations" | "/home" | null,
  "tool_used": "get_market_price" | "get_weather" | "get_schemes" | "get_crop_recommendation" | "diagnose_disease" | "get_natural_farming_guide" | "none",
  "answer": "Formulate a direct, conversational spoken response in English. Keep it under 45 words. Be direct, friendly, and actionable. State key values from the pre-fetched context (e.g., exact price, trend, benefit amount, primary crop name). Speak the answer first. Never say you are redirecting unless the action is Navigate.",
  "suggest_label": "A short farmer-friendly button label in English to suggest navigation (e.g., 'View Detailed Market Trends', 'Open Disease Dashboard', 'Open Subsidy Center', 'Explore Crop Recommendations'). Keep it under 4 words. Set to null if action is AnswerOnly or Navigate."
}
"""

async def parse_intent_openai(question: str, profile: dict = None, tool_context: dict = None) -> dict:
    """
    Use OpenAI to parse intent and formulate a response using pre-fetched tool context.
    """
    if not openai_client:
        raise ValueError("OpenAI client not configured")
        
    context = ""
    if profile:
        context += f"Farmer Profile:\n{json.dumps(profile, indent=2)}\n"
    if tool_context:
        context += f"Pre-fetched Tool Context:\n{json.dumps(tool_context, indent=2)}\n"
    
    user_prompt = f"{context}User query: {question}"

    resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_INTENT},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=200,
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content.strip())
