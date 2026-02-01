import openai
import base64
import json
from pathlib import Path
import dotenv.load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_KEY")

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_food_waste(image_path):
    """
    Analyze an image of unfinished food and return comprehensive food preference data.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        dict: Dictionary containing thrown away food, eaten food, and preferences
    """
    # Encode the image
    base64_image = encode_image(image_path)
    
    # Create the prompt
    prompt = """Analyze this image of unfinished food carefully. 

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
    
    # Call OpenAI API with vision
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    
    # Extract the response
    response_text = response.choices[0].message.content
    
    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return error structure
        return {
            "error": "Failed to parse response",
            "raw_response": response_text,
            "error_details": str(e)
        }

def analyze_food_waste_from_url(image_url):
    """
    Analyze an image of unfinished food from a URL.
    
    Args:
        image_url (str): URL of the image
        
    Returns:
        dict: Dictionary containing thrown away food, eaten food, and preferences
    """
    prompt = """Analyze this image of unfinished food carefully. 

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
    
    # Call OpenAI API with vision using URL
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    
    response_text = response.choices[0].message.content
    
    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return error structure
        return {
            "error": "Failed to parse response",
            "raw_response": response_text,
            "error_details": str(e)
        }

# Example usage
if __name__ == "__main__":
    # Example 1: Using a local image file
    image_path = "unfinished_food.jpg"
    
    try:
        result = analyze_food_waste(image_path)
        
        # Print the full JSON response
        print("=== FULL API RESPONSE ===")
        print(json.dumps(result, indent=2))
        
        
        
    except FileNotFoundError:
        print(f"Image file not found: {image_path}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Using an image URL
    # image_url = "https://example.com/food_waste.jpg"
    # result = analyze_food_waste_from_url(image_url)
    # print(json.dumps(result, indent=2))