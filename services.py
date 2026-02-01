import openai
import base64
import json
import os
from dotenv import load_dotenv
from models import WasteAnalysis

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

# Helper to decode response safely
def parse_json_response(response_text):
    try:
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        # Fallback or error
        raise ValueError(f"Failed to parse JSON from OpenAI: {e}")

def _call_openai_vision(payload_content: list) -> dict:
    """Helper to call OpenAI API and parse JSON response"""
    prompt_text = """Analyze this image of unfinished food carefully. 

Your task is to:
1. Identify what the ORIGINAL meal was before eating
2. Identify what food was THROWN AWAY (left on plate/uneaten)
3. Estimate what food was EATEN (consumed/missing from original meal)
4. Infer food preferences based on what was eaten vs thrown away

Return your response ONLY as a JSON object with this EXACT structure:
{
    "original_meal": {
        "name": "name of the dish/meal",
        "description": "brief description of what the meal originally was"
    },
    "thrown_away": [
        {
            "item": "food item name",
            "quantity": "estimated quantity (e.g., '1/2 cup', '3 pieces', '50%')",
            "percentage_of_original": "estimated percentage left uneaten"
        }
    ],
    "eaten": [
        {
            "item": "food item name",
            "quantity": "estimated quantity consumed",
            "percentage_of_original": "estimated percentage that was eaten"
        }
    ],
    "food_preferences": {
        "likely_dislikes": ["list of foods they seem to dislike based on what was thrown away"],
        "likely_likes": ["list of foods they seem to like based on what was eaten"],
        "insights": "brief insight about their eating preferences"
    },
    "waste_summary": {
        "total_waste_percentage": "estimated overall waste percentage",
        "waste_value": "low/medium/high"
    }
}

Return ONLY the JSON object, no other text or markdown."""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                *payload_content
            ]
        }
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )
        
        return parse_json_response(response.choices[0].message.content)

    except Exception as e:
        raise Exception(f"OpenAI API Error: {str(e)}")

def analyze_food_waste_image(image_bytes: bytes) -> dict:
    """
    Analyze an image of unfinished food provided as bytes.
    """
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    payload = [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        }
    ]
    return _call_openai_vision(payload)

def analyze_food_waste_url(image_url: str) -> dict:
    """
    Analyze an image of unfinished food from a URL.
    """
    payload = [
        {
            "type": "image_url",
            "image_url": {
                "url": image_url
            }
        }
    ]
    return _call_openai_vision(payload)
