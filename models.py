from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

# --- Shared Models (Waste Analysis) ---

class OriginalMeal(BaseModel):
    name: str = Field(default="Unknown")
    description: str = Field(default="")

class FoodItem(BaseModel):
    item: str
    quantity: str
    percentage_of_original: str

class FoodPreferences(BaseModel):
    likely_dislikes: List[str] = []
    likely_likes: List[str] = []
    insights: str = ""

class WasteSummary(BaseModel):
    total_waste_percentage: str
    waste_value: str

class WasteAnalysis(BaseModel):
    original_meal: OriginalMeal
    thrown_away: List[FoodItem]
    eaten: List[FoodItem]
    food_preferences: FoodPreferences
    waste_summary: WasteSummary

# --- User Models ---

class UserCreate(BaseModel):
    user_id: str
    user_name: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    liked_foods: List[str] = []
    disliked_foods: List[str] = []
    meal_count: int = 0
    total_waste_percentage: float = 0.0
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserSummary(UserResponse):
    total_meals_analyzed: int
    average_waste_percentage: float
    recent_meals: List[Dict[str, Any]]

# --- API Request/Response Models ---

class UpdatePreferencesRequest(BaseModel):
    user_id: str
    waste_analysis: WasteAnalysis

class StandardResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None

class MealHistoryResponse(BaseModel):
    success: bool
    history: List[Dict[str, Any]] 
    count: int

class AnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[WasteAnalysis] = None
    error: Optional[str] = None
