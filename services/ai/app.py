
import os
import json
import re
import requests

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load settings from the main TripGenie .env file
load_dotenv()

app = Flask(__name__)

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")


# Sample destinations used when AI is unavailable
SAMPLE_DESTINATIONS = [
    {
        "name": "Bali",
        "country": "Indonesia",
        "budget_level": "medium",
        "vibe_tags": ["beach", "adventure", "romantic"],
        "description": "Beautiful beaches, temples and tropical experiences.",
        "avg_cost_per_day": 55
    },
    {
        "name": "Manali",
        "country": "India",
        "budget_level": "low",
        "vibe_tags": ["mountains", "adventure", "nature"],
        "description": "Mountain scenery, snow activities and peaceful valleys.",
        "avg_cost_per_day": 30
    },
    {
        "name": "Paris",
        "country": "France",
        "budget_level": "high",
        "vibe_tags": ["romantic", "culture", "city"],
        "description": "Art, architecture, cafes and romantic experiences.",
        "avg_cost_per_day": 120
    },
    {
        "name": "Goa",
        "country": "India",
        "budget_level": "medium",
        "vibe_tags": ["beach", "nightlife", "adventure"],
        "description": "Sunny beaches, water sports and coastal culture.",
        "avg_cost_per_day": 45
    },
    {
        "name": "Ooty",
        "country": "India",
        "budget_level": "low",
        "vibe_tags": ["mountains", "nature", "relaxation"],
        "description": "Green hills, tea gardens and cool weather.",
        "avg_cost_per_day": 25
    },
    {
        "name": "Tokyo",
        "country": "Japan",
        "budget_level": "high",
        "vibe_tags": ["city", "culture", "food"],
        "description": "Modern city life, traditional culture and amazing food.",
        "avg_cost_per_day": 110
    }
]


def extract_json(text):
    """Extract JSON safely from an AI response."""

    text = text.strip()

    # Remove Markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def get_fallback_recommendations(preferences):
    """Recommend destinations without using an external AI."""

    requested_vibes = preferences.get("vibes", [])
    budget = str(preferences.get("budget", "any")).lower()

    if isinstance(requested_vibes, str):
        requested_vibes = [requested_vibes]

    scored = []

    for destination in SAMPLE_DESTINATIONS:
        score = len(
            set(str(v).lower() for v in requested_vibes)
            & set(destination["vibe_tags"])
        )

        if budget in ["low", "medium", "high"]:
            if destination["budget_level"] == budget:
                score += 2

        scored.append((score, destination))

    scored.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            **destination,
            "match_score": min(100, 70 + score * 10),
            "reason": "Matched your travel preferences."
        }
        for score, destination in scored[:3]
    ]


def ask_gemini(prompt):
    """Send a request to Google Gemini."""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{AI_MODEL}:generateContent"
    )

    response = requests.post(
        url,
        params={"key": AI_API_KEY},
        json={
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        },
        timeout=45
    )

    response.raise_for_status()

    result = response.json()

    return result["candidates"][0]["content"]["parts"][0]["text"]


def ask_openrouter(prompt):
    """Send a request to OpenRouter."""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": AI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Return only valid JSON. No Markdown."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"}
        },
        timeout=45
    )

    response.raise_for_status()

    result = response.json()

    return result["choices"][0]["message"]["content"]


def get_ai_recommendations(preferences):
    """Generate recommendations using the configured AI provider."""

    prompt = f"""
You are TripGenie, a friendly travel recommendation assistant.

Recommend exactly 3 travel destinations based on these preferences:
{json.dumps(preferences)}

Return only valid JSON in this format:
{{
  "recommendations": [
    {{
      "name": "Destination name",
      "country": "Country",
      "description": "Short description",
      "budget_level": "low, medium or high",
      "vibe_tags": ["beach", "adventure"],
      "avg_cost_per_day": 50,
      "match_score": 95,
      "reason": "Why this destination matches"
    }}
  ]
}}

Use realistic destinations and estimated daily costs in USD.
Keep descriptions short.
"""

    if AI_PROVIDER == "gemini":
        raw_response = ask_gemini(prompt)

    elif AI_PROVIDER == "openrouter":
        raw_response = ask_openrouter(prompt)

    else:
        raise ValueError("Unsupported AI_PROVIDER")

    parsed = extract_json(raw_response)

    recommendations = parsed.get("recommendations")

    if not isinstance(recommendations, list) or not recommendations:
        raise ValueError("AI returned invalid recommendations")

    return recommendations[:3]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "ai-service",
        "provider": AI_PROVIDER,
        "ai_configured": bool(AI_API_KEY)
    })


@app.route("/recommend", methods=["POST"])
def recommend():
    preferences = request.get_json(silent=True) or {}

    try:
        if AI_API_KEY:
            try:
                recommendations = get_ai_recommendations(preferences)
                source = "ai"

            except Exception as error:
                print("AI request failed:", str(error))
                recommendations = get_fallback_recommendations(preferences)
                source = "fallback"

        else:
            recommendations = get_fallback_recommendations(preferences)
            source = "fallback"

        return jsonify({
            "success": True,
            "source": source,
            "count": len(recommendations),
            "recommendations": recommendations
        })

    except Exception as error:
        print("Recommendation error:", str(error))

        return jsonify({
            "success": False,
            "error": "Could not generate recommendations."
        }), 500


if __name__ == "__main__":
    print("TripGenie AI Service starting...")
    print("AI provider:", AI_PROVIDER)
    print("AI API key configured:", bool(AI_API_KEY))

    app.run(host="0.0.0.0", port=5003, debug=True)
