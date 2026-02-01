from food_analysis_service import analyze_image_bytes, analyze_image_url

def analyze_food_waste_image(image_bytes: bytes) -> dict:
    """
    Analyze an image of unfinished food provided as bytes.
    Delegates to food_analysis_service.
    """
    return analyze_image_bytes(image_bytes)

def analyze_food_waste_url(image_url: str) -> dict:
    """
    Analyze an image of unfinished food from a URL.
    Delegates to food_analysis_service.
    """
    return analyze_image_url(image_url)
