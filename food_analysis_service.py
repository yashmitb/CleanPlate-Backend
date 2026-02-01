import openai
import base64
import json
import os
from typing import Dict, Any, Union
from dotenv import load_dotenv
from models import WasteAnalysis

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

SYSTEM_PROMPT = """Analyze this image of unfinished food carefully. 

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

def _parse_json_response(response_text: str) -> Dict[str, Any]:
    """Helper to safely parse JSON response from OpenAI."""
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
        raise ValueError(f"Failed to parse JSON from OpenAI: {e}")

def _call_openai_vision(payload_content: list) -> Dict[str, Any]:
    """Internal helper to call OpenAI API."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        *payload_content
                    ]
                }
            ],
            max_tokens=1000
        )
        
        result_dict = _parse_json_response(response.choices[0].message.content)
        
        # Validate against the Pydantic model (this ensures structure compliance)
        # We return the dict for now as downstream expects dicts, but validation is useful.
        validated_result = WasteAnalysis(**result_dict)
        return validated_result.model_dump()
        
    except Exception as e:
        # Re-raise with clear context
        raise Exception(f"Analysis failed: {str(e)}")

def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyze an image provided as bytes.
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

def analyze_image_url(image_url: str) -> Dict[str, Any]:
    """
    Analyze an image provided via URL.
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
