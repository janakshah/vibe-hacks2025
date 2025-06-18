from fastapi import FastAPI, Form
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Import your LiteLLMClient from the wrapper module
from bedrockWrapper import LiteLLMClient

# ---- Configuration & Constants ----
REQUIRED_SLOTS = ["business_type", "offer", "zip_code", "date"]
MAX_ROUNDS = 2
API_KEY = "sk-rilla-vibes"  # move to environment in production

# ---- FastAPI setup ----
app = FastAPI()
llm_client = LiteLLMClient(api_key=API_KEY)

# ---- Entity Extraction via LLM ----
def extract_entities(text: str) -> Dict[str, str]:
    """
    Uses the LLM to parse the transcript into JSON fields.
    Expects a JSON object with keys: business_type, offer, zip_code.
    """
    system_prompt = (
        "You are a data extraction assistant. "
        "Given a user transcript, output only a JSON object with the keys: "
        "business_type, offer, zip_code. "
        "If any field is not mentioned, set its value to an empty string."
    )
    user_prompt = f"Transcript: \"\"\"{text}\"\"\"\n\nExtract the fields into JSON."  

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    resp = llm_client.chat_completion(
        model="llama-4-maverick-17b-instruct", messages=messages
    )
    content = resp["choices"][0]["message"]["content"]
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}
    # Filter out empty values
    return {k: v for k, v in data.items() if isinstance(v, str) and v.strip()}


def fetch_census_data(zip_code: str) -> Dict[str, Any]:
    """
    Fetch basic demographic data for the given ZIP code.
    """
    # TODO: integrate with Census API
    return {}


def fetch_local_context(zip_code: str) -> Dict[str, str]:
    """
    Pull in headlines, holiday/festival info, sports wins, etc.
    """
    # TODO: integrate with NewsAPI, Calendarific, sports API
    return {}


def build_prompt(entities: Dict[str, str], census: Dict[str, Any], context: Dict[str, str]) -> str:
    """
    Assemble a very rich prompt for the LLM using all gathered data.
    """
    # Fallback defaults
    biz = entities.get('business_type', 'your business')
    offer = entities.get('offer', 'a special offer')
    zip_code = entities.get('zip_code', 'your area')
    date = entities.get('date', 'today')

    lines = [
        "You are a creative marketing assistant specializing in crafting hyper-local, high-energy marketing messages.",
        f"Current date: {date}.",
        f"Business type: {biz}.",
        f"Location (ZIP): {zip_code}.",
        f"Promotion: {offer}.",
        "",
        "Contextual Details:",
    ]

    # Add census snippet
    if census:
        dem = ", ".join(f"{k}: {v}" for k, v in census.items())
    else:
        dem = "No demographic data available"
    lines.append(f"- Local demographics: {dem}")

    # Add local context
    if context:
        for label, txt in context.items():
            lines.append(f"- {label}: {txt}")
    else:
        lines.append("- No local context data available")

    lines += [
        "",
        "Instructions for the marketing message:",
        "- Write a short (1-2 sentences), punchy, and engaging message.",
        "- Mention the promotion clearly and invite customers in.",
        "- Highlight local community spirit or relevant local events.",
        "- Include a sense of urgency (e.g., 'Today only', 'Don't miss out').",
        "- Optionally call out the ZIP code or neighborhood name.",
        "- Use a friendly, conversational tone suitable for social media.",
        "",
        "Provide only the marketing message, without any extra explanation."
    ]

    return "\n".join(lines)


@app.post("/generate_message")
async def generate_message(
    transcript: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    offer: Optional[str] = Form(None),
    zip_code: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    round: int = Form(0),
):
    # 1) Collect provided slots
    entities: Dict[str, str] = {}
    for slot, val in [
        ("business_type", business_type),
        ("offer", offer),
        ("zip_code", zip_code),
        ("date", date)
    ]:
        if val:
            entities[slot] = val

    # 2) First-round auto-extraction from transcript
    if transcript and round == 0:
        entities.update(extract_entities(transcript))

    # 3) Check missing slots
    missing = [s for s in REQUIRED_SLOTS if not entities.get(s)]
    if missing and round < MAX_ROUNDS:
        return {"status": "need_more_info", "missing": missing}

    # 4) Proceed regardless of missing data after max tries
    census = fetch_census_data(entities.get("zip_code", ""))
    context = fetch_local_context(entities.get("zip_code", ""))

    # 5) Build and send prompt
    prompt = build_prompt(entities, census, context)
    messages = [{"role": "user", "content": prompt}]
    llm_resp = llm_client.chat_completion(
        model="llama-4-maverick-17b-instruct", messages=messages
    )

    marketing_msg = llm_resp["choices"][0]["message"]["content"]
    return {"status": "success", "message": marketing_msg}
